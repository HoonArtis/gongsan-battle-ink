# 공산 전투 927 · 수묵 3D 전투 시안

후백제 견훤의 공산 동수 전투(927)를 빌려 만든 수묵 톤 three.js 전투 장면과, 약 1분짜리 영화형 영상을 뽑는 제작 파이프라인. 내부 시연용 시안.

## 구성

| 경로 | 내용 |
|---|---|
| `ink_game_preview/index.html` | 먹빛 대문 — 생성형 환경 시안을 옮긴 3D 산책 장면 |
| `ink_game_preview/battle.html` | 공산 전투 — 1,000 대 1,000 자동 관전, 견훤 선봉·먹의 호흡 6형·화살 피하기·승전 |
| `ink_game_preview/battle_v1.html` | 초기 대군전 판(2,000 대 2,000, 절차 모델) |
| `ink_game_preview/assets/` | TripoSG 복원 GLB 17종, 효과음 MP3 24종, KCISA 모션 리타깃 JSON, 썸네일 |
| `pipeline/` | 에셋·모션·효과음·녹화 스크립트 |
| `share/index.html` | 완성 영상 공유 페이지 |

## 보기

정적 파일이라 아무 HTTP 서버로 연다. 저장소 루트에서:

```
python -m http.server 8765
```

- `http://127.0.0.1:8765/ink_game_preview/battle.html?cinema=1` — 영화 모드 미리보기. 레터박스, 자막, 효과음, 하단 타임라인(클릭 이동, Space 일시정지, ←/→ 5초, [ ] 배속). 화면을 한 번 클릭해야 소리가 켜짐.
- `?record=1` — 녹화 모드. `window.recStep(dt)`로만 진행(녹화 스크립트 전용).
- 파라미터 없이 열면 자동 관전(V 카메라 고정, G 자동 카메라, R 처음부터, 1/2/3 먹 농도).

## 파이프라인

1. `gen_images.sh` + `prompts.tsv` — Codex CLI로 흰 배경 참조 이미지 생성
2. `reconstruct_all.py` — WSL의 로컬 TripoSG로 이미지 → 3D (에셋당 20~30초)
3. `decimate_export.py` — Blender 배치: 감면(대량 병사는 복셀 재메시 후 800면 안팎), 방향 정렬, 바닥 원점, 웹용 GLB
4. `ue_export_anims.py` → `sample_kcisa.py` — UE 5.7 커맨드릿으로 KCISA 무예 애니메이션 FBX 반출 → Blender에서 30fps 샘플링해 웹 리그(13본) 방향 데이터로 리타깃
5. `gen_battle_sfx.py` — Stable Audio Open으로 효과음 생성
6. `record_battle.py` — 헤드리스 크롬(D3D11 GPU)을 CDP로 몰아 프레임 단위 녹화 → `mix_audio.py`가 사건 시각(events.json)에 맞춰 효과음 배치 → ffmpeg로 그레인·비네팅·합성
7. `share_server.py` — 공유 폴더 하나만 서비스하는 Range 지원 서버(외부 공개는 cloudflared 임시 터널)

`cdp_probe.py`, `views.py`, `inspect_fbx.py`는 진단용.

스크립트 안의 절대 경로(`C:\Users\hunvr\...`, WSL `/mnt/c/...`)는 제작 PC 기준.

## 라이선스·주의

- **TripoSG 복원 에셋**: 로컬 설치본의 의존 패키지(diso)가 CC BY-NC 4.0 — 내부 시연 한정, 상업 사용 불가.
- **무예 모션**: KCISA 「한국 전통 무예」(Fab, CC BY 4.0). 사용 시 출처 표기 필수. 원본 에셋은 포함하지 않고 리타깃한 방향 데이터(`kcisa_clips.json`)만 포함.
- **효과음**: Stable Audio Open 1.0 생성물(Stability AI Community License).
- 먹의 호흡 기술명과 형태는 자체 창작. 실제 영화·애니 영상은 사용하지 않음.
- 역사를 빌린 게임용 재구성 — 인물·전황은 사실과 다름.
