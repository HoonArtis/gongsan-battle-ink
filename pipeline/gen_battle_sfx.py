"""공산 전투 영상용 효과음 배치 생성 — Stable Audio Open 1.0 (로컬, C:\\audio-tools\\stable-audio)

    C:\\audio-tools\\stable-audio\\.venv\\Scripts\\python.exe gen_battle_sfx.py
"""
import sys, time
from pathlib import Path
import soundfile as sf
import torch
sys.path.insert(0, r"C:\audio-tools\stable-audio")
import webui  # load_pipe, SR 재사용

OUT = Path(r"C:\Users\hunvr\Desktop\GyeonHwon_Onboarding\production_v10\08_audio"); OUT.mkdir(exist_ok=True)
NEG = "music, melody, singing, modern, electronic, synth, beeps, speech, narration"
JOBS = [  # (이름, 프롬프트, 길이초, 개수, 시드)
 ("wind", "cold autumn wind over a wide mountain valley, grass rustling, calm and ominous, field recording", 30, 1, 101),
 ("drums", "slow powerful ancient war drums, deep booming big barrel drums beating in unison, army preparing for battle, cinematic, huge space", 30, 2, 201),
 ("horn", "ancient war horn blast, one long low horn call echoing across a battlefield valley", 8, 2, 301),
 ("arrows", "volley of hundreds of arrows whooshing overhead through the air then raining down with thuds", 10, 2, 401),
 ("charge", "cavalry charge, hundreds of horses galloping thunderously, men shouting war cries, rumbling ground", 20, 2, 501),
 ("clash", "close quarters ancient battle, swords and spears clashing, metal hits, shields, grunts and yells, chaotic", 20, 2, 601),
 ("bed", "huge ancient battlefield ambience, thousands of soldiers fighting in the distance, shouting, clashing weapons, horses neighing", 45, 2, 701),
 ("breath", "one long sharp deep inhale through clenched teeth, intense focused breathing before a strike, close microphone, dry", 4, 3, 901),
 ("slash", "single huge sword slash whoosh with a swirling rushing water and wind sweep, powerful, cinematic sound effect", 4, 3, 1001),
 ("impact", "massive deep cinematic impact boom with debris, low thud and rumble tail", 5, 2, 1101),
 ("cheer", "huge army victory cheer, thousands of soldiers shouting and roaring in triumph, raising weapons, crowd roar", 20, 3, 801),
]
pipe = webui.load_pipe()
torch.cuda.set_per_process_memory_fraction(0.9)  # load_pipe가 거는 45% 제한은 30초 이상 디코딩에서 OOM — 로딩 뒤에 푼다
try: pipe.vae.enable_slicing()
except Exception: pass
for name, prompt, secs, count, seed0 in JOBS:
    for i in range(count):
        if (OUT/f"{name}_{i}.wav").exists(): continue
        t0 = time.time(); g = torch.Generator("cuda"); g.manual_seed(seed0 + i)
        audio = pipe(prompt=prompt, negative_prompt=NEG, num_inference_steps=100, guidance_scale=7.0,
                     audio_end_in_s=float(secs), num_waveforms_per_prompt=1, generator=g).audios[0]
        wav = audio.T.float().cpu().numpy(); pk = abs(wav).max()
        if pk > 0: wav = wav/pk*0.708
        dst = OUT/f"{name}_{i}.wav"; sf.write(dst, wav, webui.SR)
        print(f"OK {dst.name} {time.time()-t0:.1f}s", flush=True); torch.cuda.empty_cache()
print("ALL DONE", flush=True)
