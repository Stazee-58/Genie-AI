from __future__ import annotations

import json
import os
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field
from PIL import Image


# =========================
# Config
# =========================
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("Thiếu GEMINI_API_KEY trong file .env")

client = genai.Client(api_key=API_KEY)

# Thư mục gốc chứa ảnh mẫu
IMAGES_ROOT = Path(r"C:\Users\ADMIN\Downloads\fashionmentor-upgraded\fashionmentor-upgraded\templates\images")

# Thư mục lưu ảnh output của session
OUTPUT_DIR = Path(r"C:\Users\ADMIN\Downloads\fashionmentor-upgraded\fashionmentor-upgraded\output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Model phân loại intent
INTENT_MODEL = "gemini-2.5-flash-lite"

# Model chỉnh ảnh
IMAGE_MODEL = "gemini-3.1-flash-image-preview"

# Các face shape hợp lệ
VALID_FACE_SHAPES = {"heart", "oblong", "oval", "round", "square"}

# Tên hiển thị đẹp hơn cho face shape
FACE_SHAPE_DISPLAY = {
    "heart": "Trái Tim (Heart)",
    "oblong": "Chữ Nhật Dài (Oblong)",
    "oval": "Bầu Dục (Oval)",
    "round": "Tròn (Round)",
    "square": "Vuông (Square)",
}

# Prefix nhận diện loại file
HAIR_PREFIXES = ("toc-", "toc_")
GLASSES_PREFIXES = ("kinh-", "kinh_", "gong-", "gong_")


# =========================
# Intent schema
# =========================
class EditTarget(str, Enum):
    HAIR = "hair"
    GLASSES = "glasses"
    BOTH = "both"
    NONE = "none"


class EditIntent(BaseModel):
    target: EditTarget = Field(
        description="User muốn đổi tóc, đổi kính, đổi cả hai, hay không rõ"
    )
    user_prompt_cleaned: str = Field(
        description="Phiên bản prompt đã làm sạch, ngắn gọn, giữ nguyên ý chính của user"
    )
    notes: str = Field(
        description="Ghi chú ngắn về cách hiểu yêu cầu"
    )


# =========================
# File helpers
# =========================
def load_image(path: str | Path) -> Image.Image:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file ảnh: {path}")
    return Image.open(path)


def is_hair_file(name: str) -> bool:
    lower = name.lower()
    return any(lower.startswith(p) for p in HAIR_PREFIXES)


def is_glasses_file(name: str) -> bool:
    lower = name.lower()
    return any(lower.startswith(p) for p in GLASSES_PREFIXES)


def get_samples(face_shape: str) -> dict[str, list[Path]]:
    """Trả về dict {'hair': [...], 'glasses': [...]} với các file ảnh tương ứng."""
    folder = IMAGES_ROOT / face_shape
    if not folder.exists():
        return {"hair": [], "glasses": []}

    hair_files = []
    glasses_files = []

    for f in sorted(folder.iterdir()):
        if not f.is_file():
            continue
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        if is_hair_file(f.name):
            hair_files.append(f)
        elif is_glasses_file(f.name):
            glasses_files.append(f)

    return {"hair": hair_files, "glasses": glasses_files}


def pretty_name(path: Path) -> str:
    """Trả tên file không có đuôi, thay - thành space, capitalize."""
    return path.stem.replace("-", " ").replace("_", " ").title()


def display_menu(title: str, items: list[Path]) -> None:
    print(f"\n{'─'*45}")
    print(f"  {title}")
    print(f"{'─'*45}")
    for i, item in enumerate(items, start=1):
        print(f"  {i}. {pretty_name(item)}")
    print(f"{'─'*45}")


def pick_from_list(items: list[Path], label: str) -> Optional[Path]:
    """Hiển thị danh sách và để user chọn bằng số. None nếu list rỗng."""
    if not items:
        print(f"  ⚠️  Không có mẫu {label} nào cho khuôn mặt này.")
        return None

    display_menu(f"Các mẫu {label} phù hợp:", items)

    while True:
        raw = input(f"Chọn số thứ tự mẫu {label} (hoặc 'skip' để bỏ qua): ").strip()
        if raw.lower() in ("skip", "s", "bỏ qua", "bo qua"):
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(items):
            return items[int(raw) - 1]
        print(f"  ❌ Vui lòng nhập số từ 1 đến {len(items)}, hoặc 'skip'.")


# =========================
# Intent classification
# =========================
def classify_user_intent(user_request: str) -> EditIntent:
    """Dùng gemini-2.5-flash-lite để phân loại yêu cầu người dùng."""
    prompt = f"""
Bạn là bộ phân loại intent cho app chỉnh ảnh thời trang.

Nhiệm vụ:
- Đọc câu user.
- Xác định user muốn:
  - hair: đổi kiểu tóc
  - glasses: đổi kính
  - both: đổi cả tóc và kính
  - none: không rõ hoặc không liên quan
- Trả về JSON đúng schema.

Câu user:
\"\"\"{user_request}\"\"\"

Quy tắc:
- Nếu user nói "đổi tóc", "kiểu tóc", "tóc giống ảnh mẫu" => hair
- Nếu user nói "đổi kính", "thêm kính", "đeo kính" => glasses
- Nếu có cả tóc lẫn kính => both
- Nếu mơ hồ quá => none
- user_prompt_cleaned: viết lại ngắn gọn, tự nhiên, giữ nguyên ý
- notes: giải thích ngắn 1 câu
"""

    response = client.models.generate_content(
        model=INTENT_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": EditIntent,
        },
    )

    text = response.text
    data = json.loads(text)
    return EditIntent(**data)


