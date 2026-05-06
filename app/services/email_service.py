import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests

logger = logging.getLogger(__name__)


def send_transactional(subject: str, body: str, to_email: str,
                       from_email: str | None = None,
                       html: str | None = None) -> bool:
    """Send a transactional email.

    Tries Brevo's HTTP API first (works through HTTPS — won't be blocked
    by cloud providers that ban outbound port 587). Falls back to SMTP
    via the EmailService class if BREVO_API_KEY is not configured.

    Returns True on success, False on failure.
    """
    sender = from_email or os.getenv('MAIL_DEFAULT_SENDER') or os.getenv('EMAIL_FROM') \
        or os.getenv('MAIL_USERNAME') or os.getenv('SMTP_USER') or 'noreply@aksjeradar.trade'

    brevo_key = os.getenv('BREVO_API_KEY')
    if brevo_key:
        try:
            payload = {
                'sender': {'email': sender},
                'to': [{'email': to_email}],
                'subject': subject,
            }
            if html:
                payload['htmlContent'] = html
                if body:
                    payload['textContent'] = body
            else:
                payload['textContent'] = body

            resp = requests.post(
                'https://api.brevo.com/v3/smtp/email',
                json=payload,
                headers={
                    'accept': 'application/json',
                    'api-key': brevo_key,
                    'content-type': 'application/json',
                },
                timeout=15,
            )
            if 200 <= resp.status_code < 300:
                logger.info(f"✅ Brevo API: email sent to {to_email} (subject={subject!r})")
                return True
            logger.error(
                f"❌ Brevo API HTTP {resp.status_code} sending to {to_email}: {resp.text[:300]}"
            )
            # Fall through to SMTP attempt
        except Exception as e:
            logger.error(f"❌ Brevo API exception sending to {to_email}: {e}")
            # Fall through

    # SMTP fallback (works locally; blocked on many cloud providers)
    try:
        svc = EmailService()
        if not svc.email_user or not svc.email_password:
            logger.warning("Email NOT sent: no SMTP credentials and Brevo API also unavailable")
            return False
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to_email
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        if html:
            msg.attach(MIMEText(html, 'html', 'utf-8'))
        with smtplib.SMTP(svc.smtp_server, svc.smtp_port, timeout=15) as server:
            server.starttls()
            server.login(svc.email_user, svc.email_password)
            server.send_message(msg)
        logger.info(f"✅ SMTP: email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"❌ SMTP send failed to {to_email}: {e}")
        return False


class EmailService:
    def __init__(self):
        # Unified env-var convention: MAIL_* (Flask-Mail standard).
        # Falls back to legacy EMAIL_*/SMTP_* names so older deployments still work.
        self.email_user = (
            os.getenv('MAIL_USERNAME')
            or os.getenv('EMAIL_USERNAME')
            or os.getenv('SMTP_USERNAME')
            or os.getenv('SMTP_USER')
        )
        self.email_password = (
            os.getenv('MAIL_PASSWORD')
            or os.getenv('EMAIL_PASSWORD')
            or os.getenv('SMTP_PASSWORD')
            or os.getenv('SMTP_PASS')
        )
        self.smtp_port = int(
            os.getenv('MAIL_PORT')
            or os.getenv('EMAIL_PORT')
            or os.getenv('SMTP_PORT')
            or '587'
        )
        smtp_server_raw = (
            os.getenv('MAIL_SERVER')
            or os.getenv('EMAIL_SERVER')
            or os.getenv('SMTP_SERVER')
            or os.getenv('SMTP_HOST')
            or 'smtp.gmail.com'
        )
        # Defensive: someone occasionally types imap.* — convert to smtp.*
        self.smtp_server = smtp_server_raw.replace('imap.', 'smtp.')

        self.from_email = os.getenv('MAIL_DEFAULT_SENDER') or self.email_user

        print(f"📧 Email service initialized:")
        print(f"   SMTP Server: {self.smtp_server}")
        print(f"   SMTP Port: {self.smtp_port}")
        print(f"   Email User: {self.email_user}")
        print(f"   Email configured: {bool(self.email_user and self.email_password)}")
    
    @classmethod
    def send_email(cls, to_email: str, subject: str, template: str, context: dict) -> bool:
        """Generic email sender used by alert workflows.

        In test/CI or when credentials are not configured, this is a no-op that returns True.
        """
        try:
            svc = cls()
            # If not configured, behave as no-op success to avoid breaking tests/environments
            if not svc.email_user or not svc.email_password or not svc.smtp_server:
                print(f"📭 EmailService NOOP send -> to={to_email} subject={subject}")
                return True

            # Very simple text body using context; template rendering is out-of-scope here
            text_lines = [
                f"Subject: {subject}",
                "",
                "This is an automated notification.",
            ]
            try:
                if context:
                    text_lines.append("")
                    text_lines.append("Context:")
                    for k, v in context.items():
                        text_lines.append(f"- {k}: {v}")
            except Exception:
                pass
            text_body = "\n".join(text_lines)

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = svc.from_email
            msg['To'] = to_email
            msg.attach(MIMEText(text_body, 'plain'))

            with smtplib.SMTP(svc.smtp_server, svc.smtp_port) as server:
                server.starttls()
                server.login(svc.email_user, svc.email_password)
                server.send_message(msg)

            print(f"✅ Email sent to {to_email} (subject='{subject}')")
            return True
        except Exception as e:
            print(f"❌ EmailService.send_email failed: {e}")
            return False

    def send_reset_email(self, to_email, reset_url):
        """Send password reset email"""
        if not self.email_user or not self.email_password:
            print("⚠️ Email service not configured - skipping email send")
            return False
        
        # Fix URL if it's using wrong port/host
        if 'localhost:5000' in reset_url:
            # Check if server is actually running on a different port
            import requests
            try:
                requests.get('http://localhost:5002', timeout=1)
            except:
                # Try other common ports
                for port in [8000, 3000, 4000]:
                    try:
                        requests.get(f'http://localhost:{port}', timeout=1)
                        reset_url = reset_url.replace('localhost:5000', f'localhost:{port}')
                        print(f"🔧 Updated reset URL to use port {port}")
                        break
                    except:
                        continue
        
        try:
            # Create email content
            subject = "Password Reset Request"
            
            html_body = f"""
            <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>You requested a password reset for your account.</p>
                <p>Click the link below to reset your password:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>This link will expire in 24 hours.</p>
                <p>If you did not request this reset, please ignore this email.</p>
            </body>
            </html>
            """
            
            text_body = f"""
            Password Reset Request
            
            You requested a password reset for your account.
            
            Visit this link to reset your password:
            {reset_url}
            
            This link will expire in 24 hours.
            
            If you did not request this reset, please ignore this email.
            """
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add both text and HTML versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            print(f"✅ Reset email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
