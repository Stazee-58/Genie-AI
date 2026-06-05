"""
Wardrobe Manager — Tu Quan Ao Ao Thong Minh
=============================================
Tinh nang:
  1. Upload anh quan ao -> tach nen (rembg) -> luu PNG
  2. Phan loai quan ao bang Gemini Vision
  3. SQLite DB: items, preference_history, outfit_sets
  4. GPS + OpenWeatherMap -> goi y outfit theo thoi tiet
  5. Layer-based outfit recommendation (trong -> ngoai)
  6. Preference learning: phat hien "diem mu"
  7. CRUD: them, sua ten/chu thich/phan loai, xoa items
"""

import os
import json
import time
import sqlite3
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from io import BytesIO

from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIG ──────────────────────────────────────────────────────────────────

BASE_DIR       = Path(__file__).parent
WARDROBE_DIR   = BASE_DIR / 'static' / 'wardrobe'
DB_PATH        = BASE_DIR / 'wardrobe.db'
WEATHER_API    = "https://api.openweathermap.org/data/2.5/weather"
OWM_KEY        = os.getenv("OPENWEATHER_API_KEY", "")
DEFAULT_CITY   = os.getenv("DEFAULT_CITY", "Ho Chi Minh City,VN")

WARDROBE_DIR.mkdir(parents=True, exist_ok=True)

# Gemini client (cho Vision)
_GEMINI_KEY = os.getenv("GEMINI_API_KEY")
try:
    from google import genai as google_genai
    from google.genai import types as genai_types
    _genai_client = google_genai.Client(api_key=_GEMINI_KEY) if _GEMINI_KEY else None
    _VISION_MODEL = "gemini-2.5-flash"
except ImportError:
    _genai_client = None

# Clothing categories
CLOTHING_CATEGORIES = [
    'ao thun', 'ao so mi', 'ao khoac', 'ao len', 'ao hoodie', 'ao blazer',
    'quan jean', 'quan tay', 'quan short', 'quan jogger', 'quan legging',
    'vay ngan', 'vay dai', 'dam', 'chan vay',
    'giay sneaker', 'giay cao got', 'giay boots', 'giay loafer',
    'tui xach', 'balo', 'mu', 'that lung', 'khan', 'phu kien khac',
]

CLOTHING_CATEGORIES_VI = [
    '\u00e1o thun', '\u00e1o s\u01a1 mi', '\u00e1o kho\u00e1c', '\u00e1o len', '\u00e1o hoodie', '\u00e1o blazer',
    'qu\u1ea7n jean', 'qu\u1ea7n t\u00e2y', 'qu\u1ea7n short', 'qu\u1ea7n jogger', 'qu\u1ea7n legging',
    'v\u00e1y ng\u1eafn', 'v\u00e1y d\u00e0i', '\u0111\u1ea7m', 'ch\u00e2n v\u00e1y',
    'gi\u00e0y sneaker', 'gi\u00e0y cao g\u00f3t', 'gi\u00e0y boots', 'gi\u00e0y loafer',
    't\u00fai x\u00e1ch', 'balo', 'm\u0169', 'th\u1eaft l\u01b0ng', 'kh\u0103n', 'ph\u1ee5 ki\u1ec7n kh\u00e1c',
]

WEATHER_OUTFIT_RULES = {
    'hot':  {'min': 30, 'max': 50,  'layers': 1, 'materials': ['cotton', 'linen', 'v\u1ea3i nh\u1eb9'], 'avoid': ['\u00e1o kho\u00e1c', '\u00e1o len', 'hoodie']},
    'warm': {'min': 24, 'max': 30,  'layers': 1, 'materials': ['cotton', 'chiffon'],            'avoid': ['\u00e1o len', '\u00e1o kho\u00e1c n\u1eb7ng']},
    'mild': {'min': 18, 'max': 24,  'layers': 2, 'materials': ['denim', 'cotton pha'],          'avoid': []},
    'cool': {'min': 10, 'max': 18,  'layers': 3, 'materials': ['len', 'wool', 'fleece'],        'avoid': ['\u00e1o thun m\u1ecfng']},
    'cold': {'min': -10,'max': 10,  'layers': 3, 'materials': ['len d\u00e0y', 'n\u1ec9', 'down'],        'avoid': ['qu\u1ea7n short', 'v\u00e1y ng\u1eafn']},
}


