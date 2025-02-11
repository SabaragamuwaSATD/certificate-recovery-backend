from flask import request
from app.services.firebase import FirebaseService
from app.utils.exceptions import CertificateError
from datetime import datetime
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from app.utils.certificate_generator import generate_certificate

# Register the "Young Serif" font
pdfmetrics.registerFont(TTFont('YoungSerif', 'C:/Users/Dell/PycharmProjects/PythonProject/FlaskProject/app/services/templates/YoungSerif-Regular.ttf'))


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

            # Create request record
            request_data = {
                'user_id': user['uid'],
                'status': 'pending',
                'old_document_url': old_doc_url,
                'nic_url': nic_url,
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
    def get_status(user):
        try:
            requests = FirebaseService.get_user_requests(user['uid'])
            return {'requests': requests}, 200
        except Exception as e:
            raise CertificateError(str(e))

    # Add to CertificateService class
    @staticmethod
    def get_all_pending_requests():
        try:
            docs = FirebaseService.db.collection('certificate_requests') \
                 \
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
            certificate_path = generate_certificate(request_data)

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
    def reject_request(request_id):
        try:
            doc_ref = FirebaseService.db.collection('certificate_requests').document(request_id)
            doc_ref.update({'status': 'rejected'})
            return {'message': 'Request rejected successfully'}, 200
        except Exception as e:
            raise CertificateError(str(e))

    @staticmethod
    def download_certificate(user, request_id):
        try:
            # Check if the user has access to the certificate
            certificate = FirebaseService.db.collection('certificates').document(request_id).get().to_dict()
            if certificate['user_id'] != user['uid']:
                raise CertificateError('You do not have permission to access this certificate')

            # Get the certificate URL
            certificate_url = certificate['certificate_url']
            return {'certificate_url': certificate_url}, 200
        except Exception as e:
            raise CertificateError(str(e))

    @staticmethod
    def delete_request(user, request_id):
        try:
            # Check if the user has access to the request
            request_data = FirebaseService.db.collection('certificate_requests').document(request_id).get().to_dict()
            if request_data['user_id'] != user['uid']:
                raise CertificateError('You do not have permission to delete this request')

            # Delete the request
            FirebaseService.db.collection('certificate_requests').document(request_id).delete()
            return {'message': 'Request deleted successfully'}, 200
        except Exception as e:
            raise CertificateError(str(e))

