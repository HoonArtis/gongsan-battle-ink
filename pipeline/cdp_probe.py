# 헤드리스 크롬으로 페이지를 열고 콘솔·예외·지정 식을 주기적으로 찍는 진단 도구
import sys, json, time, subprocess, urllib.request, threading
from pathlib import Path
import websocket
url = sys.argv[1]; exprs = sys.argv[2:] or ['document.getElementById("loading")?.textContent']
prof = Path(__file__).resolve().parent.parent/'07_video'/'probe_profile'
proc = subprocess.Popen([r'C:\Program Files\Google\Chrome\Application\chrome.exe', '--headless=new', '--remote-debugging-port=9335', '--remote-allow-origins=*',
                         f'--user-data-dir={prof}', '--window-size=1280,720', '--enable-unsafe-swiftshader', 'about:blank'] + (['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'] if __import__('os').environ.get('GPU') else []), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    tabs = None
    for _ in range(120):
        try: tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9335/json')); break
        except Exception: time.sleep(.5)
    ws = websocket.create_connection([t for t in tabs if t['type'] == 'page'][0]['webSocketDebuggerUrl'], max_size=None, timeout=5, suppress_origin=True)
    ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'})); ws.send(json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': url}}))
    ws.send(json.dumps({'id': 3, 'method': 'Debugger.enable'}))
    t0 = time.time(); nid = 10; pending = {}; paused = False
    while time.time() - t0 < float(__import__('os').environ.get('PROBE_SECS', '90')):
        try: m = json.loads(ws.recv())
        except websocket.WebSocketTimeoutException:
            if not paused and time.time() - t0 > float(__import__('os').environ.get('PAUSE_AT', '1e9')):
                paused = True; ws.send(json.dumps({'id': 5, 'method': 'Debugger.pause'})); continue
            for e in exprs:
                nid += 1; pending[nid] = e; ws.send(json.dumps({'id': nid, 'method': 'Runtime.evaluate', 'params': {'expression': e, 'returnByValue': True, 'awaitPromise': True, 'timeout': 8000}}))
            continue
        if m.get('method') == 'Runtime.consoleAPICalled':
            print(f'[{time.time()-t0:5.1f}] console.{m["params"]["type"]}:', ' '.join(str(a.get('value', a.get('description', ''))) for a in m['params']['args'])[:300], flush=True)
        elif m.get('method') == 'Runtime.exceptionThrown':
            d = m['params']['exceptionDetails']; print(f'[{time.time()-t0:5.1f}] EXCEPTION:', (d.get('exception', {}).get('description') or d.get('text'))[:600], flush=True)
        elif m.get('method') == 'Debugger.paused':
            for cf in m['params']['callFrames'][:8]: print('  at', cf['functionName'] or '(anon)', 'line', cf['location']['lineNumber'] + 1, flush=True)
            break
        elif m.get('id') in pending:
            r = m.get('result', {}); print(f'[{time.time()-t0:5.1f}] {pending.pop(m["id"])[:50]} =>', json.dumps(r.get('result', {}).get('value', r))[:300], flush=True)
finally:
    proc.terminate()
