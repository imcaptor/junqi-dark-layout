#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = json.loads((ROOT / 'examples' / 'v2-test-layouts.json').read_text(encoding='utf-8'))

for sample in SAMPLES:
    subprocess.run([
        'python3',
        str(ROOT / 'junqi-dark-layout' / 'scripts' / 'validate_layout.py'),
        '--layout', json.dumps(sample['layout'], ensure_ascii=False),
    ], check=True)
    subprocess.run([
        'python3',
        str(ROOT / 'junqi-dark-layout' / 'scripts' / 'render_layout.py'),
        '--title', sample['title'],
        '--subtitle', sample['subtitle'],
        '--layout', json.dumps(sample['layout'], ensure_ascii=False),
        '--notes', json.dumps(sample['notes'], ensure_ascii=False),
        '--output', str(ROOT / sample['output']),
    ], check=True)

print('done')
