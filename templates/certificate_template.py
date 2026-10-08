"""One predefined certificate design, rendered with ReportLab."""
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = landscape(A4)


def generate_certificate_pdf(
    output_path: str,
    recipient_name: str,
    certificate_title: str,
    event_name: str,
    date_str: str,
) -> None:
    """Render a simple professional certificate PDF to output_path."""
    if not recipient_name or not recipient_name.strip():
        raise ValueError("Recipient name is empty")

    c = canvas.Canvas(output_path, pagesize=landscape(A4))

    # Outer border
    c.setStrokeColorRGB(0.2, 0.3, 0.55)
    c.setLineWidth(4)
    c.rect(12 * mm, 12 * mm, PAGE_W - 24 * mm, PAGE_H - 24 * mm)
    # Inner border
    c.setLineWidth(1)
    c.rect(17 * mm, 17 * mm, PAGE_W - 34 * mm, PAGE_H - 34 * mm)

    cx = PAGE_W / 2
    y = PAGE_H - 45 * mm

    c.setFont("Helvetica-Bold", 26)
    c.setFillColorRGB(0.2, 0.3, 0.55)
    c.drawCentredString(cx, y, "CERTIFICATE")
    y -= 12 * mm
    c.setFont("Helvetica", 14)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawCentredString(cx, y, "OF")
    y -= 12 * mm
    c.setFont("Helvetica-Bold", 20)
    c.setFillColorRGB(0.15, 0.15, 0.15)
    c.drawCentredString(cx, y, certificate_title.upper())
    y -= 14 * mm

    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.drawCentredString(cx, y, "This is to certify that")
    y -= 13 * mm

    c.setFont("Helvetica-Bold", 24)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawCentredString(cx, y, recipient_name.strip().upper())
    y -= 6 * mm
    # underline for name
    c.setStrokeColorRGB(0.2, 0.3, 0.55)
    c.setLineWidth(1.2)
    name_w = c.stringWidth(recipient_name.strip().upper(), "Helvetica-Bold", 24)
    c.line(cx - name_w / 2, y, cx + name_w / 2, y)
    y -= 10 * mm

    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.drawCentredString(cx, y, "has successfully participated in")
    y -= 11 * mm

    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.2, 0.3, 0.55)
    c.drawCentredString(cx, y, event_name)
    y -= 11 * mm

    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawCentredString(cx, y, date_str)

    c.showPage()
    c.save()
