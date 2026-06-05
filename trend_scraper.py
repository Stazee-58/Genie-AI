"""
Trend Scraper — Thu thập xu hướng thời trang thời gian thực
============================================================
Chiến lược:
  1. Gemini Search grounding (đã có API, an toàn pháp lý)
  2. RSS feeds công khai: Vogue, Elle, Harper's Bazaar
  3. Cache 6 giờ trong file JSON để tránh over-calling API
"""

import os
import json
import time
import hashlib
import feedparser          # pip install feedparser
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from google import genai as google_genai
from google.genai import types as genai_types
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIG ──────────────────────────────────────────────────────────────────

_GEMINI_KEY   = os.getenv("GEMINI_API_KEY")
_SEARCH_MODEL = "gemini-2.5-pro"
_CACHE_DIR    = Path(__file__).parent / '.trend_cache'
_CACHE_TTL    = 6 * 3600  # 6 giờ tính bằng giây

_CACHE_DIR.mkdir(exist_ok=True)

_genai_client = google_genai.Client(api_key=_GEMINI_KEY) if _GEMINI_KEY else None

# RSS feeds thời trang công khai (không vi phạm ToS)
FASHION_RSS_FEEDS = {
    'vogue':    'https://www.vogue.com/feed/rss',
    'elle':     'https://www.elle.com/rss/all.xml/',
    'harpers':  'https://www.harpersbazaar.com/rss/all.xml/',
    'gq':       'https://www.gq.com/feed/rss',
    'instyle':  'https://www.instyle.com/rss/all.xml',
}

# Từ khoá lọc bài liên quan thời trang
FASHION_KEYWORDS = [
    'trend', 'fashion', 'style', 'outfit', 'collection', 'season',
    'runway', 'streetwear', 'aesthetic', 'wardrobe', 'look',
    'xu hướng', 'thời trang', 'phong cách', 'bộ sưu tập',
]


# ─── CACHE HELPERS ───────────────────────────────────────────────────────────

def _cache_key(query: str) -> str:
    return hashlib.md5(query.encode()).hexdigest()[:16]


def _load_cache(key: str) -> Optional[Dict]:
    path = _CACHE_DIR / f'{key}.json'
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if time.time() - data.get('cached_at', 0) < _CACHE_TTL:
            return data
    except Exception:
        pass
    return None


def _save_cache(key: str, data: Dict):
    path = _CACHE_DIR / f'{key}.json'
    data['cached_at'] = time.time()
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        pass


# ─── RSS FEED SCRAPER ────────────────────────────────────────────────────────

def fetch_rss_trends(category: str = 'general', max_items: int = 8) -> List[Dict]:
    """
    Lấy bài mới nhất từ RSS feeds thời trang, lọc theo category.
    category: 'menswear' | 'womenswear' | 'general'
    """
    cache_key = _cache_key(f'rss_{category}')
    cached = _load_cache(cache_key)
    if cached:
        return cached.get('items', [])

    items = []
    gender_filter = []
    if category == 'menswear':
        gender_filter = ['men', 'male', 'menswear', 'gentleman', 'suit']
    elif category == 'womenswear':
        gender_filter = ['women', 'female', 'womenswear', 'dress', 'skirt']

    for source, url in FASHION_RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title   = entry.get('title', '')
                summary = entry.get('summary', entry.get('description', ''))[:300]
                link    = entry.get('link', '')
                pub     = entry.get('published', '')

                # Lọc bài liên quan thời trang
                text_lower = (title + ' ' + summary).lower()
                if not any(kw in text_lower for kw in FASHION_KEYWORDS):
                    continue

                # Lọc theo giới tính nếu cần
                if gender_filter and not any(gf in text_lower for gf in gender_filter):
                    continue

                items.append({
                    'source':  source,
                    'title':   title,
                    'summary': summary,
                    'link':    link,
                    'pub':     pub,
                })

                if len(items) >= max_items:
                    break
        except Exception as e:
            print(f"[TrendScraper] RSS {source} error: {e}")
            continue

        if len(items) >= max_items:
            break

    _save_cache(cache_key, {'items': items})
    return items


# ─── GEMINI SEARCH TREND ANALYSIS ────────────────────────────────────────────

