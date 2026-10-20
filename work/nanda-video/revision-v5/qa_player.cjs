const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});const p=await b.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto('http://127.0.0.1:8767/production/player/?frame=0');await p.waitForFunction(()=>window.player&&document.fonts.status==='loaded');const out=path.join(__dirname,'qa');fs.mkdirSync(out,{recursive:true});
 const info=await p.evaluate(()=>({duration:player.total,scenes:player.scenes.map(s=>({id:s.id,start:s.start,dur:s.dur})),fit:player.qaFit()}));
 await p.evaluate(()=>document.querySelector('#qa').style.display='none');
 for(const s of info.scenes){await p.evaluate(t=>{player.seek(t);document.getAnimations().forEach(a=>a.finish());},s.start+s.dur*.85);await p.screenshot({path:path.join(out,s.id+'.png')});}
 const prompts=await p.evaluate(()=>[...document.querySelectorAll('[data-prompt]')].filter(e=>!e.dataset.part).map(e=>({id:e.dataset.prompt,text:e.textContent})));
 const canonical=JSON.parse(fs.readFileSync(path.join(__dirname,'prompts.json'))).prompts;
 for(const r of prompts)if(canonical.find(x=>x.id===r.id)?.text!==r.text)errors.push('Prompt mismatch '+r.id);
 for(const c of canonical)if(!prompts.some(p=>p.id===c.id))errors.push('Prompt not shown '+c.id);
 const visibleText=await p.locator('#scenes').innerText();
 if(/\b(search|discover|discovery|discoverable)\b/i.test(visibleText))errors.push('Banned search content remains');
 fs.writeFileSync(path.join(out,'player-qa.json'),JSON.stringify({...info,errors,promptBindings:prompts.length},null,2));console.log(JSON.stringify({...info,errors,promptBindings:prompts.length}));await b.close();
 if(errors.length||info.fit.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
