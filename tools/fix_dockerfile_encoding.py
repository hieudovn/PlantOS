import os
path = r'd:\Project\Github\PlantOS\edge-v2\Dockerfile'
with open(path, 'rb') as f:
    data = f.read()
# Convert UTF-16LE to UTF-8
text = data.decode('utf-16-le')
with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)
print(f'Converted {len(data)} bytes UTF-16LE -> {len(text)} chars UTF-8')
# Verify
with open(path, 'rb') as f:
    first = f.read(4)
print(f'First 4 bytes: {first.hex()} (should be 46524f4d = FROM)')
