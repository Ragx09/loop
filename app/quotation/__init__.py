"""Quotation generation module.

Layering inside this module:

    QuotationDocument (plain data)
        -> QuotationRenderer (chooses a template, renders HTML)
            -> PdfEngine (turns HTML into PDF bytes)

Nothing here imports the task or auth modules, and no SQLAlchemy model is
required to render a quotation — so templates and the PDF engine can both be
replaced without touching business logic.
"""
