import os
import shutil
import uuid

from src.core.config import get_settings


class FileStorageService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_dir = self.settings.UPLOAD_DIR

    def _get_dir(self, user_id: uuid.UUID, document_id: uuid.UUID) -> str:
        return os.path.join(self.base_dir, str(user_id), str(document_id))

    def save_file(
        self,
        user_id: uuid.UUID,
        document_id: uuid.UUID,
        filename: str,
        content: bytes,
    ) -> str:
        """Save file to disk and return the relative storage path."""
        directory = self._get_dir(user_id, document_id)
        os.makedirs(directory, exist_ok=True)
        rel_path = os.path.join(str(user_id), str(document_id), filename)
        abs_path = os.path.join(self.base_dir, rel_path)
        with open(abs_path, "wb") as f:
            f.write(content)
        return rel_path

    def get_absolute_path(self, storage_path: str) -> str:
        """Return the absolute path for a stored file."""
        return os.path.join(self.base_dir, storage_path)

    def delete_file(self, user_id: uuid.UUID, document_id: uuid.UUID) -> None:
        """Delete the entire document directory."""
        directory = self._get_dir(user_id, document_id)
        if os.path.exists(directory):
            shutil.rmtree(directory)

    def delete_user_folder_files(
        self, user_id: uuid.UUID, document_ids: list[uuid.UUID]
    ) -> None:
        """Delete files for multiple documents (used when cascade-deleting a folder)."""
        for doc_id in document_ids:
            self.delete_file(user_id, doc_id)
