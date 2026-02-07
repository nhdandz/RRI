import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select, update

from src.api.deps import DbSession, get_current_user_dep
from src.api.schemas.folder import BookmarkCreate, BookmarkResponse, BookmarkUpdate
from src.storage.models.bookmark import Bookmark
from src.storage.models.folder import Folder

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.get("/folder/{folder_id}", response_model=list[BookmarkResponse])
async def list_bookmarks(
    folder_id: uuid.UUID,
    current_user: get_current_user_dep,
    db: DbSession,
):
    """Get all bookmarks in a folder."""
    # Verify folder belongs to user
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Folder not found")

    result = await db.execute(
        select(Bookmark)
        .where(Bookmark.folder_id == folder_id, Bookmark.user_id == current_user.id)
        .order_by(Bookmark.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
async def create_bookmark(
    body: BookmarkCreate,
    current_user: get_current_user_dep,
    db: DbSession,
):
    """Create a new bookmark."""
    # Verify folder belongs to user
    result = await db.execute(
        select(Folder).where(Folder.id == body.folder_id, Folder.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Folder not found")

    bookmark = Bookmark(
        user_id=current_user.id,
        folder_id=body.folder_id,
        item_type=body.item_type,
        item_id=body.item_id,
        external_url=body.external_url,
        external_title=body.external_title,
        external_metadata=body.external_metadata,
        note=body.note,
    )
    db.add(bookmark)
    await db.flush()
    await db.refresh(bookmark)
    return bookmark


@router.patch("/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(
    bookmark_id: uuid.UUID,
    body: BookmarkUpdate,
    current_user: get_current_user_dep,
    db: DbSession,
):
    """Update a bookmark (move to different folder or edit note)."""
    result = await db.execute(
        select(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == current_user.id)
    )
    bookmark = result.scalar_one_or_none()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    update_data = body.model_dump(exclude_unset=True)

    # If moving to a different folder, verify it belongs to user
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
            update(Bookmark).where(Bookmark.id == bookmark_id).values(**update_data)
        )
        await db.flush()
        await db.refresh(bookmark)

    return bookmark


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    bookmark_id: uuid.UUID,
    current_user: get_current_user_dep,
    db: DbSession,
):
    """Delete a bookmark."""
    result = await db.execute(
        select(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Bookmark not found")

    await db.execute(delete(Bookmark).where(Bookmark.id == bookmark_id))
