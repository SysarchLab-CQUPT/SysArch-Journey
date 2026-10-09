#!/usr/bin/env bash
# 构建脚本（macOS / Linux）。
#
#   scripts/build.sh                                      构建全书 → build/main.pdf
#   scripts/build.sh chapters/03-riscv-isa/chapter.tex     只编译单章（预览用）
#
# 产物统一写在 build/ 下，仓库其它位置不会出现编译文件。
# 需要 TeX Live（xelatex，建议同时安装 latexmk）。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TARGET="${1:-main.tex}"

if ! command -v xelatex >/dev/null 2>&1; then
  echo "未找到 xelatex，请先安装 TeX Live。" >&2
  exit 1
fi

HAS_LATEXMK=0
command -v latexmk >/dev/null 2>&1 && HAS_LATEXMK=1

compile() {
  # 在 $1 目录内编译 $2，输出到 $3
  local workdir="$1" file="$2" outdir="$3"
  mkdir -p "$outdir"
  if [ "$HAS_LATEXMK" = "1" ]; then
    ( cd "$workdir" && latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir="$outdir" "$file" )
  else
    echo "未找到 latexmk，改用 xelatex 直接编译（需要多跑几遍）。" >&2
    ( cd "$workdir" && for pass in 1 2 3; do
        xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory="$outdir" "$file"
      done )
  fi
}

if [ "$TARGET" = "main.tex" ]; then
  # 章的清单和各表单的章节下拉都是派生产物，编译前重新生成一次，
  # 免得加了章却忘了跑脚本。
  if command -v python3 >/dev/null 2>&1; then
    python3 "$ROOT/scripts/update-manifest.py"
    python3 "$ROOT/scripts/update-modules.py"
  else
    echo "未找到 python3，跳过章节清单与表单的同步。" >&2
  fi
  compile "$ROOT" "main.tex" "$ROOT/build"
  echo "全书 PDF：build/main.pdf"
else
  # 单章预览：按 subfiles 的约定，必须在章目录内编译。
  CHDIR="$(dirname "$TARGET")"
  NAME="$(basename "$CHDIR")"
  compile "$ROOT/$CHDIR" "$(basename "$TARGET")" "$ROOT/build/$NAME"
  echo "单章 PDF：build/$NAME/$(basename "${TARGET%.tex}").pdf"
fi
