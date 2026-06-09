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

# In-memory cache with mtime invalidation (replaces @lru_cache which can't
# detect file changes after re-compression/re-encryption).
_decrypt_cache = {}  # {file_path: (mtime, bytes)}
_CACHE_MAX = 64

def decrypt_file_to_bytes(file_path: str) -> bytes:
    """Returns the decrypted bytes of a file. Returns None if error or unencrypted fallback.
    Caches results in RAM with mtime-based invalidation."""
    p = Path(file_path)
    if not p.exists():
        return None

    mtime = p.stat().st_mtime
    cached = _decrypt_cache.get(file_path)
    if cached and cached[0] == mtime:
        return cached[1]

    with open(p, 'rb') as f:
        data = f.read()

    try:
        # Try to decrypt
        decrypted_data = _cipher.decrypt(data)
    except Exception:
        # Fallback for old, unencrypted images
        decrypted_data = data

    # Evict oldest if cache full
    if len(_decrypt_cache) >= _CACHE_MAX:
        oldest = next(iter(_decrypt_cache))
        del _decrypt_cache[oldest]

    _decrypt_cache[file_path] = (mtime, decrypted_data)
    return decrypted_data


def clear_decrypt_cache(file_path: str = None):
    """Clear decrypt cache for a specific file or all files."""
    if file_path:
        _decrypt_cache.pop(file_path, None)
    else:
        _decrypt_cache.clear()
