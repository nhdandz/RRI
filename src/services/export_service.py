"""Export service for generating PDF/Markdown reports."""


class ExportService:
    async def export_markdown(self, content: str, filename: str) -> bytes:
        return content.encode("utf-8")

    async def export_pdf(self, content: str, filename: str) -> bytes:
        # PDF generation would require a library like weasyprint or reportlab
        # For now, return markdown as fallback
        return content.encode("utf-8")
