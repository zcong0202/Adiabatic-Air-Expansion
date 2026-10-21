import AppKit
import WebKit
import Darwin

final class USBSerial {
    private var fd: Int32 = -1
    private var timer: DispatchSourceTimer?
    var onBytes: ((Data) -> Void)?
    var onLost: ((String) -> Void)?
    func openPort(_ path: String) throws {
        closePort()
        let handle = Darwin.open(path, O_RDWR | O_NOCTTY | O_NONBLOCK)
        guard handle >= 0 else { throw error("Cannot open Arduino. Close other apps using it, then reconnect.") }
        fd = handle
        var options = termios()
        guard tcgetattr(fd, &options) == 0 else { closePort(); throw error("Cannot read Arduino USB settings.") }
        cfmakeraw(&options)
        options.c_cflag |= tcflag_t(CLOCAL | CREAD)
        cfsetispeed(&options, speed_t(B115200)); cfsetospeed(&options, speed_t(B115200))
        guard tcsetattr(fd, TCSANOW, &options) == 0 else { closePort(); throw error("Cannot set Arduino USB speed.") }
        tcflush(fd, TCIOFLUSH)
        guard ioctl(fd, UInt(TIOCEXCL)) == 0 else { closePort(); throw error("Arduino USB is busy. Close other serial apps.") }
        let source = DispatchSource.makeTimerSource(queue: .main)
        source.schedule(deadline: .now(), repeating: .milliseconds(5))
        source.setEventHandler { [weak self] in self?.readAvailable() }
        timer = source; source.resume()
    }
    func writeBytes(_ data: Data) throws {
        guard fd >= 0 else { throw error("Arduino is disconnected.") }
        try data.withUnsafeBytes { buffer in
            var offset = 0
            while offset < data.count {
                let count = Darwin.write(fd, buffer.baseAddress!.advanced(by: offset), data.count-offset)
                if count > 0 { offset += count }
                else if count < 0 && errno == EINTR { continue }
                else { throw error("Cannot send to Arduino. Reconnect its USB cable.") }
            }
        }
    }
    func signals(_ values: [String: Bool]) throws {
        guard fd >= 0 else { throw error("Arduino is disconnected.") }
        for (name, mask) in [("dataTerminalReady", TIOCM_DTR), ("requestToSend", TIOCM_RTS)] {
            if let enabled = values[name] {
                var bits = Int32(mask)
                guard ioctl(fd, UInt(enabled ? TIOCMBIS : TIOCMBIC), &bits) == 0 else { throw error("This USB adapter cannot reset the Arduino automatically. Use the Uno USB port.") }
            }
        }
    }
    private func readAvailable() {
        guard fd >= 0 else { return }
        var buffer = [UInt8](repeating: 0, count: 4096)
        for _ in 0..<16 {
            let count = Darwin.read(fd, &buffer, buffer.count)
            if count > 0 { onBytes?(Data(buffer.prefix(count))); continue }
            if count < 0 && errno == EINTR { continue }
            if count < 0 && errno != EAGAIN { closePort(); onLost?("Arduino USB disconnected. Reconnect the cable.") }
            break
        }
    }
    func closePort() {
        timer?.cancel(); timer = nil
        if fd >= 0 { Darwin.close(fd); fd = -1 }
    }
    private func error(_ message: String) -> NSError { NSError(domain: "AA.USB", code: 1, userInfo: [NSLocalizedDescriptionKey: message]) }
}

