#!/usr/bin/env bash
# Codex 이미지 생성: prompts.tsv 한 줄 = 에셋 하나. 4개씩 병렬.
cd "$(dirname "$0")/.."
gen(){
 name="$1"; desc="$2"
 [ -s "01_gpt_images/$name.png" ] && { echo "SKIP $name"; return; }
 timeout 900 codex exec --skip-git-repo-check -s workspace-write "Generate ONE image with your image generation tool, then copy the generated PNG file to ./01_gpt_images/$name.png (create nothing else). Image: $desc. Plain pure white background, soft even studio lighting, no cast shadow on the ground, no ground plane, no text, clean silhouette, realistic 3D miniature style suitable for image-to-3D reconstruction." > "logs/gen_$name.log" 2>&1
 [ -s "01_gpt_images/$name.png" ] && echo "OK $name" || echo "FAIL $name"
}
export -f gen
mkdir -p logs 01_gpt_images
while IFS=$'\t' read -r n d; do printf '%s\0%s\0' "$n" "$d"; done < scripts/prompts.tsv | xargs -0 -n 2 -P 4 bash -c 'gen "$0" "$1"'
