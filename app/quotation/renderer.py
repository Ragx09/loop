"""Renders a QuotationDocument through a selected template into HTML or PDF."""

from decimal import Decimal
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.quotation.document import QuotationDocument
from app.quotation.pdf import PdfEngine, get_pdf_engine
from app.quotation.registry import get_template

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def _money(value: Decimal | None) -> str:
    if value is None:
        return ""
    return f"{Decimal(value):,.2f}"


def _build_environment() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["money"] = _money
    return env


class QuotationRenderer:
    def __init__(self, pdf_engine: PdfEngine | None = None):
        self.env = _build_environment()
        self.pdf_engine = pdf_engine or get_pdf_engine()

    def render_html(self, document: QuotationDocument, template_key: str) -> str:
        template_def = get_template(template_key)
        template = self.env.get_template(template_def.template_file)
        return template.render(doc=document, business=document.business)

    def render_pdf(self, document: QuotationDocument, template_key: str) -> bytes:
        return self.pdf_engine.render(self.render_html(document, template_key))
