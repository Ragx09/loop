"""Renders the non-quotation printable documents: invoices and service reports.

Quotation formats stay in ``app.quotation`` because they are a registry of
interchangeable customer-facing layouts. These are single fixed documents, so
they live here — but they share the same swappable PDF engine, so changing the
PDF technology is still a one-line change in ``app/quotation/pdf.py``.
"""

from decimal import Decimal
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.quotation.pdf import PdfEngine, get_pdf_engine

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

INVOICE_TEMPLATE = "invoice.html"
SERVICE_REPORT_TEMPLATE = "service_report.html"


def _money(value) -> str:
    if value in (None, ""):
        return ""
    return f"{Decimal(value):,.2f}"


class DocumentRenderer:
    def __init__(self, pdf_engine: PdfEngine | None = None):
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters["money"] = _money
        self.pdf_engine = pdf_engine or get_pdf_engine()

    def render_html(self, template_file: str, **context) -> str:
        return self.env.get_template(template_file).render(**context)

    def render_pdf(self, template_file: str, **context) -> bytes:
        return self.pdf_engine.render(self.render_html(template_file, **context))

    # --- convenience -----------------------------------------------------
    def invoice_pdf(self, invoice) -> tuple[str, bytes]:
        pdf = self.render_pdf(INVOICE_TEMPLATE, invoice=invoice, business=invoice.business)
        return f"invoice-{_safe(invoice.invoice_number)}.pdf", pdf

    def service_report_pdf(self, report) -> tuple[str, bytes]:
        pdf = self.render_pdf(SERVICE_REPORT_TEMPLATE, report=report, task=report.task)
        return f"service-report-{report.task_id}.pdf", pdf


def _safe(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in value)
