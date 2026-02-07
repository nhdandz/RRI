import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, func, select, update

from src.api.deps import DbSession, get_current_user_dep
from src.api.schemas.folder import (
    BreadcrumbItem,
    BookmarkResponse,
    DocumentResponse,
    FolderContentsResponse,
    FolderCreate,
    FolderResponse,
    FolderUpdate,
)
from src.services.file_storage import FileStorageService
from src.storage.models.bookmark import Bookmark
from src.storage.models.document import Document
from src.storage.models.folder import Folder

router = APIRouter(prefix="/folders", tags=["folders"])

file_storage = FileStorageService()


def _build_tree(
    folders: list[Folder],
    bookmark_counts: dict[uuid.UUID, int],
    parent_id: uuid.UUID | None = None,
) -> list[FolderResponse]:
    """Recursively build a nested folder tree."""
    children = []
    for f in folders:
        if f.parent_id == parent_id:
            node = FolderResponse(
                id=f.id,
                parent_id=f.parent_id,
                name=f.name,
                icon=f.icon,
                position=f.position,
                created_at=f.created_at,
                updated_at=f.updated_at,
                children=_build_tree(folders, bookmark_counts, parent_id=f.id),
                bookmark_count=bookmark_counts.get(f.id, 0),
            )
            children.append(node)
    children.sort(key=lambda x: x.position)
    return children


async def _build_breadcrumb(db, folder_id: uuid.UUID, user_id: uuid.UUID) -> list[BreadcrumbItem]:
    """Build breadcrumb trail from root to the given folder."""
    crumbs: list[BreadcrumbItem] = []
    current_id = folder_id
    while current_id:
        result = await db.execute(
            select(Folder).where(Folder.id == current_id, Folder.user_id == user_id)
        )
        folder = result.scalar_one_or_none()
        if not folder:
            break
        crumbs.append(BreadcrumbItem(id=folder.id, name=folder.name))
        current_id = folder.parent_id
    crumbs.reverse()
    return crumbs


async def _collect_descendant_folder_ids(
    db, folder_id: uuid.UUID, user_id: uuid.UUID
) -> list[uuid.UUID]:
    """Recursively collect all descendant folder IDs (including the given folder)."""
    ids = [folder_id]
    result = await db.execute(
        select(Folder.id).where(Folder.parent_id == folder_id, Folder.user_id == user_id)
    )
    child_ids = [row[0] for row in result.all()]
    for child_id in child_ids:
        ids.extend(await _collect_descendant_folder_ids(db, child_id, user_id))
    return ids


@router.get("", response_model=list[FolderResponse])
async def list_folders(current_user: get_current_user_dep, db: DbSession):
    """Get the full folder tree for the current user."""
    result = await db.execute(
        select(Folder).where(Folder.user_id == current_user.id).order_by(Folder.position)
    )
    folders = list(result.scalars().all())

    # Count bookmarks per folder
    counts_result = await db.execute(
        select(Bookmark.folder_id, func.count(Bookmark.id))
        .where(Bookmark.user_id == current_user.id)
        .group_by(Bookmark.folder_id)
    )
    bookmark_counts = {row[0]: row[1] for row in counts_result.all()}

    return _build_tree(folders, bookmark_counts, parent_id=None)