# ─── DATABASE ────────────────────────────────────────────────────────────────

def init_db():
    """Khoi tao SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS wardrobe_items (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     TEXT DEFAULT 'default',
        filename    TEXT NOT NULL,
        name        TEXT DEFAULT '',
        note        TEXT DEFAULT '',
        category    TEXT,
        subcategory TEXT,
        color       TEXT,
        gender      TEXT DEFAULT 'unisex',
        tags        TEXT DEFAULT '[]',
        wear_count  INTEGER DEFAULT 0,
        last_worn   TEXT,
        skip_count  INTEGER DEFAULT 0,
        weight      REAL DEFAULT 1.0,
        layer_order INTEGER DEFAULT 0,
        created_at  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS preference_history (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     TEXT DEFAULT 'default',
        item_id     INTEGER,
        action      TEXT,
        context     TEXT DEFAULT '{}',
        created_at  TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (item_id) REFERENCES wardrobe_items(id)
    );

    CREATE TABLE IF NOT EXISTS daily_outfits (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     TEXT DEFAULT 'default',
        date        TEXT,
        outfit_ids  TEXT DEFAULT '[]',
        weather     TEXT DEFAULT '{}',
        signature   TEXT,
        created_at  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS outfit_sets (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         TEXT DEFAULT 'default',
        name            TEXT DEFAULT '',
        note            TEXT DEFAULT '',
        item_ids        TEXT DEFAULT '[]',
        weather_profile TEXT DEFAULT '',
        occasion        TEXT DEFAULT '',
        created_at      TEXT DEFAULT (datetime('now'))
    );
    """)

    # Migration: add new columns safely
    for col, definition in [
        ('name',        'TEXT DEFAULT ""'),
        ('note',        'TEXT DEFAULT ""'),
        ('layer_order', 'INTEGER DEFAULT 0'),
    ]:
        try:
            c.execute(f'ALTER TABLE wardrobe_items ADD COLUMN {col} {definition}')
        except Exception:
            pass  # column already exists

    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── BACKGROUND REMOVAL ──────────────────────────────────────────────────────

def remove_background(image_path: str, output_path: str) -> bool:
    try:
        from rembg import remove as rembg_remove
        with open(image_path, 'rb') as f:
            input_data = f.read()
        output_data = rembg_remove(input_data)
        with open(output_path, 'wb') as f:
            f.write(output_data)
        return True
    except ImportError:
        img = Image.open(image_path).convert('RGBA')
        img.save(output_path, 'PNG')
        return False
    except Exception as e:
        print(f"[Wardrobe] BG removal error: {e}")
        img = Image.open(image_path).convert('RGBA')
        img.save(output_path, 'PNG')
        return False


# ─── AI CLASSIFICATION ───────────────────────────────────────────────────────

def classify_clothing(image_path: str) -> Dict:
    default = {
        'category': 'ph\u1ee5 ki\u1ec7n kh\u00e1c',
        'color': 'kh\u00f4ng x\u00e1c \u0111\u1ecbnh',
        'tags': [],
        'description': 'Kh\u00f4ng th\u1ec3 ph\u00e2n lo\u1ea1i',
    }
    if not _genai_client:
        return default
    try:
        with open(image_path, 'rb') as f:
            img_bytes = f.read()
        ext  = Path(image_path).suffix.lower()
        mime = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.webp': 'image/webp'}.get(ext, 'image/jpeg')

        cats = ', '.join(CLOTHING_CATEGORIES_VI[:8])
        prompt = (
            "Ph\u00e2n t\u00edch b\u1ee9c \u1ea3nh qu\u1ea7n \u00e1o/ph\u1ee5 ki\u1ec7n v\u00e0 tr\u1ea3 v\u1ec1 JSON:\n"
            "{\n"
            f"  \"category\": \"<{cats}, etc.>\",\n"
            "  \"color\": \"<m\u00e0u ch\u1ee7 \u0111\u1ea1o ti\u1ebfng Vi\u1ec7t>\",\n"
            "  \"style\": \"<casual|formal|sporty|elegant|streetwear>\",\n"
            "  \"season\": \"<summer|winter|all-season|spring-fall>\",\n"
            "  \"tags\": [\"<tag1>\", \"<tag2>\", \"<tag3>\"],\n"
            "  \"description\": \"<m\u00f4 t\u1ea3 ng\u1eafn ti\u1ebfng Vi\u1ec7t>\"\n"
            "}\nCh\u1ec9 tr\u1ea3 v\u1ec1 JSON."
        )

        resp = _genai_client.models.generate_content(
            model=_VISION_MODEL,
            contents=[
                genai_types.Part.from_bytes(data=img_bytes, mime_type=mime),
                prompt,
            ],
        )
        text = resp.text.strip()
        if '```' in text:
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return default
    except Exception as e:
        print(f"[Wardrobe] Classification error: {e}")
        return default


