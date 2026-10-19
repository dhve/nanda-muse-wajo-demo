// Check visible actions against independently reviewed spoken cue times.
// Run against the local animation server, not a user's browser/profile.
const {chromium}=require('playwright');
const fs=require('fs');
const path=require('path');
const cues=[
  [23.5,'connect_alice','.muted','Following the setup',true,'Her agent completes the setup'],
  [34.0,'connect_bob','.bot',"You're set up",true,'Each agent gets its own Agent Box address'],
  [43.8,'verify','[data-target="Credential in the email"]','',true,'copy the agent credential from that same email'],
  [44.5,'verify','.field span','',false,'credential is still being copied from the email'],
  [46.4,'verify','.field span','',true,'into the secure field'],
  [47.9,'verify','.chip','Keep it private',true,'Keep it private'],
  [71.2,'discover','.muted','Searching the index',true,'searches by what the business can do'],
  [71.2,'discover','.bot',"Found Alice's Bakery",false,'the search is still in progress'],
  [73.0,'discover','.bot',"Found Alice's Bakery",true,'then finds Alice’s Bakery'],
  [114.0,'ask','.btn','Approved by Bob',true,'Bob approves the message'],
  [129.9,'reply','.bot',"Sent to Bob's agent",false,'chocolate and vanilla cakes'],
  [131.1,'reply','.bot',"Sent to Bob's agent",true,'Her agent sends the answer back'],
  [150.0,'another','.pill.bob','',false,'introducing the cake tasting example'],
  [151.7,'another','.pill.bob','',true,'Bob asks about Tuesday'],
  [152.0,'another','.panel','Reply: Yes',false,'Bob’s question is still being delivered'],
  [153.8,'another','.pill.alice','',true,'Alice replies with a time'],
];
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.RENDER_CHROME||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1920,height:1080}});
 await page.goto((process.env.PLAYER_URL||'http://127.0.0.1:8766/production/player/')+'?frame=0');
 await page.waitForFunction(()=>window.player&&document.fonts.status==='loaded');
 const results=[];
 for(const [time,scene,selector,text,visible,spoken] of cues){
   const opacity=await page.evaluate(({time,scene,selector,text})=>{
     player.seek(time);
     const el=[...document.querySelectorAll(`[data-id="${scene}"] ${selector}`)].find(e=>e.textContent.includes(text));
     if(!el)throw Error(`Missing cue target: ${scene} ${selector} ${text}`);
     let op=1;
     for(let e=el;e;e=e.parentElement){const s=getComputedStyle(e);if(s.visibility==='hidden'||s.display==='none')return 0;op*=Number(s.opacity);}
     return op;
   },{time,scene,selector,text});
   const pass=visible?opacity>=0.8:opacity<=0.05;
   results.push({time,scene,spoken,expected:visible?'visible':'hidden',opacity:+opacity.toFixed(3),pass});
 }
 await browser.close();
 const output=path.join(__dirname,'../../audio/visual-timing-qa.json');
 fs.writeFileSync(output,JSON.stringify({checks:results.length,passed:results.filter(x=>x.pass).length,results},null,2)+'\n');
 for(const r of results)console.log(`${r.pass?'PASS':'FAIL'} ${r.time}s ${r.scene}: ${r.spoken} (${r.expected}; opacity ${r.opacity})`);
 if(results.some(x=>!x.pass))process.exitCode=1;
})();
