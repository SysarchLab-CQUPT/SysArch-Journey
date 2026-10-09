# 清掉编译产物，把仓库恢复成"只有源码"的状态。
#
#   .\scripts\clean.ps1
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Root

Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Root 'build')

$patterns = '*.aux','*.log','*.out','*.toc','*.lof','*.lot','*.bbl','*.blg','*.xdv','*.fls','*.fdb_latexmk','*.synctex.gz'
Get-ChildItem -Path $Root -Recurse -File -Include $patterns -ErrorAction SilentlyContinue | Remove-Item -Force

Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $Root 'main.pdf')
Get-ChildItem -Path (Join-Path $Root 'chapters') -Recurse -Filter '*.pdf' -ErrorAction SilentlyContinue | Remove-Item -Force

Write-Output '已清理编译产物，仓库现在只有源码。'