# ─── WEATHER API (GPS + City fallback) ───────────────────────────────────────

def wmo_to_text(code: int) -> tuple[str, str]:
    '''Chuyển đổi mã thời tiết WMO sang mô tả tiếng Việt và điều kiện tiếng Anh (để map icon/layer).'''
    mapping = {
        0: ("Trời quang", "Clear"),
        1: ("Trời ít mây", "Clouds"),
        2: ("Trời có mây", "Clouds"),
        3: ("Nhiều mây âm u", "Clouds"),
        45: ("Có sương mù", "Fog"),
        48: ("Có sương mù lạnh", "Fog"),
        51: ("Mưa phùn nhẹ", "Drizzle"),
        53: ("Mưa phùn vừa", "Drizzle"),
        55: ("Mưa phùn dày", "Drizzle"),
        61: ("Mưa nhỏ", "Rain"),
        63: ("Mưa vừa", "Rain"),
        65: ("Mưa to", "Rain"),
        71: ("Tuyết rơi nhẹ", "Snow"),
        73: ("Tuyết rơi vừa", "Snow"),
        75: ("Tuyết rơi dày", "Snow"),
        95: ("Có dông, sấm sét", "Thunderstorm")
    }
    return mapping.get(code, ("Không xác định", "Unknown"))

def get_current_weather(city: str = None, lat: float = None, lon: float = None) -> Dict:
    """
    Lấy thời tiết hiện tại sử dụng API miễn phí Open-Meteo.
    Ưu tiên GPS (lat, lon), fallback về Hà Nội nếu không có GPS.
    Cache 30 phút.
    """
    # Nếu không có GPS, lấy mặc định Hà Nội
    if lat is None or lon is None:
        lat, lon = 21.0285, 105.8542 # Hà Nội
        city_name = "Hà Nội (Mặc định)"
    else:
        city_name = "Vị trí của bạn"

    cache_key = f'gps_{lat:.3f}_{lon:.3f}'
    cache_dir  = BASE_DIR / '.trend_cache'
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / f'weather_{cache_key}.json'

    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text(encoding='utf-8'))
            if time.time() - data.get('cached_at', 0) < 1800:
                return data
        except Exception:
            pass

    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        resp = requests.get(url, timeout=5)
        data = resp.json()

        if 'current_weather' not in data:
            raise Exception("Invalid API response")
            
        cw = data['current_weather']
        temp = round(cw['temperature'])
        wmo_code = cw['weathercode']
        desc, condition = wmo_to_text(wmo_code)

        result = {
            'temp':        temp,
            'feels_like':  temp, # Open-Meteo current_weather ko có feels_like, dùng temp
            'humidity':    70,   # Mock humidity
            'description': desc,
            'condition':   condition,
            'city':        city_name,
            'icon':        '01d', # Mock icon
            'lat':         lat,
            'lon':         lon,
            'cached_at':   time.time(),
        }
        cache_file.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
        return result
    except Exception as e:
        print(f"[Weather] Open-Meteo Error: {e}")
        return {'temp': 28, 'description': 'không xác định', 'condition': 'Unknown', 'mock': True}

def get_weather_profile(temp: float) -> str:
    for name, profile in WEATHER_OUTFIT_RULES.items():
        if profile['min'] <= temp <= profile['max']:
            return name
    return 'warm'


# ─── OUTFIT LAYER RECOMMENDATION ─────────────────────────────────────────────

