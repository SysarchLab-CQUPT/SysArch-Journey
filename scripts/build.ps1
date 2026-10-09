# 构建脚本（Windows PowerShell）。
#
#   .\scripts\build.ps1                                    构建全书 → build\main.pdf
#   .\scripts\build.ps1 chapters\03-riscv-isa\chapter.tex   只编译单章（预览用）
#
# 产物统一写在 build\ 下，仓库其它位置不会出现编译文件。
# 需要 TeX Live（xelatex，建议同时安装 latexmk）。
[CmdletBinding()]
param([string]$Target = 'main.tex')

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Root

if (-not (Get-Command xelatex -ErrorAction SilentlyContinue)) {
    throw '未找到 xelatex，请先安装 TeX Live。'
}

function Invoke-Compile {
    param([string]$WorkDir, [string]$File, [string]$OutDir)
    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
    Push-Location -LiteralPath $WorkDir
    try {
        if (Get-Command latexmk -ErrorAction SilentlyContinue) {
            & latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir=$OutDir $File
            if ($LASTEXITCODE -ne 0) { throw "latexmk 编译失败（退出码 $LASTEXITCODE）。" }
        } else {
            Write-Warning '未找到 latexmk，改用 xelatex 直接编译（需要多跑几遍）。'
            foreach ($pass in 1..3) {
                & xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=$OutDir $File
                if ($LASTEXITCODE -ne 0) { throw "xelatex 第 $pass 遍失败（退出码 $LASTEXITCODE）。" }
            }
        }
    } finally {
        Pop-Location
    }
}

if ($Target -eq 'main.tex') {
    # 章的清单和各表单的章节下拉都是派生产物，编译前重新生成一次，
    # 免得加了章却忘了跑脚本。
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        & python3 (Join-Path $Root 'scripts\update-manifest.py')
        & python3 (Join-Path $Root 'scripts\update-modules.py')
    } else {
        Write-Warning '未找到 python3，跳过章节清单与表单的同步。'
    }
    Invoke-Compile -WorkDir $Root -File 'main.tex' -OutDir (Join-Path $Root 'build')
    Write-Output '全书 PDF：build\main.pdf'
} else {
    # 单章预览：按 subfiles 的约定，必须在章目录内编译。
    $chapterDir = Split-Path -Parent $Target
    $name = Split-Path -Leaf $chapterDir
    $outDir = Join-Path (Join-Path $Root 'build') $name
    Invoke-Compile -WorkDir (Join-Path $Root $chapterDir) -File (Split-Path -Leaf $Target) -OutDir $outDir
    $base = [IO.Path]::GetFileNameWithoutExtension($Target)
    Write-Output "单章 PDF：build\$name\$base.pdf"
}