# =========================
# Image editing
# =========================
def build_edit_prompt(intent: EditIntent) -> str:
    base_rules = """
Use the first image as the base person.
Preserve the original face identity, facial features, skin tone, expression, lighting, pose, and background.
Do not change the person's face.
Make the result photorealistic, natural, and well blended.
"""

    if intent.target == EditTarget.HAIR:
        return f"""
Apply the hairstyle from the second image to the person in the first image.

{base_rules}

User request:
{intent.user_prompt_cleaned}
"""

    if intent.target == EditTarget.GLASSES:
        return f"""
Apply the glasses from the second reference image to the person in the first image.

{base_rules}

Ensure the glasses fit the face shape correctly and match the perspective.

User request:
{intent.user_prompt_cleaned}
"""

    if intent.target == EditTarget.BOTH:
        return f"""
Take the hairstyle from the second image and the glasses from the third image.

Apply both to the person in the first image.

{base_rules}

Ensure the hairstyle and glasses match the original lighting, angle, and proportions.

User request:
{intent.user_prompt_cleaned}
"""

    return f"""
Edit the first image according to this request:

{intent.user_prompt_cleaned}

{base_rules}
"""


def generate_edited_image(
    face_img: Image.Image,
    hair_img: Optional[Image.Image],
    glasses_img: Optional[Image.Image],
    intent: EditIntent,
    output_path: str | Path,
) -> None:
    """Gọi model image để chỉnh ảnh theo intent."""
    prompt = build_edit_prompt(intent)

    contents = [prompt, face_img]

    if intent.target == EditTarget.HAIR:
        if hair_img is None:
            raise ValueError("Intent là HAIR nhưng chưa có hair image")
        contents.append(hair_img)

    elif intent.target == EditTarget.GLASSES:
        if glasses_img is None:
            raise ValueError("Intent là GLASSES nhưng chưa có glasses image")
        contents.append(glasses_img)

    elif intent.target == EditTarget.BOTH:
        if hair_img is None or glasses_img is None:
            raise ValueError("Intent là BOTH nhưng thiếu hair image hoặc glasses image")
        contents.extend([hair_img, glasses_img])

    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=contents,
    )

    saved = False

    candidates = []
    if hasattr(response, "parts") and response.parts:
        candidates = response.parts
    elif hasattr(response, "candidates") and response.candidates:
        for candidate in response.candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None)
            if parts:
                candidates.extend(parts)

    for part in candidates:
        inline_data = getattr(part, "inline_data", None)
        if inline_data is not None:
            try:
                img = part.as_image()
                img.save(output_path)
                saved = True
                break
            except Exception:
                pass

    if not saved:
        raise RuntimeError(
            "Không tìm thấy ảnh output trong response. "
            "Hãy kiểm tra model/account có hỗ trợ image output không."
        )


