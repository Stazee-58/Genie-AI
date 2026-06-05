import sys
sys.stdout.reconfigure(encoding='utf-8')
text = open('my_server.py', encoding='utf-8').read()
idx = text.find('wardrobe')
print('first wardrobe mention:', idx)
# find all route decorators
import re
for m in re.finditer(r'@app\.route\("/api/wardrobe[^"]*"', text):
    print('route:', m.group(), 'at pos:', m.start())

# find last route
routes = list(re.finditer(r'@app\.route\("/api/wardrobe[^"]*"', text))
if routes:
    last_route = routes[-1]
    # find end of that route function
    end_search = text.find('\n\n\n@app.route', last_route.start())
    if end_search == -1:
        end_search = text.find('\n\nif __name__', last_route.start())
    print('Last route ends around:', end_search)
    print(repr(text[end_search-50:end_search+50]))
