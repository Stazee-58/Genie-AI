import os
import glob
from dotenv import load_dotenv
from google import genai
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env file.")

client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-2.5-pro"

# Danh sách các file KHÔNG nên mở rộng (vì là trang chủ, layout, logic UI)
IGNORED_FILES = {
    "home.html", 
    "base_result.html", 
    "chatbot.html", 
    "body_shape.html", 
    "face_shape.html", 
    "personal_color.html"
}

def expand_html_content(file_path):
    print(f"Bắt đầu xử lý: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        original_content = f.read()

    prompt = f"""
Bạn là một chuyên gia thời trang (Fashion Stylist) cao cấp và kỹ sư lập trình Frontend giỏi.

Nhiệm vụ của bạn là nhận định dạng code HTML của một trang kết quả phân tích thời trang (dáng người, khuôn mặt, hoặc màu sắc cá nhân) được cung cấp bên dưới. 
Bạn phải MỞ RỘNG (dài gấp 2 lần) và LÀM CHI TIẾT HƠN toàn bộ nội dung text (những đoạn tư vấn, mô tả, bí quyết, lời khuyên). Nội dung phải thể hiện được kiến thức chuyên môn sâu sắc, ngôn từ hoa mỹ, cuốn hút và đúng 100% với context / chủ đề của chính template đó.

Quy định ĐẶC BIỆT QUAN TRỌNG:
1. Bắt buộc GIỮ NGUYÊN HOÀN TOÀN cấu trúc HTML, tên thẻ, id, class, và vị trí các thẻ.
2. Bắt buộc GIỮ NGUYÊN HOÀN TOÀN các mã Jinja2 templating ví dụ như `{{% extends "base_result.html" %}}`, `{{% block ... %}}`, `{{% endblock %}}`, v.v...
3. Bắt buộc GIỮ NGUYÊN các đường link ảnh `src="..."` và các `href="..."` (không thay đổi URL ảnh).
4. CHỈ LÀM DÀI VÀ THÊM CHI TIẾT VÀO NỘI DUNG VĂN BẢN hiển thị cho người xem (text nằm trong `<p>`, `<h2>`, `<h1>`, `<li>`, thẻ block). Không làm hỏng code.
5. Chỉ trả về trực tiếp đoạn code HTML hoàn chỉnh sau khi xử lý (không bọc trong thẻ ```html nếu không cần thiết, tốt nhất trả về plain string HTML sạch, hoặc nếu có Markdown thì phần mềm sẽ tự parse). Đặc biệt không tự bỏ bớt các block đã có.

Mã HTML ban đầu:
{original_content}
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        
        # Xử lý kết quả trả về: gỡ bớt cú pháp markdown ```html nếu Gemini có đính kèm
        result_text = response.text.strip()
        if result_text.startswith("```html"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        
        result_text = result_text.strip()
        
        # Ghi đè lại file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(result_text)
            
        print(f"[Xong] Đã lưu nội dung mở rộng: {file_path}")
        return True
    
    except Exception as e:
        print(f"[FAIL] Lỗi ở file {file_path}: {e}")
        return False

def main():
    templates_dir = r"C:\Users\ADMIN\Downloads\fashionmentor-upgraded\fashionmentor-upgraded\templates"
    
    # Tìm tất cả các file html trong thư mục
    all_html_files = glob.glob(os.path.join(templates_dir, "*.html"))
    
    target_files = []
    for path in all_html_files:
        filename = os.path.basename(path)
        if filename not in IGNORED_FILES:
            target_files.append(path)
            
    print(f"Tổng số file cần xử lý: {len(target_files)}")
    
    # Xử lý đồng thời 5 file một lúc để tăng tốc độ
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(expand_html_content, target_files)
        
    print("\nHOÀN TẤT VIỆC MỞ RỘNG TOÀN BỘ TEMPLATE HTML!")

if __name__ == '__main__':
    main()
