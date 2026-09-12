"""HTML-to-PDF engine.

Isolated behind ``PdfEngine`` so the implementation can be swapped later (for
example for WeasyPrint or a headless browser) without touching templates or
services.
"""

from io import BytesIO
from typing import Protocol


class PdfEngine(Protocol):
    def render(self, html: str) -> bytes:  # pragma: no cover - interface
        ...


class Xhtml2PdfEngine:
    """Default engine: pure-Python, no system libraries required."""

    def render(self, html: str) -> bytes:
        from xhtml2pdf import pisa  # imported lazily to keep startup fast

        buffer = BytesIO()
        result = pisa.CreatePDF(src=html, dest=buffer, encoding="utf-8")
        if result.err:
            raise RuntimeError("PDF generation failed.")
        return buffer.getvalue()


def get_pdf_engine() -> PdfEngine:
    return Xhtml2PdfEngine()
