from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageDraw

B = Path(__file__).resolve().parent.parent
for name in sys.argv[1:]:
    target = B / 'retake' / name
    target.mkdir(exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(B / 'captures' / f'{name}.mov'),
                    '-vf', 'fps=1/2,scale=480:-1', str(target / '%03d.png')], check=True)
    files = sorted(target.glob('*.png'))
    w, h = Image.open(files[0]).size
    sheet = Image.new('RGB', (w*4, (h+24)*((len(files)+3)//4)), '#f5f8fd')
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(files):
        x, y = i%4*w, i//4*(h+24)
        sheet.paste(Image.open(path), (x, y+24))
        draw.text((x+8, y+5), f'{name} {2*i}s', fill='black')
    sheet.save(B / 'retake' / f'{name}-contact.jpg')