@router.get("/{folder_id}/contents", response_model=FolderContentsResponse)
async def get_folder_contents(
    folder_id: uuid.UUID,
    current_user: get_current_user_dep,
    db: DbSession,
):
    """Get folder contents: subfolders, bookmarks, and documents (Google Drive style)."""
    # Fetch the folder
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.user_id == current_user.id)
    )
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    # Breadcrumb
    breadcrumb = await _build_breadcrumb(db, folder_id, current_user.id)

    # Subfolders
    sub_result = await db.execute(
        select(Folder)
        .where(Folder.parent_id == folder_id, Folder.user_id == current_user.id)
        .order_by(Folder.position)
    )
    subfolders_raw = list(sub_result.scalars().all())

    # Bookmark counts for subfolders
    sub_ids = [sf.id for sf in subfolders_raw]
    bookmark_counts: dict[uuid.UUID, int] = {}
    if sub_ids:
        counts_result = await db.execute(
            select(Bookmark.folder_id, func.count(Bookmark.id))
            .where(Bookmark.folder_id.in_(sub_ids))
            .group_by(Bookmark.folder_id)
        )
        bookmark_counts = {row[0]: row[1] for row in counts_result.all()}

    subfolders = [
        FolderResponse(
            id=sf.id,
            parent_id=sf.parent_id,
            name=sf.name,
            icon=sf.icon,
            position=sf.position,
            created_at=sf.created_at,
            updated_at=sf.updated_at,
            children=[],
            bookmark_count=bookmark_counts.get(sf.id, 0),
        )
        for sf in subfolders_raw
    ]

    # Bookmarks
    bm_result = await db.execute(
        select(Bookmark)
        .where(Bookmark.folder_id == folder_id, Bookmark.user_id == current_user.id)
        .order_by(Bookmark.created_at.desc())
    )
    bookmarks = [BookmarkResponse.model_validate(b) for b in bm_result.scalars().all()]

    # Documents
    doc_result = await db.execute(
        select(Document)
        .where(Document.folder_id == folder_id, Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    documents = [DocumentResponse.model_validate(d) for d in doc_result.scalars().all()]

    return FolderContentsResponse(
        folder=FolderResponse(
            id=folder.id,
            parent_id=folder.parent_id,
            name=folder.name,
            icon=folder.icon,
            position=folder.position,
            created_at=folder.created_at,
            updated_at=folder.updated_at,
            children=[],
            bookmark_count=len(bookmarks),
        ),
        breadcrumb=breadcrumb,
        subfolders=subfolders,
        bookmarks=bookmarks,
        documents=documents,
    )


@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(body: FolderCreate, current_user: get_current_user_dep, db: DbSession):
    """Create a new folder."""
    # Verify parent exists and belongs to user
    if body.parent_id:
        result = await db.execute(
            select(Folder).where(Folder.id == body.parent_id, Folder.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Parent folder not found")

    folder = Folder(
        user_id=current_user.id,
        parent_id=body.parent_id,
        name=body.name,
        icon=body.icon,
        position=body.position,
    )
    db.add(folder)
    await db.flush()
    await db.refresh(folder)
    return FolderResponse(
        id=folder.id,
        parent_id=folder.parent_id,
        name=folder.name,
        icon=folder.icon,
        position=folder.position,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
        children=[],
        bookmark_count=0,
    )


@router.patch("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: uuid.UUID,
    body: FolderUpdate,
    current_user: get_current_user_dep,
    db: DbSession,
):
    """Update a folder (rename, move, reorder)."""
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.user_id == current_user.id)
    )
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    update_data = body.model_dump(exclude_unset=True)
    if update_data:
        await db.execute(
            update(Folder).where(Folder.id == folder_id).values(**update_data)
        )
        await db.flush()
        await db.refresh(folder)

    return FolderResponse(
        id=folder.id,
        parent_id=folder.parent_id,
        name=folder.name,
        icon=folder.icon,
        position=folder.position,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
        children=[],
        bookmark_count=0,
    )


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: uuid.UUID,
    current_user: get_current_user_dep,
    db: DbSession,
):
    """Delete a folder and all its contents (cascading), including physical files."""
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Folder not found")

    # Collect all descendant folder IDs to find documents to delete
    all_folder_ids = await _collect_descendant_folder_ids(db, folder_id, current_user.id)

    # Find all documents in these folders and delete their physical files
    doc_result = await db.execute(
        select(Document.id).where(
            Document.folder_id.in_(all_folder_ids),
            Document.user_id == current_user.id,
        )
    )
    doc_ids = [row[0] for row in doc_result.all()]
    if doc_ids:
        file_storage.delete_user_folder_files(current_user.id, doc_ids)

    # Cascade delete will handle DB records for bookmarks, documents, subfolders
    await db.execute(delete(Folder).where(Folder.id == folder_id))
