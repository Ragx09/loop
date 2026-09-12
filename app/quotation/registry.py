"""Registry of available quotation formats.

Each format is a separate template file under ``templates/``. Adding a new
format means adding a template file and one entry here — no other part of LOOP
changes.
"""

from dataclasses import dataclass

from app.core.errors import ValidationError


@dataclass(frozen=True)
class QuotationTemplate:
    key: str
    name: str
    description: str
    #: File name inside app/quotation/templates/
    template_file: str


TEMPLATES: tuple[QuotationTemplate, ...] = (
    QuotationTemplate(
        key="standard",
        name="Standard",
        description="Plain tabular quotation: header, customer block, particulars/HSN/price table.",
        template_file="standard.html",
    ),
)


def list_templates() -> list[QuotationTemplate]:
    return list(TEMPLATES)


def get_template(key: str) -> QuotationTemplate:
    for template in TEMPLATES:
        if template.key == key:
            return template
    raise ValidationError("Unknown quotation format.")
