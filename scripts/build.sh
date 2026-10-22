#!/usr/bin/env bash
# 构建脚本（macOS / Linux）。
#
#   scripts/build.sh                                      构建全书 → build/main.pdf
#   scripts/build.sh chapters/03-riscv-isa/chapter.tex     只编译单章（预览用）
#   scripts/build.sh chapters/03-riscv-isa/02-role.tex     只编译单节（预览用）
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
  # 在 $1 目录内编译 $2，输出到 $3；可选 $4 指定 jobname。
  local workdir="$1" file="$2" outdir="$3" jobname="${4:-}"
  local latexmk_args xelatex_args
  mkdir -p "$outdir"

  latexmk_args=(
    -xelatex
    -interaction=nonstopmode
    -halt-on-error
    -file-line-error
    "-outdir=$outdir"
  )
  xelatex_args=(
    -interaction=nonstopmode
    -halt-on-error
    -file-line-error
    "-output-directory=$outdir"
  )
  if [ -n "$jobname" ]; then
    latexmk_args+=("-jobname=$jobname")
    xelatex_args+=("-jobname=$jobname")
  fi
  latexmk_args+=("$file")
  xelatex_args+=("$file")

  if [ "$HAS_LATEXMK" = "1" ]; then
    ( cd "$workdir" && latexmk "${latexmk_args[@]}" )
  else
    echo "未找到 latexmk，改用 xelatex 直接编译（需要多跑几遍）。" >&2
    ( cd "$workdir" && for pass in 1 2 3; do
        xelatex "${xelatex_args[@]}"
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
  TARGET="${TARGET#./}"
  if [ ! -f "$ROOT/$TARGET" ]; then
    echo "找不到目标文件：$TARGET" >&2
    exit 1
  fi

  CHDIR="$(dirname "$TARGET")"
  NAME="$(basename "$CHDIR")"
  FILE="$(basename "$TARGET")"

  if [ ! -f "$ROOT/$CHDIR/chapter.tex" ]; then
    echo "目标不在有效章节目录中，缺少 $CHDIR/chapter.tex。" >&2
    exit 1
  fi

  if [ "$FILE" = "chapter.tex" ]; then
    # 单章预览：按 subfiles 的约定，必须在章目录内编译。
    compile "$ROOT/$CHDIR" "$FILE" "$ROOT/build/$NAME"
    echo "单章 PDF：build/$NAME/${FILE%.tex}.pdf"
  else
    # 单节预览：临时生成一个最小 subfiles 包装器，载入全书前言和本章单节。
    # 包装器放在章目录中，确保节内的 figures/、code/ 相对路径仍按本章解析。
    BASE="${FILE%.tex}"
    CHAPTER_TOKEN="${NAME%%-*}"
    SECTION_TOKEN="${BASE%%-*}"
    CHAPTER_NUMBER=0
    SECTION_NUMBER=0

    if [[ "$CHAPTER_TOKEN" =~ ^[0-9]+$ ]]; then
      CHAPTER_NUMBER=$((10#$CHAPTER_TOKEN))
    fi
    if [[ "$SECTION_TOKEN" =~ ^[0-9]+$ ]]; then
      SECTION_NUMBER=$((10#$SECTION_TOKEN))
      if [ "$SECTION_NUMBER" -gt 0 ]; then
        SECTION_NUMBER=$((SECTION_NUMBER - 1))
      fi
    fi

    PREVIEW_RAW=""
    PREVIEW_FILE=""
    cleanup_preview() {
      rm -f -- "${PREVIEW_RAW:-}" "${PREVIEW_FILE:-}"
    }
    trap cleanup_preview EXIT
    trap 'exit 130' INT TERM

    PREVIEW_RAW="$(mktemp "$ROOT/$CHDIR/.section-preview.XXXXXX")"
    PREVIEW_FILE="$PREVIEW_RAW.tex"
    mv -- "$PREVIEW_RAW" "$PREVIEW_FILE"

    {
      printf '%s\n' '\documentclass[../../main.tex]{subfiles}'
      printf '%s\n' '\begin{document}'
      printf '\\setcounter{chapter}{%s}\n' "$CHAPTER_NUMBER"
      printf '\\setcounter{section}{%s}\n' "$SECTION_NUMBER"
      printf '%s\n' '\markboth{单节预览}{}'
      printf '\\input{%s}\n' "$FILE"
      printf '%s\n' '\end{document}'
    } > "$PREVIEW_FILE"

    SECTION_OUT="$ROOT/build/$NAME/sections"
    compile "$ROOT/$CHDIR" "$(basename "$PREVIEW_FILE")" "$SECTION_OUT" "$BASE"
    echo "单节 PDF：build/$NAME/sections/$BASE.pdf"
  fi
fi
