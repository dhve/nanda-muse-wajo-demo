from pathlib import Path
import re,shutil,json
P=Path(__file__).resolve().parent;V=P.parent/'revision-v4';D=P/'production/player';D.mkdir(parents=True,exist_ok=True)
for f in ['player.js','player.css']:shutil.copy2(V/'production/player'/f,D/f)
shutil.copytree(V/'production/player/assets',D/'assets',dirs_exist_ok=True)
old=(V/'production/player/index.html').read_text();prefix=old.split('<!-- 1. goal -->')[0];suffix=old[old.index('\n</div>\n\n<div id="persist">'):]
prefix=re.sub(r'  <symbol id="i-search".*?</symbol>\n','',prefix)
scenes=json.loads((P/'scenes.json').read_text())['scenes'];parts={}
def section(id,body,nom=10,focus='both'):
 return f'<section class="scene" data-id="{id}" data-nominal="{nom}" data-focus="0:{focus}"><h1 class="scene-title" data-title data-fit="1180,1"></h1>{body}</section>'
def txt(text,x,y,w=1200,cls='t40 w6',at=.2):return f'<div class="abs {cls}" style="left:{x}px;top:{y}px;width:{w}px" data-in="{at}" data-fit="{w},3">{text}</div>'
def panel(text,x,y,w,h,at=.2,cls='t44 w6'):
 return f'<div class="panel" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px" data-in="{at}"><div class="{cls}" style="padding:32px" data-fit="{w-64},4">{text}</div></div>'
def promptapp(id,pid,who,result,nom=10,topnote=''):
 app='muse' if who=='alice' else 'wajo';name='Alice in Muse' if who=='alice' else 'Bob in Wajo'
 return section(id,f'''<div class="win {app}" style="left:300px;top:155px;width:1320px;height:820px" data-in="0" data-dur=".4"><div class="win-bar"><span class="who-dot" style="background:var(--{who})"></span>{name}<span class="badge">Illustration</span></div><div class="win-body">
 {txt(topnote,90,30,1100,'t34 muted',.2) if topnote else ''}
 <div class="u-bubble" style="left:100px;top:120px;width:1100px;font-size:44px;line-height:60px" data-in=".7"><div data-prompt="{pid}" data-fit="1040,3"></div></div>
 {txt(result,100,330,1090,'t40 bot',5)}
 <div class="composer" style="left:90px;bottom:50px;width:1140px;height:100px"><div class="ph">Message</div><div class="send"><svg><use href="#i-up"/></svg></div></div></div></div>''',nom,who)
def wire(path,who='navy',at=.2):return f'<svg class="wires"><path class="wire {who}" d="{path}" data-anim="draw" data-in="{at}" data-dur="1.1"/></svg>'
def index(at=.2,sub='Known ID resolution'):
 return f'<div class="indexbox" style="left:700px;top:160px;width:520px;height:112px" data-in="{at}"><div class="n">NANDA Index</div><div class="s">{sub}</div></div>'
def delivery(pid,who='alice',at=1,y=600,out=8):
 x1,x2=(590,1330) if who=='alice' else (1330,590)
 return f'''{wire(f'M290 {y} L1630 {y}','',.2)}<div class="abox-label" style="left:720px;top:{y-140}px;width:480px" data-in=".2">AgentBox</div><div class="agentbox" style="left:720px;top:{y-50}px;width:480px;height:100px" data-in=".2"></div><div class="pill {who}" data-anim="move" data-path="{x1},{y} 960,{y} {x2},{y}" data-in="{at}" data-dur="3.3" data-pause=".4" data-out="{out}" data-prompt="{pid}" data-part="message"></div>'''
parts['goal']=section('goal',panel("Alice's Bakery<br><span class='t36 c-alice'>bakery.com</span>",360,250,560,220)+panel("Bob<br><span class='t36 c-bob'>bob@gmail.com</span>",1000,250,560,220,.8)+txt('Bob contacts the bakery.',470,600,1000,'t48 w6 center',3.2)+txt('Later, the bakery contacts Bob.',420,720,1100,'t48 w6 center',8.0)+txt('Known identities. Different agent apps.',500,875,1000,'t36 ink2 center',10),14)
# Keep the established, readable onboarding visuals and exact prompt binding.
for id in ['connect_alice','connect_bob','verify']:
 part=re.search(r'<section class="scene" data-id="'+id+r'".*?</section>',old,re.S).group(0)
 part=part.replace('Agent Box','AgentBox')
 parts[id]=part
