import os
import base64
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from config import Config

# Derive Fernet key from Config.SECRET_KEY
def _get_encryption_cipher():
    secret = Config.SECRET_KEY.encode('utf-8')
    salt = b'onlyus_privacy_first_salt_2026'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret))
    return Fernet(key)

_cipher = _get_encryption_cipher()

def encrypt_message_content(plaintext: str) -> str:
    """Encrypts message content with AES-256 Fernet symmetric encryption."""
    if not plaintext:
        return ""
    try:
        token = _cipher.encrypt(plaintext.encode('utf-8'))
        return token.decode('utf-8')
    except Exception as e:
        print(f"[SECURITY] Encryption warning: {e}")
        return plaintext

def decrypt_message_content(ciphertext: str) -> str:
    """Decrypts message content encrypted with AES-256 Fernet."""
    if not ciphertext:
        return ""
    try:
        decrypted = _cipher.decrypt(ciphertext.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception:
        # If text is unencrypted or legacy, return as-is
        return ciphertext

def hash_passcode(passcode: str) -> str:
    """Hashes a 4-digit login passcode using Werkzeug PBKDF2."""
    if not passcode:
        return ""
    return generate_password_hash(str(passcode))

def check_passcode_hash(stored_hash: str, candidate_passcode: str) -> bool:
    """Verifies candidate passcode against stored hash or fallback plain string."""
    if not stored_hash or not candidate_passcode:
        return False
    if stored_hash.startswith(('pbkdf2:', 'scrypt:')):
        return check_password_hash(stored_hash, str(candidate_passcode))
    return stored_hash == str(candidate_passcode)

def hash_text(text: str) -> str:
    """Computes SHA-256 hash string for data hashing (e.g. notifications, user IDs)."""
    if not text:
        return ""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def generate_next_custom_user_id() -> str:
    """Generates next custom user ID in format ON0001, ON0002, ON0003..."""
    from models import User
    try:
        users = User.query.all()
    except Exception:
        users = []
    max_num = 0
    for u in users:
        val = getattr(u, 'id', None)
        if val and str(val).startswith('ON'):
            try:
                num = int(str(val)[2:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"ON{max_num + 1:04d}"



# Strict Media Extension & Mime-Type Sanitization
ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'webp',
    'webm', 'wav', 'mp3', 'ogg', 'm4a',
    'mp4', 'mov', 'pdf', 'txt', 'doc', 'docx'
}

ALLOWED_MIME_TYPES = {
    'image/png', 'image/jpeg', 'image/gif', 'image/webp',
    'audio/webm', 'audio/wav', 'audio/mpeg', 'audio/ogg', 'audio/m4a', 'audio/mp4',
    'video/webm', 'video/mp4', 'video/quicktime',
    'application/pdf', 'text/plain',
    'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/octet-stream'
}

def validate_upload_file(file_obj) -> tuple[bool, str]:
    """Validates uploaded file against allowed extensions and MIME types."""
    if not file_obj or not file_obj.filename:
        return False, "No file provided"

    filename = file_obj.filename.lower()
    ext = filename.rsplit('.', 1)[-1] if '.' in filename else ''
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File extension '.{ext}' is not permitted for security reasons."

    content_type = file_obj.content_type.lower() if file_obj.content_type else ''
    if content_type and content_type not in ALLOWED_MIME_TYPES and not content_type.startswith(('image/', 'audio/', 'video/')):
        return False, f"File content-type '{content_type}' is not allowed."

    return True, "Valid"
