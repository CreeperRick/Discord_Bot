python3.11 -c "
import json
with open('config.json', 'rb') as f:
    raw = f.read()
print('bytes:', len(raw))
print('first 50:', raw[:50])
"