parts['known']=promptapp('known','ask','bob',"Connecting to the agent published by bakery.com.",10,'Bob already knows the business domain.')
parts['domain']=section('domain',panel('bakery.com',390,300,480,170)+wire('M875 385 L1055 385','navy',2)+panel('Published agent<br>contact endpoint',1080,300,480,200,2.4,'t40 w6')+txt('Use the business’s direct published path.',380,620,1180,'t44 w6 center',3.5)+txt('No Index lookup is needed for this connection.',380,740,1180,'t36 ink2 center',6)+txt('Domain publication is assumed in this example.',380,850,1180,'t32 ink2 center',.2),12,'bob')
parts['menu']=section('menu',txt('Bob → Alice: What cakes are available?',350,170,1240,'t40 w6 center',.1)+delivery('ask','bob',.4,365,3.7)+f'''<div class="panel" style="left:340px;top:480px;width:1240px;height:365px" data-in="3.5">{txt('Alice in Muse',32,24,1120,'t34 w7 c-alice',0)}<div class="t38" style="position:absolute;left:32px;top:90px" data-in="3.6" data-prompt="check_alice"></div><div class="t40 w6" style="position:absolute;left:32px;top:158px;width:1160px" data-in="5.2" data-prompt="menu_reply" data-fit="1160,2"></div><div class="t34 c-bob" style="position:absolute;left:32px;top:275px;width:1160px" data-in="8">Bob receives the menu in Wajo.</div></div>'''+f'''<div class="pill alice" data-anim="move" data-path="590,365 960,365 1330,365" data-in="6.3" data-dur="3.3" data-pause=".3" data-prompt="menu_reply" data-part="message"></div>'''+txt('Bob in Wajo: <span data-prompt="check_bob"></span>',380,890,1150,'t34 center',7.4),11)
parts['later']=promptapp('later','update','alice','Resolving Bob’s registered agent ID…',12,'Later, after an order. Bob has allowed updates.')
parts['resolve']=section('resolve',index()+wire('M580 400 L580 220 L690 220','alice',6.8)+wire('M1230 220 L1370 220 L1370 400','navy',9)+panel('Known agent ID<br><span class="c-bob">bob@gmail.com</span>',330,400,560,180,0.5,'t40 w6')+panel('Bob’s hosted<br>Agent Card',1030,400,560,180,9.6,'t40 w6')+txt('Bob controls his email account.',430,665,1100,'t44 w6 center',2.8)+txt('He does not need to own gmail.com or a website.',360,760,1200,'t36 ink2 center',4.7)+txt('One known identity → its authorized card',380,890,1180,'t38 w6 center',11),15,'alice')
parts['card']=section('card',f'''<div class="card" style="left:470px;top:160px;width:980px;height:590px;border-color:var(--bob)" data-in=".2">{txt('Bob’s Agent Card',45,30,880,'t48 w7 c-bob',.2)}{txt('Hosted separately, e.g. host39',45,98,880,'t32 ink2',.3)}{txt('Known ID: bob@gmail.com',45,162,880,'t40',.4)}{txt('Identity binding verified',45,244,880,'t38 w6',2.2)}{txt('Current contact endpoint',45,326,880,'t40 w6',5)}{txt('Authentication and access rules',45,411,880,'t38',7)}</div>'''+txt('Check Bob’s permissions before connecting.',350,820,1220,'t44 w6 center',8.5)+txt('Bob has allowed order updates from this bakery.',400,910,1120,'t34 ink2 center',9.2),14,'alice')
parts['deliver']=section('deliver',index(.2,'Identity resolved')+delivery('update','alice',1.1,600,10)+txt('Bob in Wajo: <span data-prompt="check_bob"></span>',350,820,1230,'t40 center',4.5)+txt('Update received from Alice’s Bakery',400,910,1120,'t36 c-bob center',5),10,'bob')
parts['reply']=section('reply',f'''<div class="panel" style="left:365px;top:180px;width:1190px;height:190px" data-in=".2">{txt('Bob in Wajo',32,22,1110,'t34 w7 c-bob',.2)}<div class="t44 w6" style="position:absolute;left:32px;top:85px;width:1120px" data-prompt="reply" data-fit="1120,2"></div></div>'''+delivery('reply','bob',2.0,600,10)+txt('Alice in Muse: <span data-prompt="check_alice"></span>',350,820,1220,'t40 center',6)+txt('Reply received in Muse',400,910,1120,'t36 c-alice center',6.5),10,'alice')
parts['roles']=section('roles',index()+txt('A known ID resolves to a card and current endpoint.',350,330,1220,'t40 w6 center',.5)+delivery('update','alice',3.0,600,6.4)+f'''<div class="pill bob" data-anim="move" data-path="1460,600 960,600 460,600" data-in="6.6" data-dur="3.3" data-pause=".4">Reply</div>'''+txt('Neutral resolution across agent apps',350,800,1220,'t44 w6 center',7)+txt('Every connection follows the recipient’s permissions.',340,910,1240,'t34 ink2 center',9),13)
part=re.search(r'<section class="scene" data-id="end".*?</section>',old,re.S).group(0)
part=part.replace('my.nandaindex.org/demo','my.nandaindex.org/demo/v5').replace('font-size:30px;line-height:38px','font-size:30px;line-height:38px').replace('Scan to explore the Index','Scan to open the Index')
part=part.replace('class="abs t40 w6 c-link"','class="abs t36 w6 c-link"').replace('data-fit="620,1"','data-fit="720,1"')
part=part.replace('Follow the guide for the exact prompts.','Setup: my.nandaindex.org   |   agentboxnanda.org')
parts['end']=part
(D/'index.html').write_text(prefix+'\n'.join(parts[s['id']] for s in scenes)+suffix)
(D/'player.js').write_text((D/'player.js').read_text().replace('revision-v4','revision-v5'))
shutil.copy2(V/'render_direct.cjs',P/'render_direct.cjs')
r=(P/'render_direct.cjs').read_text().replace(':8766/',':8767/').replace("'-crf','0','-pix_fmt','yuv444p'","'-crf','15','-pix_fmt','yuv420p'")
(P/'render_direct.cjs').write_text(r)
print('Built 14 scenes from canonical prompts.')
