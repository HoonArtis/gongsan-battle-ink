# Blender 배치: KCISA 무예 모션캡처(FBX)를 30fps로 샘플링해, 웹 리그(13본)용 '뼈 방향' 데이터로 리타깃
# 출력 좌표계: +X 캐릭터 왼쪽, +Y 위, +Z 캐릭터 앞 (첫 프레임 골반 기준으로 고정)
import bpy, sys, json
from mathutils import Vector
from pathlib import Path
argv = sys.argv[sys.argv.index('--') + 1:]
src, out = Path(argv[0]), Path(argv[1])
CLIPS = {  # 웹 클립 이름: (FBX 이름, 무기 FBX 여부)
 'sp_idle': ('Jangchang_Idle1', True), 'sp_walk': ('Jangchang_Walk', True), 'sp_run': ('Jangchang_Run', True),
 'sp_attack1': ('Jangchang_Attack1', True), 'sp_attack2': ('Jangchang_Attack2', True), 'sp_die': ('Jangchang_Die', True), 'sp_damage': ('Jangchang_Damage', True),
 'wd_idle': ('Woldo_Idle1', True), 'wd_attack1': ('Woldo_Attack1', True), 'wd_attack2': ('Woldo_Attack2', True), 'wd_attack3': ('Woldo_Attack3', True), 'wd_attack4': ('Woldo_Attack4', True),
}
SEG = {  # 웹 뼈: (시작 관절, 끝 관절)
 'hips': ('Root_M', 'Chest_M'), 'chest': ('Chest_M', 'Neck_M'), 'head': ('Neck_M', 'HeadEnd_M'),
 'rUp': ('Shoulder_R', 'Elbow_R'), 'rFo': ('Elbow_R', 'Wrist_R'), 'rHand': ('Wrist_R', 'MiddleFinger1_R'),
 'lUp': ('Shoulder_L', 'Elbow_L'), 'lFo': ('Elbow_L', 'Wrist_L'), 'lHand': ('Wrist_L', 'MiddleFinger1_L'),
 'rTh': ('Hip_R', 'Knee_R'), 'rSh': ('Knee_R', 'Ankle_R'), 'lTh': ('Hip_L', 'Knee_L'), 'lSh': ('Knee_L', 'Ankle_L'),
}
def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path), automatic_bone_orientation=False)
    arm = [o for o in bpy.data.objects if o not in before and o.type == 'ARMATURE'][0]
    return arm
def jpos(arm, name):
    if name not in arm.pose.bones: return arm.matrix_world.translation.copy()  # Root_M = 아마추어 오브젝트 자신
    pb = arm.pose.bones[name]; return arm.matrix_world @ pb.head
result = {'fps': 30, 'source': 'KCISA Korean Traditional Martial Arts (CC BY 4.0)', 'clips': {}}
stand = None
for key, (fbx, has_w) in CLIPS.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    arm = load(src/f'{fbx}.fbx'); warm = load(src/f'{fbx}_Weapon.fbx') if has_w and (src/f'{fbx}_Weapon.fbx').exists() else None
    act = arm.animation_data.action; f0, f1 = act.frame_range; sc = bpy.context.scene
    fps = sc.render.fps if sc.render.fps else 60
    step = fps/30.0
    frames = []; f = f0
    sc.frame_set(int(f0))
    L = jpos(arm, 'Hip_L') - jpos(arm, 'Hip_R'); L.z = 0; L.normalize(); U = Vector((0, 0, 1)); F = L.cross(U)
    toOur = lambda v: [round(v.dot(L), 4), round(v.dot(U), 4), round(v.dot(F), 4)]
    root0 = jpos(arm, 'Root_M')
    if stand is None:
        stand = {'root': root0.z, 'height': jpos(arm, 'HeadEnd_M').z}
    H = stand['height']
    gap = []
    while f <= f1 + 1e-6:
        fi = int(f); sub = f - fi; sc.frame_set(fi, subframe=sub)
        d = {}
        for b, (a, c) in SEG.items():
            v = jpos(arm, c) - jpos(arm, a); v.normalize(); d[b] = toOur(v)
        r = jpos(arm, 'Root_M') - root0
        fr = {'d': d, 'root': [round(r.dot(L)/H, 4), round((jpos(arm, 'Root_M').z - stand['root'])/H, 4), round(r.dot(F)/H, 4)]}
        if warm:
            w2, w5 = jpos(warm, 'weaponjoint2'), jpos(warm, 'weaponjoint5'); wv = (w5 - w2); wl = wv.length; wv.normalize()
            fr['w'] = toOur(wv); gap.append(min((jpos(arm, 'Wrist_R') - w2).length, (jpos(arm, 'Wrist_R') - w5).length, (jpos(arm, 'Wrist_L') - w2).length))
        frames.append(fr); f += step
    result['clips'][key] = {'src': fbx, 'dur': round(len(frames)/30, 3), 'frames': frames}
    print('SAMPLED', key, len(frames), 'hand-weapon gap(m) min/max', round(min(gap), 3) if gap else None, round(max(gap), 3) if gap else None, flush=True)
# 무기 방향 부호: 대기 첫 프레임에서 날(끝)이 위쪽을 향하도록
for pre in ('sp_', 'wd_'):
    w = result['clips'][pre + 'idle']['frames'][0].get('w')
    sgn = 1 if (w and w[1] >= 0) else -1
    for k, c in result['clips'].items():
        if k.startswith(pre):
            for fr in c['frames']:
                if 'w' in fr: fr['w'] = [x*sgn for x in fr['w']]
    print('WEAPON SIGN', pre, sgn, w)
out.write_text(json.dumps(result, separators=(',', ':')))
print('WROTE', out, out.stat().st_size)
