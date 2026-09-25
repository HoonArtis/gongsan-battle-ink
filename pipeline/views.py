# Blender 배치: 웹용 GLB를 정면(+Z에서 바라봄)·측면(+X)·위에서 실루엣 투영해 PNG로 저장 — 방향 판정용
import bpy, sys, numpy as np
from pathlib import Path
argv = sys.argv[sys.argv.index('--') + 1:]
src, dst = Path(argv[0]), Path(argv[1]); dst.mkdir(parents=True, exist_ok=True)
for name in argv[2:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(src/f'{name}.glb'))
    ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
    v = np.array([ob.matrix_world @ p.co for p in ob.data.vertices])
    # 블렌더(Z 위) → glTF(Y 위): gx = x, gy = z, gz = -y
    g = np.stack([v[:, 0], v[:, 2], -v[:, 1]], 1)
    S = 300; img = np.full((S, S*3, 3), 255, np.uint8)
    lo, hi = g.min(0), g.max(0); sc = (S - 20)/max(hi - lo)
    for k, (a, b, depth) in enumerate([(0, 1, 2), (2, 1, 0), (0, 2, 1)]):
        # 정면: x→오른쪽, y→위, 깊이 +z가 앞(가까움) / 측면: z→오른쪽 / 위: x→오른쪽, z→아래
        u = ((g[:, a] - lo[a])*sc + 10).astype(int); w = ((hi[b] - g[:, b])*sc + 10).astype(int) if k < 2 else ((g[:, b] - lo[b])*sc + 10).astype(int)
        d = (g[:, depth] - lo[depth])/(hi[depth] - lo[depth] + 1e-9)
        order = np.argsort(d if k != 1 else d)
        for i in order:
            c = int(40 + 180*(1 - d[i]))
            img[np.clip(w[i], 0, S - 1), np.clip(u[i] + k*S, 0, S*3 - 1)] = (c, c, c)
    np.save(dst/f'{name}_views.npy', img)
    print('VIEW', name, lo.round(2).tolist(), hi.round(2).tolist(), flush=True)
