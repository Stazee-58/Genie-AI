"""
Quản lý hệ thống xác thực người dùng (Login/Register).
Sử dụng SQLite database riêng: users.db
"""

import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / 'users.db'

def init_auth_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def register_user(username, password):
    """
    Đăng ký user mới.
    Trả về (True, user_id) nếu thành công, (False, error_msg) nếu thất bại.
    """
    if not username or not password:
        return False, "Tên đăng nhập và mật khẩu không được để trống."
    
    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự."
        
    conn = get_db()
    try:
        cur = conn.cursor()
        # Kiểm tra username đã tồn tại chưa
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone() is not None:
            return False, "Tên đăng nhập đã tồn tại."
            
        password_hash = generate_password_hash(password)
        cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        return True, str(cur.lastrowid)
    except Exception as e:
        return False, f"Lỗi hệ thống: {str(e)}"
    finally:
        conn.close()

def verify_user(username, password):
    """
    Kiểm tra thông tin đăng nhập.
    Trả về (True, user_id) nếu đúng, (False, error_msg) nếu sai.
    """
    if not username or not password:
        return False, "Vui lòng nhập đầy đủ thông tin."
        
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        
        if user is None:
            return False, "Tài khoản không tồn tại."
            
        if check_password_hash(user['password_hash'], password):
            return True, str(user['id'])
        else:
            return False, "Mật khẩu không đúng."
    except Exception as e:
        return False, f"Lỗi hệ thống: {str(e)}"
    finally:
        conn.close()

def get_username(user_id):
    """Lấy username từ user_id"""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user = cur.fetchone()
        return user['username'] if user else None
    finally:
        conn.close()

def upgrade_db():
    """Nâng cấp schema DB thêm các cột profile"""
    conn = get_db()
    try:
        cur = conn.cursor()
        # Thêm các cột nếu chưa có (dùng cơ chế PRAGMA table_info hoặc try-except đơn giản)
        try:
            cur.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
        except sqlite3.OperationalError:
            pass # Cột đã tồn tại
        try:
            cur.execute("ALTER TABLE users ADD COLUMN dob TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("ALTER TABLE users ADD COLUMN gender TEXT")
        except sqlite3.OperationalError:
            pass
        conn.commit()
    finally:
        conn.close()

def get_user_profile(user_id):
    """Lấy thông tin profile của user"""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username, full_name, dob, gender FROM users WHERE id = ?", (user_id,))
        user = cur.fetchone()
        if user:
            return dict(user)
        return None
    finally:
        conn.close()

def update_user_profile(user_id, full_name, dob, gender):
    """Cập nhật thông tin profile của user"""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET full_name = ?, dob = ?, gender = ? WHERE id = ?", (full_name, dob, gender, user_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating profile: {e}")
        return False
    finally:
        conn.close()

# Khởi tạo và nâng cấp DB khi import
init_auth_db()
upgrade_db()
