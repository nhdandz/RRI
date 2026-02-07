import uuid

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import delete, select, update

from src.api.deps import DbSession, SettingsDep, get_current_user_dep
from src.api.schemas.folder import DocumentResponse, DocumentUpdate
from src.core.logging import get_logger
from src.services.file_storage import FileStorageService
from src.storage.models.document import Document
from src.storage.models.document_embedding import DocumentEmbedding
from src.storage.models.folder import Folder
from src.storage.vector.qdrant_client import VectorStore

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

file_storage = FileStorageService()


@router.post("/upload/{folder_id}", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    folder_id: uuid.UUID,
    file: UploadFile,
    current_user: get_current_user_dep,
    db: DbSession,
    settings: SettingsDep,
):
    """Upload a file to a folder."""
    # Verify folder belongs to user
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Folder not found")

    # Read file content
    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB",
        )

    doc_id = uuid.uuid4()
    original_filename = file.filename or "unnamed"
    content_type = file.content_type or "application/octet-stream"

    storage_path = file_storage.save_file(
        user_id=current_user.id,
        document_id=doc_id,
        filename=original_filename,
        content=content,
    )

    document = Document(
        id=doc_id,
        user_id=current_user.id,
        folder_id=folder_id,
        filename=original_filename,
        original_filename=original_filename,
        content_type=content_type,
        file_size=len(content),
        storage_path=storage_path,
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)
    return document


@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    current_user: get_current_user_dep,
    db: DbSession,
):
    """Download a document file."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    abs_path = file_storage.get_absolute_path(document.storage_path)
    return FileResponse(
        path=abs_path,
        filename=document.original_filename,
        media_type=document.content_type,
    )


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    body: DocumentUpdate,
    current_user: get_current_user_dep,
    db: DbSession,
):
    """Update a document (move folder or edit note)."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    update_data = body.model_dump(exclude_unset=True)

    # Verify target folder belongs to user
    if "folder_id" in update_data and update_data["folder_id"]:
        result = await db.execute(
            select(Folder).where(
                Folder.id == update_data["folder_id"], Folder.user_id == current_user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Target folder not found")

    if update_data:
        await db.execute(
            update(Document).where(Document.id == document_id).values(**update_data)
        )
        await db.flush()
        await db.refresh(document)

    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: get_current_user_dep,
    db: DbSession,
):
    """Delete a document and its physical file."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Cleanup embeddings from Qdrant if they exist
    emb_result = await db.execute(
        select(DocumentEmbedding).where(DocumentEmbedding.document_id == document_id)
    )
    emb = emb_result.scalar_one_or_none()
    if emb and emb.chunk_count > 0:
        try:
            vector_store = VectorStore()
            point_ids = [
                str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document_id}:{i}"))
                for i in range(emb.chunk_count)
            ]
            vector_store.delete(collection="user_docs", point_ids=point_ids)
        except Exception as e:
            logger.warning("Failed to cleanup vectors", document_id=str(document_id), error=str(e))

    # Delete embedding record
    await db.execute(delete(DocumentEmbedding).where(DocumentEmbedding.document_id == document_id))

    # Delete physical file
    file_storage.delete_file(current_user.id, document_id)

    # Delete DB record
    await db.execute(delete(Document).where(Document.id == document_id))
