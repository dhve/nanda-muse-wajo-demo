// Render the local animation at exact frame times in an isolated browser.
// Audio and video both start at zero. Browser loading time never enters the video.
const {chromium}=require('playwright');
const fs=require('fs');
const path=require('path');
const {spawn}=require('child_process');
const {once}=require('events');
(async()=>{
 const out=path.join(__dirname,'recording');fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:process.env.RENDER_CHROME||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 const context=await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 const page=await context.newPage();
 await page.goto('http://127.0.0.1:8766/production/player/?frame=0');
 await page.waitForFunction(()=>window.player&&document.fonts.status==='loaded');
 const fps=30,total=await page.evaluate(()=>player.total),frames=Math.round(total*fps);
 await page.evaluate(()=>{window.renderTransitions=new WeakMap();});
 const output=path.join(out,'direct-render.mp4');
 const encoder=spawn('ffmpeg',['-y','-v','warning','-f','image2pipe','-framerate',String(fps),'-vcodec','png','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','0','-pix_fmt','yuv444p','-movflags','+faststart',output],{stdio:['pipe','ignore','inherit']});
 const finished=once(encoder,'close');
 for(let frame=0;frame<frames;frame++){
   const t=frame/fps;
   await page.evaluate(t=>{
     player.seek(t);
     // Pause CSS focus transitions and advance them on the same explicit clock.
     // The player already computes all other motion as a pure function of t.
     for(const animation of document.getAnimations()){
       if(!renderTransitions.has(animation))renderTransitions.set(animation,t);
       animation.pause();
       animation.currentTime=(t-renderTransitions.get(animation))*1000;
     }
   },t);
   const png=await page.screenshot({type:'png',animations:'allow'});
   if(!encoder.stdin.write(png))await once(encoder.stdin,'drain');
   if(frame%300===0)console.log(`Rendered ${frame}/${frames} frames (${t.toFixed(0)}s of ${total}s).`);
 }
 encoder.stdin.end();
 const [code]=await finished;
 if(code!==0)throw Error(`FFmpeg exited with ${code}`);
 await context.close();
 await browser.close();
 fs.writeFileSync(path.join(out,'direct-render.json'),JSON.stringify({source:'Frame-accurate isolated HTML animation render',width:1920,height:1080,fps,frameCount:frames,duration:total,firstFrameTime:0,lastFrameTime:(frames-1)/fps,clock:'frame number / fps; narration starts at 0',cursor:false,desktop:false},null,2)+'\n');
 console.log('Frame-accurate render saved.');
})().catch(e=>{console.error(e);process.exit(1)});
