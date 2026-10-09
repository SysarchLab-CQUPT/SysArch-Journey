# latexmk 配置：统一使用 XeLaTeX，中间文件输出到 build/。
$pdf_mode = 5;
$xelatex = 'xelatex -interaction=nonstopmode -halt-on-error -file-line-error %O %S';
$out_dir = 'build';
$max_repeat = 5;
# 参考文献文件的路径以仓库根目录为基准，始终运行 bibtex。
$bibtex_use = 2;
