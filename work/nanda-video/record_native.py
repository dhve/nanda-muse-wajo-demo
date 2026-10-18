from pathlib import Path
import subprocess,time,json,sys
b=Path(__file__).resolve().parent
name=sys.argv[1]; duration=float(sys.argv[2]); actions=json.loads(sys.argv[3])
p=subprocess.Popen(['/usr/sbin/screencapture','-v','-V',str(duration),'-C','-k','-R0,126,1029,534',str(b/'captures'/f'{name}.mov')])
start=time.monotonic()
for at,args in actions:
 time.sleep(max(0,at-(time.monotonic()-start)))
 subprocess.run([str(b/'native-pointer'),*map(str,args)],check=True)
p.wait(timeout=duration+10)
print(name,'recorded',flush=True)
