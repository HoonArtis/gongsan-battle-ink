"""녹화 때 기록된 사건 시각(events.json)에 맞춰 효과음을 배치해 한 트랙으로 섞는다.
    <stable-audio venv python> mix_audio.py <events.json> <duration_s> <out.wav>
"""
import sys, json
from pathlib import Path
import numpy as np, soundfile as sf

ev = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')); D = float(sys.argv[2]); out = Path(sys.argv[3])
SFX = Path(__file__).resolve().parent.parent/'08_audio'; SR = 44100
mix = np.zeros((int(D*SR) + SR, 2), np.float32)
def load(n):
    p = SFX/f'{n}.wav'
    if not p.exists(): return None
    a, sr = sf.read(p, dtype='float32', always_2d=True); assert sr == SR
    return a if a.shape[1] == 2 else np.repeat(a, 2, 1)
def place(name, t, gain=1.0, until=None, fade_in=.05, fade_out=.8, loop=False):
    a = load(name)
    if a is None or t >= D: return
    s0 = int(max(0, t)*SR); end = int(min(D, until)*SR) if until else s0 + len(a)
    n = end - s0
    if n <= 0: return
    if loop and n > len(a):
        xf = int(.5*SR); seg = a.copy(); buf = seg
        while len(buf) < n:  # 이어붙일 때 0.5초 교차
            r = np.linspace(0, 1, xf)[:, None]; buf = np.concatenate([buf[:-xf], buf[-xf:]*(1 - r) + seg[:xf]*r, seg[xf:]])
        a = buf
    a = a[:n].copy()
    fi, fo = int(fade_in*SR), int(fade_out*SR)
    if fi: a[:fi] *= np.linspace(0, 1, min(fi, len(a)))[:, None][:len(a[:fi])]
    if fo and len(a) > fo: a[-fo:] *= np.linspace(1, 0, fo)[:, None]
    a = a[:max(0, len(mix) - s0)]
    mix[s0:s0 + len(a)] += a*gain
T = {}
for e in ev: T.setdefault(e['type'], []).append(e['t'])
first = lambda k, d=None: T.get(k, [d])[0]
start, charge, rout, vic = first('battle_start', 9), first('charge', 25), first('rout'), first('victory')
end_battle = vic if vic is not None else D
place('wind_0', 0, .75, until=start + 4, fade_in=1.5, fade_out=3, loop=True)
place('drums_0', 1.5, .95, until=charge + 1.5, fade_in=1, fade_out=2.5, loop=True)
place('horn_0', start, .9); place('horn_1', charge - 1.2, .85)
last = -99; k = 0
for t in sorted(T.get('volley0', []) + T.get('volley1', [])):
    if t - last > 3.5: place(f'arrows_{k % 2}', t, .5); last = t; k += 1
for t in T.get('vanguard', []): place('charge_0', t, .8, fade_out=2)
place('charge_1', charge, .95, fade_out=3)
place('bed_0', charge, .5, until=end_battle + 3, fade_in=1.5, fade_out=3, loop=True)
place('clash_0', charge + 1, .55, until=(rout or end_battle) + 3, fade_in=1, fade_out=3, loop=True)
place('clash_1', charge + 6, .35, until=(rout or end_battle), fade_in=2, fade_out=3, loop=True)
for i, t in enumerate(T.get('breath', [])): place(f'breath_{i % 3}', t, 1.1, fade_out=.3)
for i, t in enumerate(T.get('breath_hit', [])): place(f'slash_{i % 3}', t - .12, 1.0); place(f'impact_{i % 2}', t, .8)
for t in T.get('general_dead', []): place('impact_1', t, 1.0)
last = -9
for k, t in enumerate(T.get('hslash', [])):
    if t - last > .4: place(f'slash_{k % 3}', t, .4, fade_out=.2); last = t
for t in T.get('dodge', []): place('arrows_1', t + .3, .95); place('breath_1', t + .75, .9, fade_out=.3); place('slash_2', t + 1.1, .6)
if vic is not None:
    place('cheer_0', vic + .2, 1.0, fade_out=2); place('cheer_1', vic + 1.4, .85, fade_out=2.5); place('cheer_2', vic + 5, .7, fade_out=4)
    place('drums_1', vic + 3, .6, fade_in=2, fade_out=4)
# 전체 레벨: 피크 -1dBFS 근처로, 부드러운 소프트 클립
mix = mix[:int(D*SR)]
pk = np.abs(mix).max() or 1; mix = np.tanh(mix/pk*1.6)/np.tanh(1.6)*.89
sf.write(out, mix, SR); print('WROTE', out, f'{D:.1f}s', 'events', {k: len(v) for k, v in T.items()})
