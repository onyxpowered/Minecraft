#!/usr/bin/env python3
"""Builds a release of the auto-updating client from Minecraft.html.

    python3 build.py 1.0.0

Writes:
  Minecraft-Auto.html   the file to hand out: a small launcher (launcher.html) carrying the build below as inert text.
  dist/part-N.bin       the build itself (Minecraft.html with updater.js at the top of <head>), gzipped and cut into 12 MB pieces (jsDelivr will not serve a GitHub file over 20 MB)
  version.json          version, number of pieces, and the size and SHA-256 of the gzipped whole

Then commit, tag it v<version> and push; jsDelivr serves the tag at once, and every Minecraft-Auto.html
already in the wild picks it up the next time it is opened.
"""
import gzip, hashlib, json, os, sys

PART = 12 * 1024 * 1024
here = os.path.dirname(os.path.abspath(__file__))
version = sys.argv[1] if len(sys.argv) > 1 else None
if not version or len(version.split('.')) != 3:
    sys.exit(__doc__)

html = open(os.path.join(here, 'Minecraft.html'), 'rb').read().decode('latin1')
script = open(os.path.join(here, 'updater.js'), encoding='utf-8').read().replace('__BUILD__', version)
anchor = '<head>'
at = html.index(anchor)
assert at < 500, 'the page opening <head> should be at the very top'
built = html[:at + len(anchor)] + '<script>' + script + '</script>' + html[at + len(anchor):]

# The page the launcher carries: every "<" becomes \x01 so nothing inside it can end or confuse the <script> element around it.
body = built.encode('latin1')
assert b'\x01' not in body, 'the page already contains \\x01'
launcher = open(os.path.join(here, 'launcher.html'), encoding='utf-8').read().replace('__BUILD__', version)
head, tail = launcher.split('__EMBEDDED__')
auto = os.path.join(here, 'Minecraft-Auto.html')
open(auto, 'wb').write(head.encode('utf-8') + body.replace(b'<', b'\x01') + tail.encode('utf-8'))

blob = gzip.compress(built.encode('latin1'), 9, mtime=0)
dist = os.path.join(here, 'dist')
os.makedirs(dist, exist_ok=True)
for f in os.listdir(dist):
    if f.startswith('part-'): os.remove(os.path.join(dist, f))
count = 0
for i in range(0, len(blob), PART):
    open(os.path.join(dist, f'part-{count}.bin'), 'wb').write(blob[i:i + PART]); count += 1
json.dump({'version': version, 'parts': count, 'gzBytes': len(blob), 'gzSha256': hashlib.sha256(blob).hexdigest(), 'htmlBytes': len(built.encode('latin1'))},
          open(os.path.join(here, 'version.json'), 'w'), indent=2)
print(f'{version}: {len(built):,} chars, {len(blob):,} bytes gzipped in {count} parts -> Minecraft-Auto.html, dist/, version.json')
