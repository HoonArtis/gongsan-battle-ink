# UE 5.7 헤드리스: KCISA 한국 전통 무예(CC BY 4.0) 병사 메시·애니메이션을 FBX로 반출
# 실행: UnrealEditor-Cmd.exe CharPt.uproject -run=pythonscript -script=<이 파일> -unattended -nosplash
import unreal, os
OUT = r'C:\Users\hunvr\Desktop\GyeonHwon_Onboarding\production_v10\06_kcisa_fbx'
os.makedirs(OUT, exist_ok=True)
BASE = '/Game/KoreanTraditionalMartialArts'
ANIMS = {
 'Jangchang': ['Idle1', 'Walk', 'Run', 'Attack1', 'Attack2', 'Damage', 'Die'],
 'Woldo': ['Idle1', 'Run', 'Attack1', 'Attack2', 'Attack3', 'Attack4', 'Defense'],
 'Deoungpae': ['Attack1', 'Defense', 'Die'],
}
def export(obj, path, anim):
    task = unreal.AssetExportTask()
    task.object = obj; task.filename = path; task.automated = True; task.replace_identical = True; task.prompt = False
    opt = unreal.FbxExportOption(); opt.ascii = False; opt.collision = False; opt.export_morph_targets = False
    opt.level_of_detail = False; opt.export_preview_mesh = False
    task.options = opt
    task.exporter = unreal.AnimSequenceExporterFBX() if anim else unreal.SkeletalMeshExporterFBX()
    ok = unreal.Exporter.run_asset_export_task(task)
    unreal.log_warning(f'EXPORT {"OK" if ok else "FAIL"} {path}')
# 스켈레탈 메시 반출은 커맨드릿에서 MeshObject 단정으로 죽어서 생략(애니 FBX에 뼈대 포함)

for style, names in ANIMS.items():
    for n in names:
        a = unreal.load_asset(f'{BASE}/Animations/{style}/Anim_{style}_{n}_Soldier')
        if a is None: unreal.log_warning(f'EXPORT MISSING {style} {n}'); continue
        unreal.log_warning(f'LEN {style}_{n} {a.get_play_length():.3f}')
        export(a, os.path.join(OUT, f'{style}_{n}.fbx'), True)
        if style in ('Jangchang', 'Woldo'):
            w = unreal.load_asset(f'{BASE}/Animations/{style}/Anim_{style}_{n}_Weapon')
            if w is not None: export(w, os.path.join(OUT, f'{style}_{n}_Weapon.fbx'), True)