def _generate_outfit_tips(layers: List[Dict], weather: Dict, rules: Dict) -> str:
    """Rule-based outfit tips — no API call needed."""
    temp   = weather.get('temp', 28)
    desc   = weather.get('description', '')
    avoid  = rules.get('avoid', [])
    mats   = rules.get('materials', [])
    colors = [l['item'].get('color', '') for l in layers if l.get('item')]
    tips   = []

    if temp >= 30:
        tips.append(f"\u2600\ufe0f Tr\u1eddi {desc} ({temp}\u00b0C) \u2014 ch\u1ecdn {', '.join(mats[:2])} \u0111\u1ec3 tho\u00e1ng m\u00e1t.")
    elif temp >= 24:
        tips.append(f"\u26c5 \u1ea4m \u00e1p ({temp}\u00b0C) \u2014 l\u00fd t\u01b0\u1edfng cho outfit 1 l\u1edbp nh\u1eb9.")
    elif temp >= 18:
        tips.append(f"Mat troi ({temp}\u00b0C) \u2014 th\u00eam \u00e1o kho\u00e1c m\u1ecfng ho\u1eb7c blazer.")
    else:
        tips.append(f"[Lanh] ({temp}\u00b0C) \u2014 m\u1eb7c nhi\u1ec1u l\u1edbp, \u01b0u ti\u00ean {', '.join(mats[:2])}.")

    if avoid:
        tips.append(f"\u26a0\ufe0f N\u00ean tr\u00e1nh h\u00f4m nay: {', '.join(avoid)}.")

    valid_colors = [c for c in colors if c]
    if len(valid_colors) >= 2:
        tips.append(f"\ud83c\udfa8 Ph\u1ed1i m\u00e0u: {valid_colors[0]} + {valid_colors[1]}.")

    return ' '.join(tips)


def recommend_daily_outfit(user_id: str = 'default', gender: str = 'unisex',
                           lat: float = None, lon: float = None) -> Dict:
    """
    Goi y outfit hom nay: GPS weather + layer-based selection.
    Layer 1 = Quan/Vay (mac trong)
    Layer 2 = Ao lot / Ao co ban
    Layer 3 = Ao ngoai / Ao khoac
    Layer 4 = Giay
    Layer 5 = Phu kien
    """
    weather = get_current_weather(lat=lat, lon=lon)
    temp    = weather.get('temp', 28)
    profile = get_weather_profile(temp)
    rules   = WEATHER_OUTFIT_RULES.get(profile, WEATHER_OUTFIT_RULES['warm'])

    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT * FROM wardrobe_items
            WHERE user_id = ?
              AND (gender = ? OR gender = 'unisex')
              AND skip_count <= 3
            ORDER BY weight DESC, RANDOM()
            LIMIT 50
        """, (user_id, gender)).fetchall()

        if not rows:
            return {
                'outfit': [], 'layers': [],
                'weather': weather,
                'message': 'T\u1ee7 \u0111\u1ed3 ch\u01b0a c\u00f3 qu\u1ea7n \u00e1o. H\u00e3y upload m\u1ed9t s\u1ed1 m\u00f3n \u0111\u1ea7u ti\u00ean!',
                'weather_profile': profile,
                'ai_tips': '',
            }

        items = [dict(r) for r in rows]
        for it in items:
            it['tags'] = json.loads(it.get('tags', '[]'))

        by_cat = {}
        for item in items:
            cat = item.get('category', 'kh\u00e1c')
            by_cat.setdefault(cat, []).append(item)

        LAYER_DEFS = [
            {'layer': 1, 'label': 'Qu\u1ea7n / V\u00e1y',
             'cats': ['qu\u1ea7n jean', 'qu\u1ea7n t\u00e2y', 'qu\u1ea7n short', 'qu\u1ea7n jogger', 'v\u00e1y ng\u1eafn', 'v\u00e1y d\u00e0i', '\u0111\u1ea7m', 'qu\u1ea7n legging']},
            {'layer': 2, 'label': '\u00c1o l\u00f3t / \u00c1o c\u01a1 b\u1ea3n',
             'cats': ['\u00e1o thun', '\u00e1o s\u01a1 mi']},
            {'layer': 3, 'label': '\u00c1o ngo\u00e0i / Layer',
             'cats': ['\u00e1o kho\u00e1c', '\u00e1o blazer', '\u00e1o len', '\u00e1o hoodie']},
            {'layer': 4, 'label': 'Gi\u00e0y / D\u00e9p',
             'cats': ['gi\u00e0y sneaker', 'gi\u00e0y cao g\u00f3t', 'gi\u00e0y boots', 'gi\u00e0y loafer']},
            {'layer': 5, 'label': 'Ph\u1ee5 ki\u1ec7n',
             'cats': ['t\u00fai x\u00e1ch', 'balo', 'm\u0169', 'th\u1eaft l\u01b0ng', 'kh\u0103n', 'ph\u1ee5 ki\u1ec7n kh\u00e1c']},
        ]

        outfit_layers  = []
        selected_items = []

        for layer_def in LAYER_DEFS:
            for cat in layer_def['cats']:
                if cat in by_cat and by_cat[cat]:
                    valid = [i for i in by_cat[cat] if cat not in rules.get('avoid', [])]
                    if valid:
                        best = dict(max(valid, key=lambda x: x.get('weight', 1.0)))
                        best['_layer']       = layer_def['layer']
                        best['_layer_label'] = layer_def['label']
                        outfit_layers.append({
                            'layer': layer_def['layer'],
                            'label': layer_def['label'],
                            'item':  best,
                        })
                        selected_items.append(best)
                        break  # only 1 item per layer

        ai_tips = _generate_outfit_tips(outfit_layers, weather, rules)

        city_name = weather.get('city', 'v\u1ecb tr\u00ed c\u1ee7a b\u1ea1n')
        return {
            'outfit':              selected_items[:5],
            'layers':              outfit_layers,
            'weather':             weather,
            'weather_profile':     profile,
            'layers_needed':       rules['layers'],
            'suggested_materials': rules['materials'],
            'avoid':               rules['avoid'],
            'ai_tips':             ai_tips,
            'message':             f"Outfit cho {weather.get('description', '')} ({temp}\u00b0C) t\u1ea1i {city_name}",
        }

    finally:
        conn.close()


# ─── PREFERENCE LEARNING ─────────────────────────────────────────────────────

def record_preference(item_id: int, action: str, context: Dict = None,
                      user_id: str = 'default'):
    """Ghi nhan phan hoi nguoi dung: worn|skipped|liked|disliked."""
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO preference_history (user_id, item_id, action, context)
            VALUES (?, ?, ?, ?)
        """, (user_id, item_id, action, json.dumps(context or {})))

        if action == 'worn':
            conn.execute("""
                UPDATE wardrobe_items
                SET wear_count = wear_count + 1,
                    weight = MIN(weight + 0.1, 3.0),
                    last_worn = date('now')
                WHERE id = ? AND user_id = ?
            """, (item_id, user_id))
        elif action == 'liked':
            conn.execute("""
                UPDATE wardrobe_items
                SET weight = MIN(weight + 0.2, 3.0)
                WHERE id = ? AND user_id = ?
            """, (item_id, user_id))
        elif action == 'skipped':
            conn.execute("""
                UPDATE wardrobe_items
                SET skip_count = skip_count + 1,
                    weight = MAX(weight - 0.15, 0.1)
                WHERE id = ? AND user_id = ?
            """, (item_id, user_id))
        elif action == 'disliked':
            conn.execute("""
                UPDATE wardrobe_items
                SET skip_count = skip_count + 2,
                    weight = MAX(weight - 0.3, 0.1)
                WHERE id = ? AND user_id = ?
            """, (item_id, user_id))

        conn.commit()
    finally:
        conn.close()


