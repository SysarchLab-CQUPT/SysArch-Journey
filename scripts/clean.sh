#!/usr/bin/env bash
# 清掉编译产物，把仓库恢复成"只有源码"的状态。
#
#   scripts/clean.sh
#
# 正常编译的产物都在 build/ 下；另外清理编辑器和手动编译可能散落在
# 源码目录里的中间文件与 PDF。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

rm -rf build

find . -type f \( \
  -name '*.aux' -o -name '*.log' -o -name '*.out' -o -name '*.toc' \
  -o -name '*.lof' -o -name '*.lot' -o -name '*.bbl' -o -name '*.blg' \
  -o -name '*.xdv' -o -name '*.fls' -o -name '*.fdb_latexmk' \
  -o -name '*.synctex.gz' \) -delete

# 就地编译产生的 PDF 只会出现在仓库根或章目录里
rm -f main.pdf
find chapters -maxdepth 2 -name '*.pdf' -delete 2>/dev/null || true

# 清掉空目录（例如某些编辑器在 build/ 下镜像出的空结构）
find . -type d -name build -empty -delete 2>/dev/null || true

echo "已清理编译产物，仓库现在只有源码。"
