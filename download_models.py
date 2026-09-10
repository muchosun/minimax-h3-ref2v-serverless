"""Build-time downloads. Never called during worker startup."""
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen
import time
import shutil
import subprocess

lock = json.loads(Path(__file__).with_name('models.lock.json').read_text())
for item in lock['files']:
    target = Path('/comfyui/models') / item['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://huggingface.co/{lock['repository']}/resolve/{lock['revision']}/{item['path']}"
    for attempt in range(3):
        try:
            digest = hashlib.sha256()
            partial = target.with_suffix('.part')
            if shutil.which('aria2c'):
                subprocess.run(['aria2c', '--continue=true', '--max-connection-per-server=8',
                                '--split=8', '--min-split-size=16M', '--summary-interval=30',
                                '--console-log-level=warn', '--auto-file-renaming=false',
                                '--dir=' + str(target.parent), '--out=' + partial.name, url], check=True)
                with partial.open('rb') as source:
                    while chunk := source.read(8 * 1024 * 1024):
                        digest.update(chunk)
            else:
                with urlopen(url, timeout=120) as source, partial.open('wb') as out:
                    while chunk := source.read(8 * 1024 * 1024):
                        digest.update(chunk)
                        out.write(chunk)
            if partial.stat().st_size != item['size'] or digest.hexdigest() != item['sha256']:
                raise ValueError(f"Model integrity failed: {item['path']}")
            partial.replace(target)
            print('Verified', item['path'], flush=True)
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5)
