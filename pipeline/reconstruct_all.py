import os, sys, json, time
from pathlib import Path
os.environ['HF_HUB_OFFLINE'] = '1'; os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
repo = Path('/mnt/c/Users/hunvr/Downloads/TripoSG'); sys.path.insert(0, str(repo))
import torch
from PIL import Image
import triposg.pipelines.pipeline_triposg as pm

# 01_gpt_images의 PNG를 도착하는 대로 TripoSG로 복원한다. 모든 이름이 끝나면 종료.
root = Path('/mnt/c/Users/hunvr/Desktop/GyeonHwon_Onboarding/production_v10')
names = ['SPEARMAN'] + [l.split('\t')[0] for l in (root/'scripts/prompts.tsv').read_text(encoding='utf-8').splitlines() if l.strip()]
out = root/'02_raw3d'; out.mkdir(exist_ok=True)
pipe = pm.TripoSGPipeline.from_pretrained(str(repo/'pretrained_weights/TripoSG'), torch_dtype=torch.float16, local_files_only=True)
pipe.model_cpu_offload_seq = 'image_encoder_dinov2->transformer->vae'; pipe.enable_model_cpu_offload(); original = pm.flash_extract_geometry
def decode(latents, vae, **kwargs):
    if hasattr(vae, '_hf_hook'): vae._hf_hook.pre_forward(vae)
    return original(latents, vae, **kwargs)
pm.flash_extract_geometry = decode
report_path = out/'report.json'
reports = json.loads(report_path.read_text()) if report_path.exists() else []
deadline = time.time() + 3*3600
while time.time() < deadline:
    todo = [n for n in names if not (out/f'{n}.glb').exists()]
    if not todo: break
    ready = [n for n in todo if (root/'01_gpt_images'/f'{n}.png').exists() and time.time() - (root/'01_gpt_images'/f'{n}.png').stat().st_mtime > 5]
    if not ready: time.sleep(10); continue
    name = ready[0]; start = time.time(); print('RECONSTRUCT', name, flush=True)
    try:
        im = Image.open(root/'01_gpt_images'/f'{name}.png').convert('RGB')
        with torch.inference_mode():
            r = pipe(image=im, generator=torch.Generator('cuda').manual_seed(1000 + names.index(name)), num_inference_steps=40, flash_octree_depth=8)
        mesh = r.meshes[0]; mesh.export(str(out/f'{name}.glb'))
        reports.append({'name': name, 'vertices': len(mesh.vertices), 'triangles': len(mesh.faces), 'bounds': mesh.bounds.tolist(), 'seconds': round(time.time() - start, 1)})
        print('DONE', reports[-1], flush=True)
    except Exception as e:
        print('FAIL', name, repr(e), flush=True); (out/f'{name}.failed').write_text(repr(e)); names.remove(name)
    report_path.write_text(json.dumps(reports, indent=2))
    torch.cuda.empty_cache()
print('ALL DONE', flush=True)
