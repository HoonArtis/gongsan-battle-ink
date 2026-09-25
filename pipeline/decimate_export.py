# Blender 배치: TripoSG GLB → 감면(decimate) → 방향 정렬 → 바닥 원점 → 웹용 GLB
# 실행: blender -b --factory-startup --python decimate_export.py -- <in_dir> <out_dir>
import bpy, sys, json, math
import numpy as np
from pathlib import Path
from mathutils import Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
src, dst = Path(argv[0]), Path(argv[1]); dst.mkdir(parents=True, exist_ok=True)
# 이름: (목표 삼각형 수, 정렬 방식) — 'long': 긴 축을 앞(+Z), 머리 높은 쪽이 앞 / 'wide': 긴 축을 좌우(X) / None
SPEC = {
 'SPEARMAN': (900, None), 'ARCHER': (900, None), 'CAVALRY': (2400, 'long'), 'GYEONHWON': (40000, 'long'),
 'WALL_SEG': (5000, 'wide'), 'GATE_TOWER': (30000, 'wide'), 'BASTION': (12000, None), 'WATCHTOWER': (8000, None),
 'TENT': (5000, None), 'PALISADE': (2500, 'wide'), 'WAR_DRUM': (4000, None), 'CART': (5000, 'long'),
 'TREBUCHET': (9000, 'long'), 'CHEVAL': (2500, 'wide'),
 'A_FISSURED': (6000, None), 'B_LAYERED': (6000, None), 'C_RUBBLE': (6000, None),
}
report = {}
for glb in sorted(src.glob('*.glb')):
    name = glb.stem
    if name not in SPEC: continue
    target, align = SPEC[name]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in bpy.context.scene.objects: o.select_set(o in meshes)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # 파라미터 없는 분리 조각(부유물) 제거는 생략, 감면만
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    if target < 3000:
        # 저폴리 대량 인스턴스용: 복셀 재메시로 표면을 닫은 뒤 감면
        size = max(ob.dimensions)
        rm = ob.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = size/90
        bpy.ops.object.modifier_apply(modifier='rm')
    for _ in range(6):
        cur = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        if cur <= target*1.15: break
        mod = ob.modifiers.new('dec', 'DECIMATE'); mod.ratio = max(.05, min(1.0, target/cur)); mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier='dec')
    if sum(len(p.vertices) - 2 for p in ob.data.polygons) > target*1.5:
        # 붕괴 감면이 막히면(조각 경계) 평면 감면으로 한 번 더
        mod = ob.modifiers.new('dec2', 'DECIMATE'); mod.decimate_type = 'DISSOLVE'; mod.angle_limit = math.radians(12)
        bpy.ops.object.modifier_apply(modifier='dec2'); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
    me = ob.data
    v = np.array([ob.matrix_world @ p.co for p in me.vertices])
    # 블렌더 좌표: Z 위, 바닥 평면 XY. glTF +Z(앞) = 블렌더 -Y
    xy = v[:, :2] - v[:, :2].mean(0)
    ang = 0.0
    if align:
        w, vec = np.linalg.eigh(np.cov(xy.T)); major = vec[:, np.argmax(w)]
        theta = math.atan2(major[1], major[0])
        if align == 'long':
            ang = -math.pi/2 - theta          # 긴 축 → -Y
        else:
            ang = -theta                      # 긴 축 → X
    R = Matrix.Rotation(ang, 4, 'Z'); me.transform(R)
    v = np.array([p.co for p in me.vertices])
    if align == 'long':
        # 긴 축 양 끝 12% 구간 중 더 높이 솟은 쪽(말 머리)을 앞(-Y)으로
        lo_y, hi_y = np.percentile(v[:, 1], 12), np.percentile(v[:, 1], 88)
        if v[v[:, 1] > hi_y, 2].max() > v[v[:, 1] < lo_y, 2].max(): me.transform(Matrix.Rotation(math.pi, 4, 'Z')); v = np.array([p.co for p in me.vertices])
    lo, hi = v.min(0), v.max(0)
    me.transform(Matrix.Translation((-(lo[0] + hi[0])/2, -(lo[1] + hi[1])/2, -lo[2])))
    for p in me.polygons: p.use_smooth = target >= 9000
    me.materials.clear()
    bpy.ops.export_scene.gltf(filepath=str(dst/f'{name}.glb'), export_format='GLB', export_materials='NONE', export_texcoords=False,
                              export_normals=True, use_selection=False, export_yup=True)
    v = np.array([p.co for p in me.vertices])
    report[name] = {'tris_in': tris, 'tris_out': sum(len(p.vertices) - 2 for p in me.polygons),
                    'size_xyz_blender': (v.max(0) - v.min(0)).round(3).tolist()}
    print('EXPORTED', name, report[name], flush=True)
(dst/'assets.json').write_text(json.dumps(report, indent=2))
