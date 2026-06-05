"""
Mã Định Danh Cảm Xúc Độc Bản (Unique Emotional Signature Engine)
================================================================
Pipeline:
  1. Nhận seed = mảng [x, y, z, vx, vy, vz] từ MediaPipe landmarks
  2. XORSHIFT128+ PRNG (tự triển khai, không dùng random Python)
  3. SHA-256 hash → 64-char hex = Emotional Signature
  4. Phân tích mood từ velocity pattern
  5. Trả về: signature, mood, ui_theme, tone, accent_color
"""

import hashlib
import struct
import time
import math
from typing import List, Dict, Any


# ─── XORSHIFT128+ PRNG (Pure Python) ────────────────────────────────────────

class XorShift128Plus:
    """
    Thuật toán XORSHIFT128+ - bộ sinh số ngẫu nhiên giả siêu nhanh.
    Tham khảo: Sebastiano Vigna, "Further scramblings of Marsaglia's xorshift generators" (2017)
    """

    MASK64 = 0xFFFFFFFFFFFFFFFF  # 64-bit mask

    def __init__(self, seed0: int, seed1: int):
        # Trạng thái gồm 2 số 64-bit
        self.s0 = seed0 & self.MASK64
        self.s1 = seed1 & self.MASK64
        # Warm-up: loại bỏ ảnh hưởng seed ban đầu
        for _ in range(8):
            self.next()

    def next(self) -> int:
        """Sinh số ngẫu nhiên 64-bit tiếp theo."""
        s0 = self.s0
        s1 = self.s1
        result = (s0 + s1) & self.MASK64

        s1 ^= s0
        self.s0 = (((s0 << 55) | (s0 >> 9)) ^ s1 ^ ((s1 << 14) & self.MASK64)) & self.MASK64
        self.s1 = ((s1 << 36) | (s1 >> 28)) & self.MASK64

        return result

    def next_float(self) -> float:
        """Sinh số float trong [0.0, 1.0)."""
        return (self.next() >> 11) * (1.0 / (1 << 53))

    def generate_sequence(self, n: int) -> List[int]:
        """Sinh danh sách n số ngẫu nhiên 64-bit."""
        return [self.next() for _ in range(n)]


# ─── SEED ENCODING ──────────────────────────────────────────────────────────

