import sys
import re

sys.stdout.reconfigure(encoding='utf-8')
content = open('my_server.py', encoding='utf-8').read()

# 1. Add auth_manager to imports
if 'import auth_manager' not in content:
    idx = content.find('# Kh\u1edfi t\u1ea1o Flask')
    content = content[:idx] + "from functools import wraps\nimport auth_manager\nfrom flask import redirect, url_for\n\n" + content[idx:]

# 2. Add login_required decorator
if 'def login_required' not in content:
    idx = content.find('# Giao di\u1ec7n trang ch\u1ee7')
    decorator = """
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- AUTH ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        success, result = auth_manager.verify_user(username, password)
        if success:
            session['user_id'] = result
            return redirect(url_for('wardrobe_page'))
        else:
            return render_template('login.html', error=result)
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        success, result = auth_manager.register_user(username, password)
        if success:
            session['user_id'] = result
            return redirect(url_for('wardrobe_page'))
        else:
            return render_template('register.html', error=result)
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home_page'))

"""
    content = content[:idx] + decorator + content[idx:]

# 3. Protect Wardrobe Routes
def protect_route(content, func_name):
    sig = f'def {func_name}('
    idx = content.find(sig)
    if idx == -1: return content
    # find line before
    lines = content[:idx].split('\n')
    if '@login_required' not in lines[-2]:
        lines.insert(-1, '@login_required')
    return '\n'.join(lines) + content[idx:]

content = protect_route(content, 'wardrobe_page')

# 4. Modify API routes to use session['user_id']
# For /api/wardrobe/upload
content = re.sub(
    r"user_id = request\.form\.get\('user_id', 'default'\)",
    "user_id = session.get('user_id', 'default')",
    content
)

# For /api/wardrobe/items
content = re.sub(
    r"user_id = request\.args\.get\('user_id', 'default'\)",
    "user_id = session.get('user_id', 'default')",
    content
)

# Replace other occurrences in api routes
# find daily_outfit
idx_daily = content.find('def api_wardrobe_daily_outfit():')
if idx_daily != -1:
    body_start = content.find(':', idx_daily) + 1
    body_end = content.find('return jsonify', body_start)
    if body_end == -1: body_end = content.find('\n@app.route', body_start)
    body = content[body_start:body_end]
    new_body = body.replace(
        "user_id = request.args.get('user_id', 'default')",
        "user_id = session.get('user_id', 'default')"
    )
    # also add lat lon support
    if "lat = request.args.get('lat')" not in new_body:
        new_body = new_body.replace(
            "gender  = request.args.get('gender', 'unisex')",
            "gender  = request.args.get('gender', 'unisex')\n    lat = request.args.get('lat')\n    lon = request.args.get('lon')\n    lat = float(lat) if lat else None\n    lon = float(lon) if lon else None"
        )
        new_body = new_body.replace(
            "recommend_daily_outfit(user_id=user_id, gender=gender)",
            "recommend_daily_outfit(user_id=user_id, gender=gender, lat=lat, lon=lon)"
        )
    content = content[:body_start] + new_body + content[body_end:]

# find stats
idx_stats = content.find('def api_wardrobe_stats():')
if idx_stats != -1:
    body_start = content.find(':', idx_stats) + 1
    body_end = content.find('\n@app.route', body_start)
    if body_end == -1: body_end = content.find('\nif __name__', body_start)
    body = content[body_start:body_end]
    new_body = body.replace(
        "user_id = request.args.get('user_id', 'default')",
        "user_id = session.get('user_id', 'default')"
    )
    content = content[:body_start] + new_body + content[body_end:]

# Add update item route
update_route = """
@app.route("/api/wardrobe/items/<int:item_id>", methods=['PUT'])
def api_wardrobe_update_item(item_id):
    user_id = session.get('user_id', 'default')
    if user_id == 'default':
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    success = update_item(item_id, user_id=user_id, **data)
    if success:
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Update failed or item not found'}), 404
"""
if 'def api_wardrobe_update_item(' not in content:
    idx_stats = content.find('def api_wardrobe_stats():')
    content = content[:idx_stats] + update_route + "\n" + content[idx_stats:]


open('my_server.py', 'w', encoding='utf-8').write(content)
print('Patched my_server.py successfully')
