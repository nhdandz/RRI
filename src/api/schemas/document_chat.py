from datetime import datetime

from pydantic import BaseModel


class DocumentEmbedRequest(BaseModel):
    document_ids: list[str] = []
    paper_ids: list[str] = []  # bookmarked papers — auto-download PDF if needed


class DocumentEmbedStatus(BaseModel):
    document_id: str
    status: str  # pending | processing | completed | failed
    chunk_count: int = 0
    error_message: str | None = None


class DocumentEmbedResponse(BaseModel):
    results: list[DocumentEmbedStatus]


class ConversationDocumentsUpdate(BaseModel):
    document_ids: list[str]


class LibraryFolder(BaseModel):
    id: str
    name: str
    parent_id: str | None = None
    documents: list["LibraryDocument"] = []
    papers: list["LibraryPaper"] = []
    children: list["LibraryFolder"] = []

    model_config = {"from_attributes": True}


class LibraryDocument(BaseModel):
    id: str
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class LibraryPaper(BaseModel):
    """A bookmarked paper that can be auto-downloaded for document chat."""
    paper_id: str
    title: str
    pdf_url: str | None = None
    arxiv_id: str | None = None
    source: str | None = None
    has_local_pdf: bool = False  # True if already downloaded as Document
    document_id: str | None = None  # Document ID if already downloaded
    folder_id: str  # folder where the bookmark lives

    model_config = {"from_attributes": True}


class LibraryResponse(BaseModel):
    folders: list[LibraryFolder]
    root_documents: list[LibraryDocument] = []
