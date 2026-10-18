import Cocoa
import CoreGraphics
let a = CommandLine.arguments
let source = CGEventSource(stateID: .hidSystemState)
func move(_ x: Double,_ y: Double,_ d: Double) {
 let p = CGEvent(source: nil)!.location
 let n = max(1,Int(d*60))
 for i in 1...n {let t=Double(i)/Double(n); let e=t*t*(3-2*t); let q=CGPoint(x:p.x+(x-p.x)*e,y:p.y+(y-p.y)*e); CGEvent(mouseEventSource:source,mouseType:.mouseMoved,mouseCursorPosition:q,mouseButton:.left)!.post(tap:.cghidEventTap); usleep(UInt32(max(0,d/Double(n))*1_000_000))}
}
switch a[1] {
case "info":
 if let items=CGWindowListCopyWindowInfo(.optionOnScreenOnly,kCGNullWindowID) as? [[String:Any]] { for w in items where (w[kCGWindowNumber as String] as? Int)==13972 { print(w[kCGWindowBounds as String] ?? "no bounds") } }
case "move", "click":
 move(Double(a[2])!,Double(a[3])!,a.count>4 ? Double(a[4])! : 0.8)
 if a[1]=="click" {let p=CGPoint(x:Double(a[2])!,y:Double(a[3])!); CGEvent(mouseEventSource:source,mouseType:.leftMouseDown,mouseCursorPosition:p,mouseButton:.left)!.post(tap:.cghidEventTap); usleep(90000); CGEvent(mouseEventSource:source,mouseType:.leftMouseUp,mouseCursorPosition:p,mouseButton:.left)!.post(tap:.cghidEventTap)}
case "drag":
 let sx=Double(a[2])!, sy=Double(a[3])!, ex=Double(a[4])!, ey=Double(a[5])!
 move(sx,sy,0.3)
 CGEvent(mouseEventSource:source,mouseType:.leftMouseDown,mouseCursorPosition:CGPoint(x:sx,y:sy),mouseButton:.left)!.post(tap:.cghidEventTap)
 usleep(150000)
 for i in 1...60 { let t=Double(i)/60.0; let p=CGPoint(x:sx+(ex-sx)*t,y:sy+(ey-sy)*t); CGEvent(mouseEventSource:source,mouseType:.leftMouseDragged,mouseCursorPosition:p,mouseButton:.left)!.post(tap:.cghidEventTap);usleep(16667) }
 CGEvent(mouseEventSource:source,mouseType:.leftMouseUp,mouseCursorPosition:CGPoint(x:ex,y:ey),mouseButton:.left)!.post(tap:.cghidEventTap)
case "scroll":
 let delta=Int32(a[2])!; let n=max(1,abs(delta)/12)
 for _ in 0..<n {CGEvent(scrollWheelEvent2Source:source,units:.pixel,wheelCount:1,wheel1:delta/Int32(n),wheel2:0,wheel3:0)!.post(tap:.cghidEventTap);usleep(20000)}
default: break
}