def get_blind_spots(user_id: str = 'default') -> List[Dict]:
    """Tim items bi skip nhieu: skip_count > 3 va weight < 0.5."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT * FROM wardrobe_items
            WHERE user_id = ? AND skip_count > 3 AND weight < 0.5
            ORDER BY skip_count DESC LIMIT 10
        """, (user_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_wardrobe_stats(user_id: str = 'default') -> Dict:
    conn = get_db()
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM wardrobe_items WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        by_cat = conn.execute("""
            SELECT category, COUNT(*) as cnt
            FROM wardrobe_items WHERE user_id = ?
            GROUP BY category ORDER BY cnt DESC
        """, (user_id,)).fetchall()
        most_worn = conn.execute("""
            SELECT * FROM wardrobe_items WHERE user_id = ?
            ORDER BY wear_count DESC LIMIT 3
        """, (user_id,)).fetchall()
        blind_spots = get_blind_spots(user_id)

        return {
            'total_items':      total,
            'by_category':      [dict(r) for r in by_cat],
            'most_worn':        [dict(r) for r in most_worn],
            'blind_spots':      blind_spots,
            'blind_spot_count': len(blind_spots),
        }
    finally:
        conn.close()


# ─── ITEM CRUD ───────────────────────────────────────────────────────────────

def add_item(filename: str, category: str, color: str, gender: str = 'unisex',
             tags: List[str] = None, user_id: str = 'default',
             name: str = '', note: str = '') -> int:
    """Them item vao wardrobe database."""
    conn = get_db()
    try:
        cur = conn.execute("""
            INSERT INTO wardrobe_items (user_id, filename, name, note, category, color, gender, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, filename, name, note, category, color, gender, json.dumps(tags or [])))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_item(item_id: int, user_id: str = 'default', **fields) -> bool:
    """
    Cap nhat metadata item: name, note, category, color, tags, gender.
    Chi cap nhat cac field duoc truyen vao.
    """
    ALLOWED = {'name', 'note', 'category', 'color', 'tags', 'gender'}
    to_update = {k: v for k, v in fields.items() if k in ALLOWED}
    if not to_update:
        return False

    if 'tags' in to_update and isinstance(to_update['tags'], list):
        to_update['tags'] = json.dumps(to_update['tags'], ensure_ascii=False)

    set_clause = ', '.join(f'{k} = ?' for k in to_update)
    values = list(to_update.values()) + [item_id, user_id]

    conn = get_db()
    try:
        conn.execute(
            f'UPDATE wardrobe_items SET {set_clause} WHERE id = ? AND user_id = ?',
            values
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_items(user_id: str = 'default', gender: str = None,
              category: str = None) -> List[Dict]:
    conn = get_db()
    try:
        query  = "SELECT * FROM wardrobe_items WHERE user_id = ?"
        params = [user_id]
        if gender and gender != 'unisex':
            query  += " AND (gender = ? OR gender = 'unisex')"
            params.append(gender)
        if category:
            query  += " AND category = ?"
            params.append(category)
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            item = dict(r)
            item['tags'] = json.loads(item.get('tags', '[]'))
            result.append(item)
        return result
    finally:
        conn.close()


def delete_item(item_id: int, user_id: str = 'default') -> bool:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT filename FROM wardrobe_items WHERE id = ? AND user_id = ?",
            (item_id, user_id)
        ).fetchone()
        if not row:
            return False
        for fname in [row['filename'], row['filename'].replace('.png', '_orig.jpg')]:
            fpath = WARDROBE_DIR / fname
            if fpath.exists():
                fpath.unlink()
        conn.execute("DELETE FROM wardrobe_items WHERE id = ? AND user_id = ?", (item_id, user_id))
        conn.execute("DELETE FROM preference_history WHERE item_id = ?", (item_id,))
        conn.commit()
        return True
    finally:
        conn.close()


# ─── OUTFIT SETS ─────────────────────────────────────────────────────────────

def save_outfit_set(user_id: str, name: str, item_ids: List[int],
                   note: str = '', weather_profile: str = '', occasion: str = '') -> int:
    """Luu mot bo outfit vao DB."""
    conn = get_db()
    try:
        cur = conn.execute("""
            INSERT INTO outfit_sets (user_id, name, note, item_ids, weather_profile, occasion)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, name, note, json.dumps(item_ids), weather_profile, occasion))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_outfit_sets(user_id: str = 'default') -> List[Dict]:
    """Lay danh sach cac bo outfit da luu."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM outfit_sets WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        result = []
        for r in rows:
            s = dict(r)
            s['item_ids'] = json.loads(s.get('item_ids', '[]'))
            items = []
            for iid in s['item_ids']:
                row = conn.execute(
                    "SELECT * FROM wardrobe_items WHERE id = ?", (iid,)
                ).fetchone()
                if row:
                    item = dict(row)
                    item['tags'] = json.loads(item.get('tags', '[]'))
                    items.append(item)
            s['items'] = items
            result.append(s)
        return result
    finally:
        conn.close()


def delete_outfit_set(set_id: int, user_id: str = 'default') -> bool:
    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM outfit_sets WHERE id = ? AND user_id = ?",
            (set_id, user_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()


# ─── INIT ────────────────────────────────────────────────────────────────────

init_db()

if __name__ == '__main__':
    print("=== Wardrobe Manager Test ===")
    print("DB:", DB_PATH)
    w = get_current_weather()
    print(f"Weather: {w.get('temp')}C - {w.get('description')}")
    print(f"Profile: {get_weather_profile(w.get('temp', 28))}")
    stats = get_wardrobe_stats()
    print(f"Items: {stats['total_items']}")
    print("update_item OK:", callable(update_item))
    print("save_outfit_set OK:", callable(save_outfit_set))
