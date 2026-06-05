import os

with open('wardrobe_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('def get_current_weather')
end_idx = content.find('def get_weather_profile', start_idx)

new_func = """def wmo_to_text(code: int) -> tuple[str, str]:
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
    \"\"\"
    Lấy thời tiết hiện tại sử dụng API miễn phí Open-Meteo.
    Ưu tiên GPS (lat, lon), fallback về Hà Nội nếu không có GPS.
    Cache 30 phút.
    \"\"\"
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

"""

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_func + content[end_idx:]
    with open('wardrobe_manager.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched wardrobe_manager.py with Open-Meteo API successfully.")
else:
    print("Could not find get_current_weather in wardrobe_manager.py")
