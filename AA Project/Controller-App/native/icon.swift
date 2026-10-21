import AppKit
let directory=URL(fileURLWithPath:CommandLine.arguments[1]);try FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true)
for (points,scale) in [(16,1),(16,2),(32,1),(32,2),(128,1),(128,2),(256,1),(256,2),(512,1),(512,2)] {
    let size=points*scale
    let bitmap=NSBitmapImageRep(bitmapDataPlanes:nil,pixelsWide:size,pixelsHigh:size,bitsPerSample:8,samplesPerPixel:4,hasAlpha:true,isPlanar:false,colorSpaceName:.deviceRGB,bytesPerRow:0,bitsPerPixel:0)!
    NSGraphicsContext.saveGraphicsState();NSGraphicsContext.current=NSGraphicsContext(bitmapImageRep:bitmap)
    NSGraphicsContext.current!.cgContext.scaleBy(x:CGFloat(size)/1024,y:CGFloat(size)/1024)
    NSColor(calibratedRed:0.03,green:0.48,blue:0.38,alpha:1).setFill();NSBezierPath(roundedRect:NSRect(x:64,y:64,width:896,height:896),xRadius:196,yRadius:196).fill()
    let attrs:[NSAttributedString.Key:Any]=[.font:NSFont.boldSystemFont(ofSize:326),.foregroundColor:NSColor.white]
    let letters="AA" as NSString;let bounds=letters.size(withAttributes:attrs);letters.draw(at:NSPoint(x:(1024-bounds.width)/2,y:(1024-bounds.height)/2+16),withAttributes:attrs)
    NSColor(calibratedRed:0.6,green:0.95,blue:0.78,alpha:1).setFill();NSBezierPath(roundedRect:NSRect(x:288,y:223,width:448,height:32),xRadius:16,yRadius:16).fill()
    NSGraphicsContext.restoreGraphicsState()
    let name="icon_\(points)x\(points)\(scale==2 ? "@2x" : "").png"
    try bitmap.representation(using:.png,properties:[:])!.write(to:directory.appendingPathComponent(name))
}
