"""Quotation creation, template selection, PDF generation and authorization."""

from decimal import Decimal

from app.quotation.document import BusinessInfo, QuotationDocument, QuotationLine
from app.quotation.registry import list_templates
from app.quotation.renderer import QuotationRenderer
from tests.conftest import ENGINEER_PASSWORD, PROPRIETOR_PASSWORD, auth_headers, login

from datetime import date


def quotation_payload(business_id: int, **overrides) -> dict:
    payload = {
        "business_id": business_id,
        "template_key": "standard",
        "customer_name": "Kumar Traders",
        "items": [
            {"particulars": "Control panel service", "hsn_code": "8537", "price": "12500.00"},
            {"particulars": "Sensor replacement", "hsn_code": "9026", "price": "3250.50"},
        ],
    }
    payload.update(overrides)
    return payload


def test_proprietor_generates_quotation_and_downloads_pdf(client, seeded):
    token = login(client, "owner", PROPRIETOR_PASSWORD)
    headers = auth_headers(token)

    created = client.post(
        "/api/quotations", json=quotation_payload(seeded["business"].id), headers=headers
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert Decimal(body["total"]) == Decimal("15750.50")
    assert body["quotation_number"]  # auto-generated when not supplied

    pdf = client.get(f"/api/quotations/{body['id']}/pdf", headers=headers)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")
    assert "attachment" in pdf.headers["content-disposition"]


def test_businesses_and_templates_are_selectable(client, seeded):
    headers = auth_headers(login(client, "owner", PROPRIETOR_PASSWORD))

    businesses = client.get("/api/quotations/businesses", headers=headers).json()
    assert "Arcot Enterprises" in [b["name"] for b in businesses]

    templates = client.get("/api/quotations/templates", headers=headers).json()
    assert "standard" in [t["key"] for t in templates]


def test_unknown_template_is_rejected(client, seeded):
    headers = auth_headers(login(client, "owner", PROPRIETOR_PASSWORD))
    response = client.post(
        "/api/quotations",
        json=quotation_payload(seeded["business"].id, template_key="does-not-exist"),
        headers=headers,
    )
    assert response.status_code == 422


def test_quotation_requires_at_least_one_line(client, seeded):
    headers = auth_headers(login(client, "owner", PROPRIETOR_PASSWORD))
    response = client.post(
        "/api/quotations",
        json=quotation_payload(seeded["business"].id, items=[]),
        headers=headers,
    )
    assert response.status_code == 422


def test_engineer_cannot_access_quotations(client, seeded):
    headers = auth_headers(login(client, "eng1", ENGINEER_PASSWORD))
    assert client.get("/api/quotations", headers=headers).status_code == 403
    assert (
        client.post(
            "/api/quotations", json=quotation_payload(seeded["business"].id), headers=headers
        ).status_code
        == 403
    )


def test_manual_prices_are_preserved_exactly(client, seeded):
    """Same product, different price per customer — no pricing logic anywhere."""
    headers = auth_headers(login(client, "owner", PROPRIETOR_PASSWORD))
    first = client.post(
        "/api/quotations",
        json=quotation_payload(
            seeded["business"].id,
            customer_name="Customer A",
            items=[{"particulars": "Pump", "hsn_code": "8413", "price": "1000.00"}],
        ),
        headers=headers,
    ).json()
    second = client.post(
        "/api/quotations",
        json=quotation_payload(
            seeded["business"].id,
            customer_name="Customer B",
            items=[{"particulars": "Pump", "hsn_code": "8413", "price": "1750.00"}],
        ),
        headers=headers,
    ).json()

    assert Decimal(first["items"][0]["price"]) == Decimal("1000.00")
    assert Decimal(second["items"][0]["price"]) == Decimal("1750.00")


def test_every_registered_template_renders(tmp_path):
    """The renderer works without a database — templates are pure presentation."""
    document = QuotationDocument(
        business=BusinessInfo(key="arcot_enterprises", name="Arcot Enterprises"),
        quotation_number="AE/2026/0001",
        quotation_date=date(2026, 9, 12),
        customer_name="Kumar Traders",
        lines=[QuotationLine(particulars="Pump", hsn_code="8413", price=Decimal("1000.00"))],
    )
    renderer = QuotationRenderer()
    for template in list_templates():
        html = renderer.render_html(document, template.key)
        assert "Arcot Enterprises" in html
        assert "Kumar Traders" in html
        assert renderer.render_pdf(document, template.key).startswith(b"%PDF")


# --- quantity -------------------------------------------------------------


def test_quantity_multiplies_the_unit_price_into_the_line_total(client, seeded):
    token = login(client, "owner", PROPRIETOR_PASSWORD)
    response = client.post(
        "/api/quotations",
        json=quotation_payload(
            seeded["business"].id,
            items=[
                {"particulars": "Drum unit", "hsn_code": "8443", "price": "8500.00",
                 "quantity": 3},
                {"particulars": "Installation", "hsn_code": "9987", "price": "1500.00"},
            ],
        ),
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    body = response.json()

    first, second = body["items"]
    assert first["quantity"] == 3
    assert Decimal(first["price"]) == Decimal("8500.00")
    assert Decimal(first["line_total"]) == Decimal("25500.00")

    # Quantity is optional and defaults to 1, so older payloads keep working.
    assert second["quantity"] == 1
    assert Decimal(second["line_total"]) == Decimal("1500.00")

    assert Decimal(body["total"]) == Decimal("27000.00")


def test_quantity_must_be_a_positive_whole_number(client, seeded):
    token = login(client, "owner", PROPRIETOR_PASSWORD)
    response = client.post(
        "/api/quotations",
        json=quotation_payload(
            seeded["business"].id,
            items=[{"particulars": "Pump", "price": "100.00", "quantity": 0}],
        ),
        headers=auth_headers(token),
    )
    assert response.status_code == 422, response.text


def test_pdf_shows_quantity_and_total_price_columns(seeded):
    from app.quotation.document import BusinessInfo, QuotationDocument, QuotationLine
    from app.quotation.renderer import QuotationRenderer

    document = QuotationDocument(
        business=BusinessInfo(key="arcot_enterprises", name="Arcot Enterprises"),
        quotation_number="AE/2026/0009",
        quotation_date=date.today(),
        customer_name="Kumar Traders",
        lines=[
            QuotationLine(particulars="Pump", hsn_code="8413",
                          price=Decimal("1000.00"), quantity=4)
        ],
    )
    html = QuotationRenderer().render_html(document, "standard")

    assert "Total Price" in html
    assert "Price (1 qty)" in html
    assert "4,000.00" in html
