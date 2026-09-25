# 공산 전투 자동 관전을 프레임 단위로 녹화해 MP4로 만든다.
# 페이지(?record=1)는 requestAnimationFrame을 쓰지 않고 window.recStep(dt)로만 진행한다.
# 실행: python record_battle.py <url> <out.mp4> [fps] [max_seconds] [width] [height]
import sys, json, time, base64, subprocess, urllib.request, shutil
from pathlib import Path
import websocket

url, out = sys.argv[1], Path(sys.argv[2]).resolve()
FPS = int(sys.argv[3]) if len(sys.argv) > 3 else 30
MAXS = float(sys.argv[4]) if len(sys.argv) > 4 else 150
args = [a for a in sys.argv if not a.startswith('--')]
W = int(args[5]) if len(args) > 5 else 1920
H = int(args[6]) if len(args) > 6 else 1080
frames = out.parent/(out.stem + '_frames'); shutil.rmtree(frames, ignore_errors=True); frames.mkdir(parents=True)
prof = (out.parent/'chrome_rec_profile').resolve()
chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
proc = subprocess.Popen([chrome, '--headless=new', '--remote-debugging-port=9333', f'--window-size={W},{H}', f'--user-data-dir={prof}',
                         '--remote-allow-origins=*', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader', '--hide-scrollbars', 'about:blank'] + (['--use-angle=d3d11', '--enable-gpu'] if '--gpu' in sys.argv else []),
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    tabs = None
    for _ in range(120):
        try: tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9333/json')); break
        except Exception: time.sleep(.5)
    page = [t for t in tabs if t['type'] == 'page'][0]
    ws = websocket.create_connection(page['webSocketDebuggerUrl'], max_size=None, timeout=600, suppress_origin=True)
    mid = [0]
    def call(method, **params):
        mid[0] += 1; ws.send(json.dumps({'id': mid[0], 'method': method, 'params': params}))
        while True:
            m = json.loads(ws.recv())
            if m.get('id') == mid[0]:
                if 'error' in m: raise RuntimeError(f'{method}: {m["error"]}')
                return m.get('result', {})
    def ev(expr):
        r = call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if 'exceptionDetails' in r: raise RuntimeError(json.dumps(r['exceptionDetails'])[:600])
        return r['result'].get('value')
    call('Page.enable'); call('Runtime.enable')
    call('Emulation.setDeviceMetricsOverride', width=W, height=H, deviceScaleFactor=1, mobile=False)
    call('Page.navigate', url=url)
    for _ in range(240):
        try:
            if ev('typeof window.recStep === "function"'): break
        except Exception: pass
        time.sleep(.5)
    else: raise RuntimeError('recStep not ready')
    print('GPU', ev('(()=>{const g=document.createElement("canvas").getContext("webgl2");const d=g.getExtension("WEBGL_debug_renderer_info");return d?g.getParameter(d.UNMASKED_RENDERER_WEBGL):"?"})()'), flush=True)
    dt = 1/FPS; n = int(MAXS*FPS); t0 = time.time(); end_after = None
    for f in range(n):
        ev(f'window.recStep({dt})')
        shot = call('Page.captureScreenshot', format='jpeg', quality=92, captureBeyondViewport=False)
        (frames/f'{f:05d}.jpg').write_bytes(base64.b64decode(shot['data']))
        if f % FPS == 0:
            st = ev('JSON.stringify({w:game.battle().winner, a:game.alive, t:+game.battle().t.toFixed(1), k:game.hero().kills})')
            print(f'frame {f} ({f/FPS:.0f}s) {st} {(time.time()-t0)/(f+1):.2f}s/frame', flush=True)
            if end_after is None and json.loads(st)['w'] >= 0: end_after = f + 10*FPS
        if end_after is not None and f >= end_after: break
    events = ev('JSON.stringify(game.events)')
    (out.parent/(out.stem + '.events.json')).write_text(events, encoding='utf-8')
    total_s = (f + 1)/FPS
    ws.close()
finally:
    proc.terminate()
silent = out.parent/(out.stem + '_silent.mp4')
# 필름 느낌: 약한 그레인 + 비네팅
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(frames/'%05d.jpg'), '-vf', 'noise=alls=3:allf=t,vignette=PI/6',
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-pix_fmt', 'yuv420p', str(silent)], check=True)
wav = out.parent/(out.stem + '.wav')
subprocess.run([r'C:\audio-tools\stable-audio\.venv\Scripts\python.exe', str(Path(__file__).resolve().parent/'mix_audio.py'),
                str(out.parent/(out.stem + '.events.json')), f'{total_s:.3f}', str(wav)], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(silent), '-i', str(wav), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest',
                '-movflags', '+faststart', str(out)], check=True)
print('WROTE', out, out.stat().st_size, flush=True)