final class AppDelegate: NSObject, NSApplicationDelegate, WKScriptMessageHandler, WKNavigationDelegate, NSWindowDelegate {
    var window: NSWindow!
    var web: WKWebView!
    let serial = USBSerial()
    var selectedPort: String?
    func applicationDidFinishLaunching(_ notification: Notification) {
        let menu = NSMenu(); let appItem = NSMenuItem(); menu.addItem(appItem)
        let appMenu = NSMenu(); appMenu.addItem(withTitle: "Quit AA Controller", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"); appItem.submenu=appMenu
        let edit = NSMenuItem(); menu.addItem(edit); let editMenu=NSMenu(title:"Edit");edit.submenu=editMenu
        for (name,action,key) in [("Copy","copy:","c"),("Paste","paste:","v"),("Select All","selectAll:","a")] { editMenu.addItem(withTitle:name,action:Selector(action),keyEquivalent:key) }
        NSApp.mainMenu = menu
        let config = WKWebViewConfiguration()
        let controller = WKUserContentController(); controller.add(self, name:"aa")
        let resources=Bundle.main.resourceURL!
        let bridge=try! String(contentsOf: resources.appendingPathComponent("bridge.js"),encoding:.utf8)
        controller.addUserScript(WKUserScript(source:bridge,injectionTime:.atDocumentStart,forMainFrameOnly:true)); config.userContentController=controller
        web=WKWebView(frame:.zero,configuration:config);web.navigationDelegate=self
        window=NSWindow(contentRect:NSRect(x:0,y:0,width:1100,height:820),styleMask:[.titled,.closable,.miniaturizable,.resizable],backing:.buffered,defer:false)
        window.title="AA Controller";window.minSize=NSSize(width:820,height:680);window.contentView=web;window.delegate=self;window.center();window.makeKeyAndOrderFront(nil)
        serial.onBytes={ [weak self] data in self?.web.evaluateJavaScript("window.__aaBytes(\"\(data.base64EncodedString())\")",completionHandler:nil) }
        serial.onLost={ [weak self] message in self?.evaluate("window.__aaLost",[message]) }
        web.loadFileURL(resources.appendingPathComponent("index.html"),allowingReadAccessTo:resources)
        NSApp.activate(ignoringOtherApps:true)
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        if window?.title.contains("Updating") == true { showUpdateNotice();return .terminateCancel }
        return .terminateNow
    }
    func applicationWillTerminate(_ notification: Notification) { serial.closePort() }
    func windowShouldClose(_ sender: NSWindow) -> Bool {
        // Do not interrupt a firmware write without an explicit choice.
        if sender.title.contains("Updating") {
            showUpdateNotice();return false
        }
        return true
    }
    func showUpdateNotice() {
        guard window.attachedSheet == nil else { return }
        let alert=NSAlert();alert.messageText="Arduino is updating";alert.informativeText="Keep the app open and USB connected until the update finishes.";alert.addButton(withTitle:"Keep open")
        alert.beginSheetModal(for:window,completionHandler:nil)
    }
    func evaluate(_ function: String,_ values: [Any]) {
        guard let data=try? JSONSerialization.data(withJSONObject:values),let json=String(data:data,encoding:.utf8) else { return }
        web.evaluateJavaScript("\(function)(...\(json))",completionHandler:nil)
    }
    func reply(_ id: Int,_ value: Any=NSNull(),_ error: String?=nil) { evaluate("window.__aaReply",[id,value,error as Any? ?? NSNull()]) }
    func userContentController(_ userContentController: WKUserContentController,didReceive message: WKScriptMessage) {
        guard message.frameInfo.isMainFrame,let args=message.body as? [String:Any],let id=args["id"] as? Int,let action=args["action"] as? String else { return }
        do {
            switch action {
            case "choose":
                let ports=(try FileManager.default.contentsOfDirectory(atPath:"/dev")).filter { $0.hasPrefix("cu.usbmodem") || $0.hasPrefix("cu.usbserial") || $0.hasPrefix("cu.wchusbserial") || $0.hasPrefix("cu.SLAB_USBtoUART") }.sorted().map { "/dev/"+$0 }
                guard !ports.isEmpty else { throw NSError(domain:"AA",code:1,userInfo:[NSLocalizedDescriptionKey:"No Arduino found. Plug it in with the USB data cable, then click Connect Arduino."]) }
                if ports.count==1 { selectedPort=ports[0] }
                else {
                    let alert=NSAlert();alert.messageText="Choose the Arduino";alert.informativeText="Several USB devices are connected. Choose the Uno USB connection.";alert.addButton(withTitle:"Connect");alert.addButton(withTitle:"Cancel")
                    let picker=NSPopUpButton(frame:NSRect(x:0,y:0,width:320,height:28));picker.addItems(withTitles:ports);alert.accessoryView=picker
                    guard alert.runModal() == .alertFirstButtonReturn else { reply(id,NSNull(),"Connection cancelled.");return };selectedPort=picker.titleOfSelectedItem
                }
                reply(id)
            case "open":
                guard let path=selectedPort else { reply(id,NSNull(),"Connect the Arduino first.");return };try serial.openPort(path);reply(id)
            case "close":serial.closePort();reply(id)
            case "write":guard let encoded=args["base64"] as? String,let data=Data(base64Encoded:encoded),data.count<=65536 else { reply(id,NSNull(),"Invalid USB data.");return };try serial.writeBytes(data);reply(id)
            case "signals":try serial.signals(args["signals"] as? [String:Bool] ?? [:]);reply(id)
            case "save":
                guard let name=args["name"] as? String,let encoded=args["base64"] as? String,let data=Data(base64Encoded:encoded),data.count<10_000_000 else { reply(id,NSNull(),"Cannot save this file.");return }
                let panel=NSSavePanel();panel.nameFieldStringValue=URL(fileURLWithPath:name).lastPathComponent;panel.directoryURL=FileManager.default.urls(for:.downloadsDirectory,in:.userDomainMask).first;panel.canCreateDirectories=true
                panel.beginSheetModal(for:window) { response in
                    if response == .OK,let url=panel.url { do { try data.write(to:url,options:.atomic);self.reply(id,true) } catch { self.reply(id,NSNull(),error.localizedDescription) } } else { self.reply(id,false) }
                }
            case "title":window.title=(args["updating"] as? Bool ?? false) ? "AA Controller — Updating Arduino" : "AA Controller";reply(id)
            default:reply(id,NSNull(),"Unknown app action.")
            }
        } catch { reply(id,NSNull(),error.localizedDescription) }
    }
    func webView(_ webView: WKWebView,decidePolicyFor navigationAction: WKNavigationAction,decisionHandler:@escaping (WKNavigationActionPolicy)->Void) {
        if let url=navigationAction.request.url,url.scheme=="https" || url.scheme=="http" { NSWorkspace.shared.open(url);decisionHandler(.cancel) } else { decisionHandler(.allow) }
    }
    func webView(_ webView: WKWebView,didFinish navigation: WKNavigation!) {
        if CommandLine.arguments.contains("--smoke-test") {
            let check="await NativeAA.call('title',{updating:false});return JSON.stringify({title:document.title,bridge:!!window.NativeAA,usb:!!navigator.serial,signal:document.getElementById('signal').textContent,save:document.getElementById('apply').textContent,export:firmwareFiles(firmware())['Valve wiring.png'].length})"
            web.callAsyncJavaScript(check,arguments:[:],in:nil,in:.page) { result in
                let text: String
                switch result { case .success(let value): text=(value as? String) ?? "ERROR: unexpected result";case .failure(let error):text="ERROR: \(error.localizedDescription)" }
                try? text.write(toFile:"/tmp/aa-native-smoke.json",atomically:true,encoding:.utf8);NSApp.terminate(nil)
            }
        }
    }
}

// Developer transport check: real macOS termios + character-device I/O on a PTY.
if CommandLine.arguments.count==3 && CommandLine.arguments[1]=="--serial-test" {
    let serial=USBSerial();var done=false
    serial.onBytes={ data in if data==Data([0x14,0x10]) { done=true;serial.closePort() } }
    do { try serial.openPort(CommandLine.arguments[2]);try serial.writeBytes(Data([0x30,0x20]));let end=Date().addingTimeInterval(3);while !done && Date()<end { RunLoop.main.run(until:Date().addingTimeInterval(0.01)) };print(done ? "PASS native serial PTY" : "FAIL native serial PTY timeout");exit(done ? 0 : 1) } catch { print(error.localizedDescription);exit(1) }
}
let app=NSApplication.shared;let delegate=AppDelegate();app.delegate=delegate;app.setActivationPolicy(.regular);app.run()