def search_fashion_trends(query: str, gender: str = 'unisex') -> Dict:
    """
    Dùng Gemini Search grounding để lấy xu hướng thời trang mới nhất.
    Kết quả được cache 6 giờ.
    """
    full_query = f"{gender} {query}" if gender != 'unisex' else query
    cache_key  = _cache_key(full_query)
    cached     = _load_cache(cache_key)
    if cached:
        return cached

    if not _genai_client:
        return {'error': 'Thiếu GEMINI_API_KEY', 'trends': [], 'summary': ''}

    prompt = f"""
Bạn là chuyên gia xu hướng thời trang. Hãy tìm kiếm và tổng hợp thông tin mới nhất (2025-2026) về:

"{full_query}"

Trả lời bằng tiếng Việt, bao gồm:
1. TOP 5 xu hướng đang hot nhất hiện tại
2. Màu sắc nổi bật của mùa này
3. Chất liệu và kiểu dáng được ưa chuộng
4. Gợi ý phối đồ thực tế

Chú ý: Ưu tiên các thông tin cụ thể, có thể áp dụng ngay.
"""

    try:
        tool = genai_types.Tool(google_search=genai_types.GoogleSearch())
        resp = _genai_client.models.generate_content(
            model=_SEARCH_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                tools=[tool],
                temperature=0.2,
            ),
        )
        result = {
            'query':     full_query,
            'summary':   resp.text,
            'trends':    _extract_trend_bullets(resp.text),
            'fetched_at': datetime.now().isoformat(),
            'source':    'gemini_search',
        }
        _save_cache(cache_key, result)
        return result
    except Exception as e:
        return {'error': str(e), 'trends': [], 'summary': ''}


def _extract_trend_bullets(text: str) -> List[str]:
    """Trích xuất các bullet point xu hướng từ response text."""
    lines = text.split('\n')
    bullets = []
    for line in lines:
        line = line.strip()
        if line and (line.startswith(('*', '-', '•', '1.', '2.', '3.', '4.', '5.'))):
            cleaned = line.lstrip('*-•0123456789. ').strip()
            if len(cleaned) > 10:
                bullets.append(cleaned)
    return bullets[:8]


# ─── REALTIME CONTEXT BUILDER ────────────────────────────────────────────────

def build_trend_context(user_query: str, gender: str = 'unisex') -> str:
    """
    Xây dựng context xu hướng để inject vào chatbot prompt.
    Kết hợp Gemini Search + RSS feeds.
    """
    # 1. Gemini Search
    search_result = search_fashion_trends(user_query, gender)
    
    # 2. RSS items
    category = 'menswear' if gender == 'male' else ('womenswear' if gender == 'female' else 'general')
    rss_items = fetch_rss_trends(category, max_items=4)

    context_parts = []

    if search_result.get('summary'):
        context_parts.append(
            f"📰 XU HƯỚNG THỜI TRANG MỚI NHẤT (Cập nhật: {datetime.now().strftime('%d/%m/%Y')}):\n"
            f"{search_result['summary'][:2000]}"
        )

    if rss_items:
        rss_text = "\n".join([
            f"• [{item['source'].upper()}] {item['title']}"
            for item in rss_items[:4]
        ])
        context_parts.append(f"\n📱 TIN TỨC THỜI TRANG GẦN ĐÂY:\n{rss_text}")

    return '\n\n'.join(context_parts) if context_parts else ''


# ─── TREND KEYWORDS DETECTION ────────────────────────────────────────────────

TREND_TRIGGER_KEYWORDS = [
    'xu hướng', 'trend', 'mốt', 'hot', 'mới nhất', 'hiện tại', 'mùa này',
    '2025', '2026', 'thịnh hành', 'phổ biến', 'nổi tiếng', 'viral',
    'collection', 'bộ sưu tập', 'tuần lễ thời trang', 'fashion week',
]

def is_trend_query(text: str) -> bool:
    """Kiểm tra xem câu hỏi có liên quan đến xu hướng thời trang không."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in TREND_TRIGGER_KEYWORDS)


# ─── SELF TEST ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=== Trend Scraper Test ===\n")
    
    # Test RSS
    print("Fetching RSS trends...")
    items = fetch_rss_trends('general', max_items=3)
    print(f"✓ Got {len(items)} RSS items")
    for item in items:
        print(f"  - [{item['source']}] {item['title'][:60]}...")
    
    # Test trend detection
    print("\n✓ Trend query detection:")
    print(f"  'xu hướng 2026'      → {is_trend_query('xu hướng 2026')}")
    print(f"  'áo sơ mi nên mặc'  → {is_trend_query('áo sơ mi nên mặc')}")
    print(f"  'fashion week Paris' → {is_trend_query('fashion week Paris')}")
