from pathlib import Path
import base64
import re
import zipfile

workspace = Path(__file__).resolve().parents[2]
root = workspace / 'outputs/nanda-demo'
source = (root / 'index.html').read_text()
standalone = source
for picture in sorted((root / 'screenshots').glob('*.jpg')):
    uri = 'data:image/jpeg;base64,' + base64.b64encode(picture.read_bytes()).decode()
    standalone = standalone.replace('"screenshots/' + picture.name + '"', '"' + uri + '"')
font = root / 'fonts/inter-latin.woff2'
font_uri = 'data:font/woff2;base64,' + base64.b64encode(font.read_bytes()).decode()
standalone = standalone.replace('"fonts/inter-latin.woff2"', '"' + font_uri + '"')
output = workspace / 'outputs/nanda-demo-guide.html'
output.write_text(standalone)
archive = workspace / 'outputs/nanda-demo-guide.zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
    for file in sorted(root.rglob('*')):
        if file.is_file():
            bundle.write(file, Path('nanda-demo-guide') / file.relative_to(root))

assert '"screenshots/' not in standalone
assert '"fonts/inter-latin.woff2"' not in standalone
images = re.findall(r'<img src="data:image/jpeg;base64,([^"]+)"', standalone)
assert len(images) == 7
assert len(re.findall(r'class="copy"', standalone)) == 7
with zipfile.ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    assert bundle.read('nanda-demo-guide/index.html').decode() == source
    assert bundle.read('nanda-demo-guide/fonts/inter-latin.woff2') == font.read_bytes()
print(f'Standalone HTML: {output.stat().st_size:,} bytes, with 7 embedded screenshots and Inter font.')
print(f'ZIP: {archive.stat().st_size:,} bytes. Integrity and source match verified.')
