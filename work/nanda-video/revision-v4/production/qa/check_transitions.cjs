// The scene beneath a dissolve stays opaque, so cuts never flash to an empty canvas.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.RENDER_CHROME||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1920,height:1080}});
 await page.goto('http://127.0.0.1:8766/production/player/?frame=0');
 await page.waitForFunction(()=>window.player);
 const results=await page.evaluate(()=>{
   const rows=[];
   const opaqueBackground=el=>!['transparent','rgba(0, 0, 0, 0)'].includes(getComputedStyle(el).backgroundColor);
   for(const next of player.scenes.slice(1)){
     player.seek(next.start);
     const visible=player.scenes.filter(s=>getComputedStyle(s.el).visibility==='visible');
     const lower=visible[0],upper=visible[1];
     const pass=visible.length===2&&Number(lower.el.style.opacity)>.99&&Number(upper.el.style.opacity)>.25&&Number(upper.el.style.opacity)<.75&&opaqueBackground(upper.el);
     rows.push({time:next.start,cut:next.id,pass});
     player.seek(next.start+.7);
     rows.push({time:next.start+.7,cut:next.id+' settled',pass:player.scenes.filter(s=>getComputedStyle(s.el).visibility==='visible').length===1&&Number(next.el.style.opacity)>.99});
     const entry=next.el.querySelector('[data-in]'),opacity=[];
     for(const dt of [.4,.5,.6]){player.seek(next.start+dt);opacity.push(Number(getComputedStyle(entry).opacity));}
     rows.push({time:next.start+.5,cut:next.id+' entry does not reverse',pass:opacity.every((value,j)=>j===0||value>=opacity[j-1]-.001)});
   }
   for(const [id,t] of [['ask',116.55],['reply',131.6]]){
     player.seek(t);
     const sec=document.querySelector(`[data-id="${id}"]`),layer=sec.querySelector('.scene-layer'),app=sec.querySelector('.win');
     const op=layer?Number(layer.style.opacity):0;
     rows.push({time:t,cut:id+' app to diagram',pass:!!layer&&op>.25&&op<.75&&Number(app.style.opacity)>.99&&opaqueBackground(layer)});
   }
   return rows;
 });
 await browser.close();
 const report={checks:results.length,passed:results.filter(r=>r.pass).length,results};
 fs.writeFileSync(path.join(__dirname,'../../transition-qa.json'),JSON.stringify(report,null,2)+'\n');
 for(const r of results)console.log(`${r.pass?'PASS':'FAIL'} ${r.time}s ${r.cut}`);
 if(results.some(r=>!r.pass))process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
