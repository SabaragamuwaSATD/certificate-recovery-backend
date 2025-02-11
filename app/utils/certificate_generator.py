# utils/certificate_generator.py
import os
import tempfile
import qrcode
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from pdfrw import PdfReader, PdfWriter, PageMerge
from app.utils.exceptions import CertificateError
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the font file
font_path = os.path.join(current_dir, '../services/templates/YoungSerif-Regular.ttf')
# Register the "Young Serif" font
pdfmetrics.registerFont(TTFont('YoungSerif', font_path))

def generate_certificate(data):
    try:
        # Construct the path to the certificate template
        template_path = os.path.join(current_dir, '../services/templates/certify.pdf')
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf').name

        # Read the template PDF
        template_pdf = PdfReader(template_path)
        template_page = template_pdf.pages[0]

        # Create a canvas object to overlay text
        overlay_path = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf').name
        c = canvas.Canvas(overlay_path, pagesize=landscape(A4))

        # Add user and event details
        c.setFont("YoungSerif", 24)
        name_text = f"{data['full_name']}"
        text_width = c.stringWidth(name_text, "YoungSerif", 24)
        page_width = landscape(A4)[0]
        x_position = (page_width - text_width) / 2
        c.drawString(x_position, 350, name_text)

        c.setFont("YoungSerif", 60)
        event_text = f"{data['event_name']}"
        text_width = c.stringWidth(event_text, "YoungSerif", 60)
        page_width = landscape(A4)[0]
        x_position = (page_width - text_width) / 2
        c.drawString(x_position, 500, event_text)

        c.setFont("Helvetica", 18)
        if data['certificate_type'] == 'Participation':
            lines = [
                f"This certificate is awarded to Appreciate for {data['certificate_type']} ",
                f"to {data['event_name']}.",
                f"Awarded on: {data['date_issued']}",
                "This is a Replacement certificate for the Original certificate."
            ]
        else:
            lines = [
                f"This certificate is awarded to recognition of their outstanding",
                f"achievement during {data['event_name']}.",
                f"Awarded on {data['date_issued']}.",
                "This is a Replacement certificate for the Original certificate."
            ]

        page_width = landscape(A4)[0]
        y_position = 300  # Starting y position for the first line
        line_height = 30  # Space between lines

        for line in lines:
            text_width = c.stringWidth(line, "Helvetica", 18)
            x_position = (page_width - text_width) / 2
            c.drawString(x_position, y_position, line)
            y_position -= line_height

        # Generate QR code with personal information
        qr_data = f"Name: {data['full_name']}\nEvent: {data['event_name']}\nDate Issued: {data['date_issued']}"
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill='black', back_color='white')

        # Save the QR code image to a temporary file
        qr_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
        qr_img.save(qr_path)

        # Add the QR code image to the certificate
        c.drawImage(qr_path, 10, 20, width=100, height=100)

        # Add e-signature
        # Construct the path to the signature image
        signature_path = os.path.join(current_dir, '../services/templates/signature.png')
        signature_img = Image.open(signature_path)

        if signature_img.mode == "RGBA":
            background = Image.new("RGB", signature_img.size, (255, 255, 255))
            background.paste(signature_img, mask=signature_img.split()[3])
            signature_img = background

        processed_signature_path = os.path.join(current_dir, '../services/templates/signature_fixed.jpg')
        signature_img.save(processed_signature_path)

        c.drawImage(processed_signature_path, 150, 130, width=160, height=60)
        c.save()

        # Merge the overlay with the template
        overlay_pdf = PdfReader(overlay_path)
        overlay_page = overlay_pdf.pages[0]
        PageMerge(template_page).add(overlay_page).render()

        # Write the final PDF
        PdfWriter(output_path, trailer=template_pdf).write()

        return output_path
    except Exception as e:
        raise CertificateError(f"Error generating certificate: {str(e)}")