def landmarks_to_seed(landmarks: List[Dict]) -> tuple:
    """
    Chuyển đổi MediaPipe landmarks thành seed (s0, s1) cho XORSHIFT128+.
    
    landmarks: list of {x, y, z, vx, vy, vz} — tọa độ + vận tốc
    Mỗi cử chỉ nhỏ (chớp mắt, nghiêng đầu) sẽ tạo seed hoàn toàn khác.
    """
    if not landmarks:
        # Fallback: dùng timestamp siêu chi tiết
        t = time.time_ns()
        return (t & 0xFFFFFFFFFFFFFFFF, (t >> 32) ^ 0xDEADBEEFCAFEBABE)

    # Nhóm lẻ → s0, nhóm chẵn → s1 (để 2 seeds tương quan ít nhất)
    acc0 = 0x6C62272E07BB0142  # FNV offset basis
    acc1 = 0x517CC1B727220A95  # Golden ratio derivative

    for i, lm in enumerate(landmarks):
        x   = int(lm.get('x',  0.0) * 1e9) & 0xFFFFFFFF
        y   = int(lm.get('y',  0.0) * 1e9) & 0xFFFFFFFF
        z   = int(lm.get('z',  0.0) * 1e9) & 0xFFFFFFFF
        vx  = int(lm.get('vx', 0.0) * 1e9) & 0xFFFFFF
        vy  = int(lm.get('vy', 0.0) * 1e9) & 0xFFFFFF

        packed = (x << 32) | (y ^ (z << 16)) ^ (vx * 31337) ^ (vy * 65537)

        if i % 2 == 0:
            acc0 ^= packed
            acc0 = ((acc0 << 13) | (acc0 >> 51)) & 0xFFFFFFFFFFFFFFFF
            acc0 = (acc0 * 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        else:
            acc1 ^= packed
            acc1 = ((acc1 << 17) | (acc1 >> 47)) & 0xFFFFFFFFFFFFFFFF
            acc1 = (acc1 * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF

    # Mix thêm timestamp để đảm bảo uniqueness tuyệt đối
    ts = time.time_ns()
    acc0 ^= (ts & 0xFFFFFFFFFFFFFFFF)
    acc1 ^= ((ts >> 13) ^ 0xDEADBEEF12345678) & 0xFFFFFFFFFFFFFFFF

    return (acc0, acc1)


# ─── HASH ENGINE ────────────────────────────────────────────────────────────

def generate_signature(landmarks: List[Dict]) -> str:
    """
    Bước 1: Encode landmarks → seeds
    Bước 2: XORSHIFT128+ sinh 256 số ngẫu nhiên
    Bước 3: Pack thành bytes → SHA-256
    Bước 4: Return 64-char hex = Emotional Signature
    """
    s0, s1 = landmarks_to_seed(landmarks)
    prng = XorShift128Plus(s0, s1)

    # Sinh 256 số 64-bit
    sequence = prng.generate_sequence(256)

    # Đóng gói thành 2048 bytes
    raw_bytes = struct.pack(f'>{len(sequence)}Q', *sequence)

    # SHA-256
    signature = hashlib.sha256(raw_bytes).hexdigest()
    return signature


# ─── MOOD & THEME ANALYSIS ──────────────────────────────────────────────────

MOOD_PROFILES = {
    'calm': {
        'ui_theme': 'liquid_glass',
        'tone': 'nurturing',
        'accent_color': '#7EC8E3',    # soft sky blue
        'secondary_color': '#B8E0D2', # mint
        'description': 'Bình thản, thư giãn',
        'emoji': '🌊',
        'advice_style': 'Nhẹ nhàng, an ủi, tập trung vào sự thoải mái và cân bằng.'
    },
    'energetic': {
        'ui_theme': 'cyberpunk',
        'tone': 'dynamic',
        'accent_color': '#FF006E',    # hot pink
        'secondary_color': '#00F5FF', # electric cyan
        'description': 'Năng động, nhiệt huyết',
        'emoji': '⚡',
        'advice_style': 'Mạnh mẽ, táo bạo, khuyến khích thử những phong cách đột phá.'
    },
    'mysterious': {
        'ui_theme': 'midnight',
        'tone': 'enigmatic',
        'accent_color': '#9D4EDD',    # deep purple
        'secondary_color': '#C77DFF', # violet
        'description': 'Huyền bí, sâu sắc',
        'emoji': '🌙',
        'advice_style': 'Ẩn dụ, tinh tế, gợi ý những tông màu đậm và phong cách avant-garde.'
    },
    'confident': {
        'ui_theme': 'warm_glow',
        'tone': 'empowering',
        'accent_color': '#F4A261',    # warm orange
        'secondary_color': '#E9C46A', # golden
        'description': 'Tự tin, quyết đoán',
        'emoji': '🔥',
        'advice_style': 'Tự tin, trực tiếp, nhấn mạnh vào sức mạnh cá nhân và phong cách đặc trưng.'
    }
}


def analyze_velocity_pattern(landmarks: List[Dict]) -> Dict[str, Any]:
    """
    Phân tích pattern vận tốc để xác định mood.
    
    velocity_magnitude → tổng năng lượng chuyển động
    velocity_variance  → độ ổn định / hỗn loạn
    """
    if not landmarks:
        return {'mood': 'calm', 'energy': 0.0, 'variance': 0.0}

    velocities = []
    for lm in landmarks:
        vx = lm.get('vx', 0.0)
        vy = lm.get('vy', 0.0)
        vz = lm.get('vz', 0.0)
        mag = math.sqrt(vx**2 + vy**2 + vz**2)
        velocities.append(mag)

    if not velocities:
        return {'mood': 'calm', 'energy': 0.0, 'variance': 0.0}

    avg_energy = sum(velocities) / len(velocities)
    mean_sq = sum(v**2 for v in velocities) / len(velocities)
    variance = mean_sq - avg_energy**2
    variance = max(0.0, variance)  # tránh số âm do floating point

    # Phân loại mood
    if avg_energy < 0.005:
        mood = 'calm'
    elif avg_energy < 0.02 and variance < 0.0001:
        mood = 'mysterious'
    elif avg_energy >= 0.02 and variance > 0.0002:
        mood = 'energetic'
    else:
        mood = 'confident'

    return {
        'mood': mood,
        'energy': round(avg_energy, 6),
        'variance': round(variance, 8),
        'landmark_count': len(landmarks)
    }


# ─── MAIN API FUNCTION ──────────────────────────────────────────────────────

def create_emotional_signature(landmarks: List[Dict]) -> Dict[str, Any]:
    """
    Entry point chính — nhận landmarks từ MediaPipe, trả về toàn bộ thông tin.
    
    Returns:
        signature    : str  — 64-char hex SHA-256 hash
        mood         : str  — calm | energetic | mysterious | confident
        ui_theme     : str  — liquid_glass | cyberpunk | midnight | warm_glow
        tone         : str  — nurturing | dynamic | enigmatic | empowering
        accent_color : str  — hex màu chủ đạo
        secondary_color: str — hex màu phụ
        energy       : float — mức năng lượng chuyển động
        description  : str  — mô tả tiếng Việt
        emoji        : str  — biểu tượng mood
        advice_style : str  — phong cách tư vấn cho AI
        timestamp    : int  — unix timestamp ms
    """
    # 1. Phân tích velocity pattern → mood
    analysis = analyze_velocity_pattern(landmarks)
    mood = analysis['mood']

    # 2. Sinh Emotional Signature (XORSHIFT128+ → SHA-256)
    signature = generate_signature(landmarks)

    # 3. Lấy profile tương ứng mood
    profile = MOOD_PROFILES[mood]

    return {
        'signature':       signature,
        'mood':            mood,
        'ui_theme':        profile['ui_theme'],
        'tone':            profile['tone'],
        'accent_color':    profile['accent_color'],
        'secondary_color': profile['secondary_color'],
        'description':     profile['description'],
        'emoji':           profile['emoji'],
        'advice_style':    profile['advice_style'],
        'energy':          analysis['energy'],
        'variance':        analysis.get('variance', 0.0),
        'landmark_count':  analysis.get('landmark_count', 0),
        'timestamp':       int(time.time() * 1000),
    }


# ─── SELF TEST ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=== XORSHIFT128+ Emotional Signature Test ===\n")

    # Test 1: Determinism với cùng seed
    prng1 = XorShift128Plus(0xDEADBEEF, 0xCAFEBABE)
    prng2 = XorShift128Plus(0xDEADBEEF, 0xCAFEBABE)
    seq1 = prng1.generate_sequence(10)
    seq2 = prng2.generate_sequence(10)
    assert seq1 == seq2, "FAIL: Same seed should produce same sequence"
    print("✓ Determinism test passed")

    # Test 2: Different seeds → different sequences
    prng3 = XorShift128Plus(0xDEADBEEF + 1, 0xCAFEBABE)
    seq3 = prng3.generate_sequence(10)
    assert seq1 != seq3, "FAIL: Different seeds should produce different sequences"
    print("✓ Uniqueness test passed")

    # Test 3: Emotional signature từ mock landmarks
    mock_calm = [{'x': 0.5, 'y': 0.5, 'z': 0.0, 'vx': 0.001, 'vy': 0.001, 'vz': 0.0}]
    mock_energetic = [{'x': 0.5, 'y': 0.5, 'z': 0.0, 'vx': 0.05, 'vy': 0.04, 'vz': 0.01}]

    result_calm = create_emotional_signature(mock_calm)
    result_energy = create_emotional_signature(mock_energetic)

    print(f"\n✓ Calm signature: {result_calm['signature'][:16]}... | mood={result_calm['mood']} | theme={result_calm['ui_theme']}")
    print(f"✓ Energetic sig : {result_energy['signature'][:16]}... | mood={result_energy['mood']} | theme={result_energy['ui_theme']}")

    assert result_calm['signature'] != result_energy['signature'], "FAIL: Different inputs should differ"
    print("\n✓ All tests passed!")
