from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from app.services.firebase import FirebaseService
import tempfile

from app.utils.exceptions import CertificateError


class PDFService:
    @staticmethod
    def generate_certificate(data):
        try:
            # Create PDF
            filename = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf').name
            c = canvas.Canvas(filename, pagesize=A4)

            # Add content
            c.setFont("Helvetica-Bold", 24)
            c.drawCentredString(300, 700, "OFFICIAL SPORTS CERTIFICATE")

            c.setFont("Helvetica", 18)
            c.drawString(100, 650, f"Athlete Name: {data['full_name']}")
            c.drawString(100, 600, f"Event: {data['event_name']}")
            c.drawString(100, 550, f"Issue Date: {data['created_at']}")

            # Save PDF
            c.save()

            # Upload to Firebase
            with open(filename, 'rb') as f:
                cert_url = FirebaseService.upload_file(
                    f,
                    f"certificates/{data['user_id']}/{data['created_at']}.pdf"
                )

            return cert_url

        except Exception as e:
            raise CertificateError(str(e))