# =========================
# Agent logic
# =========================
def ask_face_shape() -> Optional[str]:
    """Hỏi user về khuôn mặt của họ."""
    shapes = sorted(VALID_FACE_SHAPES)
    print("\n╔══════════════════════════════════════════════╗")
    print("║       👗  FASHION MENTOR – AI Stylist        ║")
    print("╚══════════════════════════════════════════════╝")
    print("\nBạn có khuôn mặt dạng nào?")
    for i, sh in enumerate(shapes, start=1):
        print(f"  {i}. {FACE_SHAPE_DISPLAY[sh]}")
    print()

    while True:
        raw = input("Nhập số hoặc tên khuôn mặt: ").strip().lower()

        # Nhập số
        if raw.isdigit() and 1 <= int(raw) <= len(shapes):
            return shapes[int(raw) - 1]

        # Nhập tên trực tiếp
        if raw in VALID_FACE_SHAPES:
            return raw

        # Nhập tên tiếng Việt gần đúng
        mapping = {
            "trai tim": "heart",
            "trái tim": "heart",
            "chu nhat dai": "oblong",
            "chữ nhật dài": "oblong",
            "bau duc": "oval",
            "bầu dục": "oval",
            "tron": "round",
            "tròn": "round",
            "vuong": "square",
            "vuông": "square",
        }
        if raw in mapping:
            return mapping[raw]

        print(f"  ❌ Không nhận ra '{raw}'. Vui lòng nhập lại.")

    return None  # unreachable but satisfies type checker


def ask_user_request() -> str:
    print("\n─────────────────────────────────────────────")
    print("Bạn muốn thử gì?")
    print("  Ví dụ: 'đổi tóc', 'thử kính', 'đổi cả tóc và kính'")
    print("─────────────────────────────────────────────")
    raw = input("Yêu cầu: ").strip()
    return raw


def ask_face_photo() -> Optional[Path]:
    """Hỏi đường dẫn ảnh khuôn mặt của user."""
    print("\n─────────────────────────────────────────────")
    print("Nhập đường dẫn ảnh khuôn mặt của bạn:")
    print("  (ví dụ: D:/me.jpg hoặc C:/Users/Bạn/Pictures/photo.png)")
    print("─────────────────────────────────────────────")
    while True:
        raw = input("Đường dẫn ảnh: ").strip().strip('"').strip("'")
        p = Path(raw)
        if p.exists() and p.is_file():
            return p
        print(f"  ❌ Không tìm thấy file: {raw}. Vui lòng thử lại.")

    return None  # unreachable


