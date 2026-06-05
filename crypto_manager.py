import os
from pathlib import Path
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

ENV_PATH = Path('.env')

def get_or_create_key() -> bytes:
    key_b64 = os.getenv('WARDROBE_ENCRYPTION_KEY')
    if not key_b64:
        key = Fernet.generate_key()
        key_b64 = key.decode('utf-8')
        # Append to .env
        with open(ENV_PATH, 'a', encoding='utf-8') as f:
            f.write(f"\nWARDROBE_ENCRYPTION_KEY={key_b64}\n")
        os.environ['WARDROBE_ENCRYPTION_KEY'] = key_b64
        return key
    return key_b64.encode('utf-8')

_cipher = Fernet(get_or_create_key())

def encrypt_file(file_path: str):
    """Encrypts a file in place."""
    p = Path(file_path)
    if not p.exists():
        return
    
    with open(p, 'rb') as f:
        data = f.read()
        
    encrypted_data = _cipher.encrypt(data)
    
    with open(p, 'wb') as f:
        f.write(encrypted_data)

def decrypt_file_to_bytes(file_path: str) -> bytes:
    """Returns the decrypted bytes of a file. Returns None if error or unencrypted fallback."""
    p = Path(file_path)
    if not p.exists():
        return None
        
    with open(p, 'rb') as f:
        data = f.read()
        
    try:
        # Try to decrypt
        decrypted_data = _cipher.decrypt(data)
        return decrypted_data
    except Exception:
        # Fallback for old, unencrypted images
        return data
