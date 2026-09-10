"""Cheap startup gate; full SHA verification already ran during image build."""
import json
from pathlib import Path

lock = json.loads(Path(__file__).with_name('models.lock.json').read_text())
for item in lock['files']:
    target = Path('/comfyui/models') / item['path']
    if not target.is_file() or target.stat().st_size != item['size']:
        raise SystemExit(f"Baked model missing or wrong size: {item['path']}")
print('H3 baked models present; no startup downloads', flush=True)
