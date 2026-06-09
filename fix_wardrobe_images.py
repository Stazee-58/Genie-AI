"""
Fix Wardrobe Images
"""

import os
import sys
from pathlib import Path
from io import BytesIO

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image
from crypto_manager import _cipher, encrypt_file, clear_decrypt_cache

WARDROBE_DIR = Path(__file__).parent / 'static' / 'wardrobe'
MAX_SIZE = 512  # px


def fix_image(file_path: Path):
    """Decrypt → compress → re-encrypt a single wardrobe image."""
    original_size = file_path.stat().st_size
    
    # Skip small files (already compressed)
    if original_size < 500_000:  # < 500KB
        print(f"  SKIP {file_path.name} ({original_size:,} bytes — already small)")
        return False
    
    # Read raw data
    with open(file_path, 'rb') as f:
        raw = f.read()
    
    # Decrypt
    try:
        data = _cipher.decrypt(raw)
        was_encrypted = True
    except Exception:
        data = raw
        was_encrypted = False
    
    # Try to open as image
    try:
        img = Image.open(BytesIO(data))
    except Exception as e:
        print(f"  ERROR {file_path.name}: not a valid image ({e})")
        return False
    
    # Compress
    img.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)
    buf = BytesIO()
    
    if img.mode == 'RGBA':
        img.save(buf, format='PNG', optimize=True)
    else:
        img = img.convert('RGBA')
        img.save(buf, format='PNG', optimize=True)
    
    compressed = buf.getvalue()
    
    # Re-encrypt
    encrypted = _cipher.encrypt(compressed)
    
    # Write back
    with open(file_path, 'wb') as f:
        f.write(encrypted)
    
    new_size = file_path.stat().st_size
    ratio = (1 - new_size / original_size) * 100
    print(f"  ✓ {file_path.name}: {original_size:,} → {new_size:,} bytes (giảm {ratio:.0f}%)")
    return True


def main():
    print("=" * 60)
    print("Fix Wardrobe Images — Nén lại ảnh cũ quá lớn")
    print("=" * 60)
    
    if not WARDROBE_DIR.exists():
        print("Không tìm thấy thư mục wardrobe!")
        return
    
    png_files = list(WARDROBE_DIR.glob('*.png'))
    print(f"\nTìm thấy {len(png_files)} file PNG trong wardrobe")
    
    # Also handle encrypted files without extension issues
    fixed = 0
    for f in sorted(png_files):
        if '_orig' in f.name:
            print(f"  SKIP {f.name} (file gốc)")
            continue
        if fix_image(f):
            fixed += 1
    
    # Clear decrypt cache after fixing
    clear_decrypt_cache()
    
    print(f"\n{'=' * 60}")
    print(f"Đã nén {fixed}/{len(png_files)} file")
    print(f"Cache đã được xóa — ảnh mới sẽ hiển thị ngay khi reload trang")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
