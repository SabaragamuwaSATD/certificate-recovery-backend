# email_service.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class EmailService:
    @staticmethod
    def send_certificate_email(to_email, certificate_url):
        from_email = os.getenv('FROM_EMAIL')
        from_password = os.getenv('FROM_PASSWORD')
        subject = "Your Certificate is Ready"
        body = f"Dear User,\n\nYour certificate is ready. You can download it from the following link:\n{certificate_url}\n\nBest regards,\nYour Team"

        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(from_email, from_password)
            server.send_message(msg)
            server.quit()
            print("Email sent successfully")
        except Exception as e:
            print(f"Failed to send email: {str(e)}")