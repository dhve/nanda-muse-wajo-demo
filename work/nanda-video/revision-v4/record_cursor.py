"""Move the real macOS pointer along the recorded walkthrough.

The user explicitly requested a native cursor recording. This helper only moves
the pointer; it does not click, type, or control the app. Start the player through
its visible UI, then supply its estimated t=0 Unix time and canvas screen bounds.
"""
from pathlib import Path
import argparse,json,subprocess,time
P=Path(__file__).resolve().parent
(P/'recording').mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--start',type=float,required=True);parser.add_argument('--x',type=float,default=0);parser.add_argument('--y',type=float,required=True);parser.add_argument('--width',type=float,required=True);args=parser.parse_args()
helper=P.parent/'alice-bob/native-recording-pointer'
moves=[
(.7,1840,1010),(16.8,490,867),(24.3,1640,940),
(29.5,515,850),(34.5,1640,940),
(38.5,485,420),(39.4,490,576),(40.6,490,896),(43.7,505,565),(50.4,1640,940),
(53,630,450),(60,1640,940),(61.5,515,850),(69.2,1640,940),
(77.0,690,206),(80.5,595,425),(88.3,1640,940),
(90.5,450,386),(92.1,450,506),(93.9,450,626),(101,1640,940),
(105.5,410,392),(107.2,410,586),(111.0,1640,940),
(112.35,515,852),(114.1,740,600),(115.6,1640,940),
(122.45,490,895),(124.4,1640,940),(126.35,490,895),(129.0,1640,940),
(137.45,515,879),(140.0,440,506),(146.1,1640,940),
(169.5,952,470),(176,1840,1010)]
log=[]
for t,x,y in moves:
    delay=args.start+t-time.time()
    if delay>0:time.sleep(delay)
    sx=args.x+x*args.width/1920;sy=args.y+y*args.width/1920
    began=time.time()
    subprocess.run([str(helper),'move',str(sx),str(sy),'.65'],check=True)
    log.append({'video_time':t,'actual_time_from_start':began-args.start,'canvas':[x,y],'screen':[sx,sy],'duration':.65})
(P/'recording/cursor-events.json').write_text(json.dumps({'start_epoch':args.start,'canvas_bounds':{'x':args.x,'y':args.y,'width':args.width,'height':args.width*9/16},'events':log},indent=2))
print('Native cursor path complete.')
