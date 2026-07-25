import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def generate_4digit_passcode():
    return ''.join(random.choices(string.digits, k=4))

def send_email(to_email, subject, body):
    """Sends email via SMTP using credentials in Config if configured, or prints in development log."""
    if Config.SMTP_USERNAME and Config.SMTP_PASSWORD:
        try:
            msg = MIMEMultipart()
            msg['From'] = Config.SMTP_USERNAME
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
            server.starttls()
            server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            print(f"[SMTP EMAIL SENT] Subject: '{subject}' to {to_email}")
            return True
        except Exception as e:
            print(f"[SMTP WARNING] Could not dispatch email via SMTP ({e}).")
            print(f"[LOCAL EMAIL LOG] To: {to_email} | Subject: '{subject}'\nBody:\n{body}\n---")
            return False
    else:
        print(f"[LOCAL EMAIL LOG] To: {to_email} | Subject: '{subject}'\nBody:\n{body}\n---")
        return True

def send_otp_email(to_email, otp_code):
    subject = "Your OnlyUs Verification Code"
    body = f"Your OnlyUs verification code is: {otp_code}. It will expire in 10 minutes."
    print(f"\n==========================================")
    print(f"  🔑 GENERATED OTP FOR {to_email}:  {otp_code}")
    print(f"==========================================\n")
    return send_email(to_email, subject, body)

def send_request_received_email(to_email):
    subject = "OnlyUs Account Access Request Received"
    body = f"Hello,\n\nYour access request for OnlyUs ({to_email}) has been received. Your account is currently in the Wait state pending Administrator approval.\n\nYou will receive a confirmation email as soon as your account is approved."
    return send_email(to_email, subject, body)

def send_approval_email(to_email):
    subject = "OnlyUs Account Approved!"
    body = f"Congratulations!\n\nYour OnlyUs account ({to_email}) has been approved by an Administrator.\n\nYou can now log in to OnlyUs and start secure, private messaging."
    return send_email(to_email, subject, body)

def send_rejection_email(to_email):
    subject = "OnlyUs Account Request Update"
    body = f"Hello,\n\nWe regret to inform you that your registration request for OnlyUs ({to_email}) was not approved at this time."
    return send_email(to_email, subject, body)

def send_friend_invite_email(friend_email, sender_email, passcode):
    subject = f"You've been invited to OnlyUs by {sender_email}"
    body = f"Hello,\n\nYour friend ({sender_email}) has sent you an invitation request to join OnlyUs.\n\nYour 4-digit passcode for access is: {passcode}.\nOnce Administrator approves this invitation, you can log in and start chatting!"
    return send_email(friend_email, subject, body)
