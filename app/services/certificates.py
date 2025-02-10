import io
import os
import tempfile

import cv2
import fitz
import numpy as np
from PIL import Image
from flask import request
from app.services.firebase import FirebaseService
from app.services.pdf import PDFService
from app.utils.exceptions import CertificateError
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pdfrw import PdfReader, PdfWriter, PageMerge



class CertificateService:
    @staticmethod
    def create_request(user):
        try:
            # Print incoming form data and files for debugging
            print("Form Data:", request.form)
            print("Uploaded Files:", request.files)

            data = request.form
            files = request.files

            # Upload supporting documents
            old_doc_url = FirebaseService.upload_file(
                files['oldDocumentCopy'],
                f"requests/{user['uid']}/{datetime.now().isoformat()}_{files['oldDocumentCopy'].filename}"
            )
            nic_url = FirebaseService.upload_file(
                files['NIC'],
                f"requests/{user['uid']}/{datetime.now().isoformat()}_{files['NIC'].filename}"
            )

            # Extract signature from NIC
            nic_file = files['NIC']
            signature_image = CertificateService.extract_signature(nic_file)

            # Upload signature image
            signature_url = FirebaseService.upload_file(
                signature_image,
                f"signatures/{user['uid']}/{datetime.now().isoformat()}_signature.png"
            )

            # Create request record
            request_data = {
                'user_id': user['uid'],
                'status': 'pending',
                'old_document_url': old_doc_url,
                'nic_url': nic_url,
                'signature_url': signature_url,
                'created_at': datetime.now().isoformat(),
                'full_name': data.get('fullName'),
                'faculty_name': data.get('facultyName'),
                'student_id': data.get('studentId'),
                'dob': data.get('dob'),
                'address': data.get('address'),
                'email': data.get('email'),
                'phone_number': data.get('phoneNumber'),
                'event_name': data.get('eventName'),
                'certificate_type': data.get('certificateType'),
                'date_issued': data.get('dateIssued'),
                'reason': data.get('reason')
            }

            # Add the request to the database and get the request_id
            doc_ref = FirebaseService.db.collection('certificate_requests').add(request_data)
            request_id = doc_ref[1].id

            # Update the request data with the request_id
            request_data['request_id'] = request_id
            FirebaseService.db.collection('certificate_requests').document(request_id).set(request_data)

            return {'message': 'Request submitted successfully', 'request_id': request_id}, 201

        except Exception as e:
            raise CertificateError(str(e))

    @staticmethod
    def extract_signature(nic_file):
        try:
            # Load image
            if nic_file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                image = Image.open(nic_file)
            elif nic_file.filename.lower().endswith('.pdf'):
                pdf_document = fitz.open(stream=nic_file.read(), filetype="pdf")
                page = pdf_document.load_page(0)
                pix = page.get_pixmap()
                image = Image.open(io.BytesIO(pix.tobytes()))
            else:
                raise CertificateError("Unsupported file format for NIC")

            # Check if image is loaded
            if image is None:
                raise CertificateError("Failed to load image from the NIC file")

            # Convert image to OpenCV format
            image = np.array(image)
            if image.shape[2] == 4:  # Handle RGBA images
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply binary thresholding to highlight signature
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

            # Find contours (potential signature regions)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Create a blank mask to extract the signature
            mask = np.zeros_like(gray)

            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = w / h  # Signature tends to be wide rather than tall

                # Filter based on aspect ratio and size
                if 2 < aspect_ratio < 10 and w > 50 and h > 20:
                    cv2.drawContours(mask, [cnt], -1, 255, thickness=cv2.FILLED)

            # Extract the signature from the original image
            signature = cv2.bitwise_and(image, image, mask=mask)

            # Crop the signature region
            x, y, w, h = cv2.boundingRect(mask)
            if w == 0 or h == 0:
                raise CertificateError("Failed to extract signature region")

            signature_cropped = signature[y:y + h, x:x + w]

            # Save the cropped signature to a temporary file
            signature_image_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
            cv2.imwrite(signature_image_path, signature_cropped)

            # Open the signature image as a binary stream for uploading
            with open(signature_image_path, 'rb') as signature_file:
                # Upload the signature using the file-like object
                signature_url = FirebaseService.upload_file(
                    signature_file,  # Pass the file-like object, not the path
                    f"signatures/{nic_file.filename}_{datetime.now().isoformat()}.png"
                )

            return signature_url

        except Exception as e:
            raise CertificateError(f"Error extracting signature: {str(e)}")

    @staticmethod
    def get_status(user):
        try:
            requests = FirebaseService.get_user_requests(user['uid'])
            return {'requests': requests}, 200
        except Exception as e:
            raise CertificateError(str(e))

    # Add to CertificateService class
    @staticmethod
    def get_all_requests():
        try:
            docs = FirebaseService.db.collection('certificate_requests') \
                .where('status', '==', 'pending') \
                .stream()
            return {'requests': [doc.to_dict() for doc in docs]}, 200
        except Exception as e:
            raise CertificateError(str(e))

    @staticmethod
    def approve_request(request_id):
        try:
            doc_ref = FirebaseService.db.collection('certificate_requests').document(request_id)
            doc_ref.update({'status': 'approved'})

            # Get request data
            request_data = doc_ref.get().to_dict()

            # Generate certificate PDF
            certificate_path = CertificateService.generate_certificate(request_data)

            # Upload certificate PDF
            with open(certificate_path, 'rb') as certificate_file:
                certificate_url = FirebaseService.upload_file(
                    certificate_file,
                    f"certificates/{request_id}_certificate.pdf"
                )

            # Update with certificate URL
            doc_ref.update({'certificate_url': certificate_url})

            # Save the certificate URL to the database
            FirebaseService.db.collection('certificates').document(request_id).set({
                'certificate_url': certificate_url,
                'user_id': request_data['user_id'],
                'created_at': datetime.now().isoformat()
            })

            return {'message': 'Request approved successfully'}, 200
        except Exception as e:
            raise CertificateError(str(e))

    @staticmethod
    def generate_certificate(data):
        try:
            # Path to the certificate template
            template_path = 'C:/Users/Dell/PycharmProjects/PythonProject/FlaskProject/app/services/templates/certify.pdf'
            output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf').name

            # Read the template PDF
            template_pdf = PdfReader(template_path)
            template_page = template_pdf.pages[0]

            # Create a canvas object to overlay text
            overlay_path = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf').name
            c = canvas.Canvas(overlay_path, pagesize=letter)

            # Add user and event details
            c.setFont("Helvetica", 12)
            c.drawString(100, 500, f"Name: {data['full_name']}")
            c.drawString(100, 480, f"Event: {data['event_name']}")
            c.drawString(100, 460, f"Date Issued: {data['date_issued']}")
            c.drawString(100, 440, f"Certificate Type: {data['certificate_type']}")

            # Save the overlay PDF
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