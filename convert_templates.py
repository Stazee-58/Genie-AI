import os
import re
from pathlib import Path

TEMPLATES_DIR = Path('templates')
STATIC_WEB_DIR = Path('static_web')

def convert_html(content):
    # Thay thế các link href="/<path>" -> href="<path>.html"
    # cẩn thận với href="/" -> "index.html"
    
    # href="/" -> href="index.html"
    content = re.sub(r'href="/"', r'href="index.html"', content)
    
    # href="/path" -> href="path.html"
    content = re.sub(r'href="/([a-zA-Z0-9_-]+)"', r'href="\1.html"', content)
    
    # Thay thế các đường dẫn file tĩnh
    # /static/css/ -> css/
    content = content.replace('/static/css/', 'css/')
    content = content.replace('static/css/', 'css/')
    # /static/js/ -> js/
    content = content.replace('/static/js/', 'js/')
    content = content.replace('static/js/', 'js/')
    
    # Xóa các tag Jinja đơn giản (mặc dù ta sẽ xử lý thủ công các phần phức tạp sau)
    content = re.sub(r'{%\s*if\s+msg\s*%}.*?{%\s*endif\s*%}', '', content, flags=re.DOTALL)
    
    # Thêm script api_keys vào trước </head>
    api_script = '<script src="js/api_keys.js"></script>\n</head>'
    content = content.replace('</head>', api_script)

    # Thêm thư viện imgly vào file wardrobe
    imgly_script = '<script src="https://cdn.jsdelivr.net/npm/@imgly/background-removal@1.4.3/dist/browser/bundle.umd.min.js"></script>\n</head>'
    if '<title>Tủ Quần Áo' in content:
        content = content.replace('</head>', imgly_script)

    return content

def main():
    if not STATIC_WEB_DIR.exists():
        STATIC_WEB_DIR.mkdir()

    for html_file in TEMPLATES_DIR.glob('*.html'):
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = convert_html(content)

        out_name = html_file.name
        if out_name == 'home.html':
            out_name = 'index.html'

        with open(STATIC_WEB_DIR / out_name, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"Converted {html_file.name} -> {out_name}")

if __name__ == '__main__':
    main()