def run_agent():
    """Vòng lặp chính của agent chat."""
    print()
    face_shape = ask_face_shape()
    print(f"\n✅ Khuôn mặt: {FACE_SHAPE_DISPLAY[face_shape]}")

    face_photo_path = ask_face_photo()
    print(f"✅ Ảnh khuôn mặt: {face_photo_path.name}")

    samples = get_samples(face_shape)

    while True:
        user_request = ask_user_request()
        if not user_request:
            print("  ⚠️  Bạn chưa nhập gì. Thử lại nhé.")
            continue

        if user_request.lower() in ("quit", "exit", "thoát", "thoat", "q"):
            print("\n👋 Cảm ơn bạn đã dùng Fashion Mentor! Hẹn gặp lại.\n")
            break

        # Phân loại intent
        print("\n⏳ Đang phân tích yêu cầu...")
        intent = classify_user_intent(user_request)

        print(f"  🎯 Intent: {intent.target.value.upper()}")
        print(f"  📝 Yêu cầu đã làm sạch: {intent.user_prompt_cleaned}")

        if intent.target == EditTarget.NONE:
            print("\n❓ Mình chưa hiểu rõ bạn muốn đổi gì.")
            print("   Hãy thử nói rõ hơn, ví dụ:")
            print("   • 'Tôi muốn thử kiểu tóc mới'")
            print("   • 'Cho tôi đeo kính'")
            print("   • 'Đổi cả tóc và kính cho tôi'")
            continue

        # Resolve files
        hair_path: Optional[Path] = None
        glasses_path: Optional[Path] = None

        if intent.target in (EditTarget.HAIR, EditTarget.BOTH):
            if not samples["hair"]:
                print(f"\n⚠️  Hiện tại chưa có mẫu tóc nào cho khuôn mặt {FACE_SHAPE_DISPLAY[face_shape]}.")
                if intent.target == EditTarget.HAIR:
                    continue
            else:
                hair_path = pick_from_list(samples["hair"], "tóc")
                if hair_path is None and intent.target == EditTarget.HAIR:
                    print("  ℹ️  Bạn đã bỏ qua chọn tóc. Quay lại menu chính.")
                    continue

        if intent.target in (EditTarget.GLASSES, EditTarget.BOTH):
            if not samples["glasses"]:
                print(f"\n⚠️  Hiện tại chưa có mẫu kính nào cho khuôn mặt {FACE_SHAPE_DISPLAY[face_shape]}.")
                if intent.target == EditTarget.GLASSES:
                    continue
            else:
                glasses_path = pick_from_list(samples["glasses"], "kính")
                if glasses_path is None and intent.target == EditTarget.GLASSES:
                    print("  ℹ️  Bạn đã bỏ qua chọn kính. Quay lại menu chính.")
                    continue

        # Kiểm tra nếu cả hai đều bị skip
        if hair_path is None and glasses_path is None:
            print("  ℹ️  Bạn chưa chọn mẫu nào. Quay lại menu chính.")
            continue

        # Điều chỉnh intent nếu user BOTH nhưng chỉ chọn một
        actual_intent = intent
        if intent.target == EditTarget.BOTH:
            if hair_path is not None and glasses_path is None:
                actual_intent = EditIntent.model_validate({
                    'target': EditTarget.HAIR,
                    'user_prompt_cleaned': intent.user_prompt_cleaned,
                    'notes': intent.notes,
                })
            elif hair_path is None and glasses_path is not None:
                actual_intent = EditIntent.model_validate({
                    'target': EditTarget.GLASSES,
                    'user_prompt_cleaned': intent.user_prompt_cleaned,
                    'notes': intent.notes,
                })

        # Load ảnh
        print("\n⏳ Đang tải ảnh và xử lý...\n")
        face_img = load_image(face_photo_path)
        hair_img = load_image(hair_path) if hair_path else None
        glasses_img = load_image(glasses_path) if glasses_path else None

        # Xác định tên output
        parts = []
        if hair_path:
            parts.append(f"toc-{hair_path.stem}")
        if glasses_path:
            parts.append(f"kinh-{glasses_path.stem}")
        output_filename = f"result_{'-'.join(parts)}.png"
        output_path = OUTPUT_DIR / output_filename

        # Generate
        try:
            print("⏳ Đang tạo ảnh với AI... (có thể mất vài giây)")
            generate_edited_image(
                face_img=face_img,
                hair_img=hair_img,
                glasses_img=glasses_img,
                intent=actual_intent,
                output_path=output_path,
            )
            print(f"\n✅ Xong! Ảnh đã được lưu tại:\n   👉 {output_path}\n")
        except Exception as e:
            print(f"\n❌ Lỗi khi tạo ảnh: {e}")

        # Hỏi tiếp hay dừng
        print("─────────────────────────────────────────────")
        again = input("Bạn muốn thử thêm không? (yes / no): ").strip().lower()
        if again not in ("yes", "y", "có", "co", "tiếp", "tiep"):
            print("\n👋 Cảm ơn bạn đã dùng Fashion Mentor! Hẹn gặp lại.\n")
            break


# =========================
# Entry point
# =========================
if __name__ == "__main__":
    run_agent()