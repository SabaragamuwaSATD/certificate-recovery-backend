from flask import request
from app.services.firebase import FirebaseService
from app.services.pdf import PDFService
from app.utils.exceptions import CertificateError
from datetime import datetime


class CertificateService:
    @staticmethod
    def create_request(user):
        try:
            # Print incoming form data and files for debugging
            print("Form Data:", request.form)
            print("Uploaded Files:", request.files)

            data = request.form
            files = request.files

            # Upload supporting document
            doc_url = FirebaseService.upload_file(
                files['document'],
                f"requests/{user['uid']}/{datetime.now().isoformat()}_{files['document'].filename}"
            )

            # Create request record
            request_data = {
                'user_id': user['uid'],
                'status': 'pending',
                'document_url': doc_url,
                'created_at': datetime.now().isoformat(),
                'athlete_name': data.get('athlete_name'),
                'event_details': data.get('event_details')
            }

            FirebaseService.create_document('certificate_requests', request_data)

            return {'message': 'Request submitted successfully'}, 201

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

            # Generate certificate PDF
            request_data = doc_ref.get().to_dict()
            certificate_url = PDFService.generate_certificate(request_data)

            # Update with certificate URL
            doc_ref.update({'certificate_url': certificate_url})

            return {'message': 'Request approved successfully'}, 200
        except Exception as e:
            raise CertificateError(str(e))