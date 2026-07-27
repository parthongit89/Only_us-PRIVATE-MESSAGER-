import os
import random
import string
import base64
import smtplib
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from config import Config

PUBLIC_HEADER_IMAGE_URL = "https://only-us-private-messager.onrender.com/static/images/email_header.png"

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def generate_4digit_passcode():
    return ''.join(random.choices(string.digits, k=4))

def load_and_render_template1(folder_name, replacements=None):
    """Loads HTML template from template1/<folder_name>/email.html and prepares images for CID/hosted rendering."""
    replacements = replacements or {}
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'template1', folder_name))
    template_path = os.path.join(base_dir, 'email.html')
    
    if not os.path.exists(template_path):
        return None

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()

        import re
        # Replace relative template image src with CID inline header logo (CID is natively rendered by Gmail, Apple Mail, Outlook)
        html = re.sub(r'images/[a-zA-Z0-9_\-\.]+\.png', 'cid:header_logo', html)

        for key, val in replacements.items():
            html = html.replace(str(key), str(val))

        return html
    except Exception as e:
        print(f"[TEMPLATE LOAD ERROR] Failed loading template from {folder_name}: {e}")
        return None

def send_via_sendgrid(to_email, subject, body, html_body=None):
    api_key = Config.SENDGRID_API_KEY
    if not api_key:
        return False
    
    sender_email = getattr(Config, 'SMTP_USERNAME', 'sonavaneparthgit@gmail.com') or 'sonavaneparthgit@gmail.com'
    url = 'https://api.sendgrid.com/v3/mail/send'
    
    content_list = [{"type": "text/plain", "value": body}]
    if html_body:
        content_list.append({"type": "text/html", "value": html_body})

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": sender_email, "name": "OnlyUs App"},
        "subject": subject,
        "content": content_list
    }

    # Add inline CID image attachment for SendGrid
    header_img_path = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'images', 'email_header.png')
    if os.path.exists(header_img_path):
        try:
            with open(header_img_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
            payload["attachments"] = [{
                "content": img_b64,
                "type": "image/png",
                "filename": "email_header.png",
                "disposition": "inline",
                "content_id": "header_logo"
            }]
        except Exception as img_err:
            print(f"[SENDGRID ATTACHMENT WARNING] {img_err}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req) as resp:
            if resp.status in [200, 202]:
                print(f"[SENDGRID EMAIL SENT] Subject: '{subject}' to {to_email}")
                return True
    except Exception as e:
        print(f"[SENDGRID WARNING] {e}")
    return False

def send_email(to_email, subject, body, html_body=None):
    """Sends email via SendGrid API or SMTP using credentials in Config, supporting HTML templates."""
    if Config.SENDGRID_API_KEY and send_via_sendgrid(to_email, subject, body, html_body=html_body):
        return True

    if Config.SMTP_USERNAME and Config.SMTP_PASSWORD:
        try:
            # Create MIMEMultipart('related') to allow inline CID image attachments
            msg = MIMEMultipart('related')
            msg['From'] = Config.SMTP_USERNAME
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg_alt = MIMEMultipart('alternative')
            msg.attach(msg_alt)

            msg_alt.attach(MIMEText(body, 'plain'))
            if html_body:
                msg_alt.attach(MIMEText(html_body, 'html'))
            
            # Attach header image with CID <header_logo>
            header_img_path = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'images', 'email_header.png')
            if os.path.exists(header_img_path):
                with open(header_img_path, 'rb') as img_f:
                    img_data = img_f.read()
                img_part = MIMEImage(img_data)
                img_part.add_header('Content-ID', '<header_logo>')
                img_part.add_header('Content-Disposition', 'inline', filename='email_header.png')
                msg.attach(img_part)

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

import threading

def send_email_async(to_email, subject, body, html_body=None):
    """Dispatches email in a background thread so the web request returns instantly to the user."""
    try:
        thread = threading.Thread(target=send_email, args=(to_email, subject, body), kwargs={'html_body': html_body})
        thread.daemon = True
        thread.start()
        return True
    except Exception as e:
        print(f"[ASYNC EMAIL THREAD ERROR] {e}")
        return send_email(to_email, subject, body, html_body=html_body)

def send_otp_email(to_email, otp_code):
    subject = "Your OnlyUs Verification Code"
    body = f"Your OnlyUs verification code is: {otp_code}. It will expire in 10 minutes."
    print(f"\n==========================================")
    print(f"  [KEY] GENERATED OTP FOR {to_email}:  {otp_code}")
    print(f"==========================================\n")
    
    html_body = load_and_render_template1('OTP template', {
        '456985': str(otp_code),
        'Hi,<br>': f'Hi {to_email},<br>'
    })
    return send_email_async(to_email, subject, body, html_body=html_body)

def send_request_received_email(to_email):
    subject = "OnlyUs Account Access Request Received"
    body = f"Hello,\n\nYour access request for OnlyUs ({to_email}) has been received. Your account is currently in the Wait state pending Administrator approval.\n\nYou will receive a confirmation email as soon as your account is approved."
    
    html_body = load_and_render_template1('Report template email', {
        'Hello User,': f'Hello {to_email},',
        "We're writing to let you know that your account or one of your activities on OnlyUs has been reported by another user.": f"Your account request for OnlyUs ({to_email}) has been received.",
        "Report Details": "Request Application Details",
        "Reported Item:  </span><span style=\"background-color:#e1c3ff;white-space:pre-wrap\">None": f"Account Access Request for {to_email}",
        "Reason: </span><span style=\"background-color:#e1c3ff;white-space:pre-wrap\">None": "Pending Admin Verification",
        "Report ID: </span><span style=\"background-color:#e1c3ff;white-space:pre-wrap\">None": "REG-PENDING",
        "Date: </span><span style=\"background-color:#e1c3ff;white-space:pre-wrap\">None": datetime.now().strftime('%Y-%m-%d')
    })
    return send_email_async(to_email, subject, body, html_body=html_body)

def send_approval_email(to_email):
    subject = "OnlyUs Account Approved!"
    body = f"Congratulations!\n\nYour OnlyUs account ({to_email}) has been approved by an Administrator.\n\nYou can now log in to OnlyUs and start secure, private messaging."
    
    html_body = load_and_render_template1('invitation Template', {
        'Hello User,': f'Hello {to_email},'
    })
    return send_email_async(to_email, subject, body, html_body=html_body)

def send_rejection_email(to_email):
    subject = "OnlyUs Account Request Update"
    body = f"Hello,\n\nWe regret to inform you that your registration request for OnlyUs ({to_email}) was not approved at this time."
    
    html_body = load_and_render_template1('Rejections Email Template', {
        'Hello User,': f'Hello {to_email},'
    })
    return send_email_async(to_email, subject, body, html_body=html_body)

def send_friend_invite_email(friend_email, sender_email, passcode):
    subject = f"You've been invited to OnlyUs by {sender_email}"
    body = f"Hello,\n\nYour friend ({sender_email}) has sent you an invitation request to join OnlyUs.\n\nYour 4-digit passcode for access is: {passcode}.\nOnce Administrator approves this invitation, you can log in and start chatting!"
    
    expiry_str = (datetime.now() + timedelta(days=7)).strftime('%d %b %Y, %I:%M %p')
    html_body = load_and_render_template1('Passcode invite template', {
        'Hello User,': f'Hello {friend_email},',
        'example@gmail.com': sender_email,
        '5978': str(passcode),
        '{{EXPIRY_DATE_TIME}}': expiry_str
    })
    return send_email_async(friend_email, subject, body, html_body=html_body)

def send_report_email(to_email, reported_item="Account Activity", reason="Community guidelines review", report_id="REP-1001"):
    subject = "OnlyUs Account Report Notification"
    body = f"Hello,\n\nYour account ({to_email}) was reported for {reason}. Report ID: {report_id}."
    
    html_body = load_and_render_template1('Report template email', {
        'Hello User,': f'Hello {to_email},',
        'Reported Item:  </span><span style="background-color:#e1c3ff;white-space:pre-wrap">None': f'Reported Item:  </span><span style="background-color:#e1c3ff;white-space:pre-wrap">{reported_item}',
        'Reason: </span><span style="background-color:#e1c3ff;white-space:pre-wrap">None': f'Reason: </span><span style="background-color:#e1c3ff;white-space:pre-wrap">{reason}',
        'Report ID: </span><span style="background-color:#e1c3ff;white-space:pre-wrap">None': f'Report ID: </span><span style="background-color:#e1c3ff;white-space:pre-wrap">{report_id}',
        'Date: </span><span style="background-color:#e1c3ff;white-space:pre-wrap">None': f'Date: </span><span style="background-color:#e1c3ff;white-space:pre-wrap">{datetime.now().strftime("%Y-%m-%d")}'
    })
    return send_email_async(to_email, subject, body, html_body=html_body)


