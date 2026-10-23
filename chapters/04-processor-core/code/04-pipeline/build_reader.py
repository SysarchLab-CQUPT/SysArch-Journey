"""Generate a complete, offline HTML textbook from the same LaTeX source.
Requires Pandoc on PATH (or PANDOC=/absolute/path/to/pandoc).
Run after the full book build and generate_assets.py; no network/CDN is used.
"""
from pathlib import Path
import html
import os
import re
import subprocess

SRC = Path(__file__).resolve().parent
CH = SRC.parents[1]
ROOT = SRC.parents[3]


def group(text, start):
    """Read one balanced TeX brace group used in these two source sections."""
    assert text[start] == '{'
    depth = 1
    for i in range(start+1, len(text)):
        if text[i] == '{' and text[i-1] != '\\': depth += 1
        if text[i] == '}' and text[i-1] != '\\': depth -= 1
        if depth == 0: return text[start+1:i], i+1
    raise ValueError('Unclosed TeX group')


def preprocess(source, section, labels):
    source = source.replace('\\begin{minipage}{\\linewidth}', '').replace('\\end{minipage}', '')
    source = source.replace('\\vspace{8pt}', '')
    source = re.sub(r'\\section\{', lambda _: '\\section{'+section+' ', source)
    counter = [0]
    def subheading(match):
        counter[0] += 1
        return '\\subsection{'+section+'.'+str(counter[0])+' '+match[1]+'}'
    source = re.sub(r'\\subsection\{([^}]+)\}', subheading, source)
    while '\\KeyPoint{' in source:
        start = source.index('\\KeyPoint{')
        title, end = group(source, start+len('\\KeyPoint'))
        body, end = group(source, end)
        source = source[:start] + '\\begin{quote}\\textbf{'+title+'}\\par\n'+body+'\\end{quote}' + source[end:]
    while '\\begin{tabularx}' in source:
        start = source.index('\\begin{tabularx}')
        _, end = group(source, start+len('\\begin{tabularx}'))
        spec, end = group(source, end)
        # Widths are handled responsively by CSS, not copied from the print layout.
        spec = re.sub(r'p\{[^}]*\}', 'l', spec).replace('Y','l')
        source = source[:start] + '\\begin{tabular}{'+spec+'}' + source[end:]
    source = source.replace('\\end{tabularx}', '\\end{tabular}')
    def listing(match):
        options, file = match[1], match[2]
        caption = re.search(r'caption=\{([^}]+)\}', options)
        label = re.search(r'label=\{([^}]+)\}', options)
        number = labels.get(label[1], '') if label else ''
        heading = '\\paragraph{代码 '+number+'：'+caption[1]+'}\n' if caption else ''
        anchor = '\\hypertarget{'+label[1]+'}{}\n' if label else ''
        code = (CH/file).read_text(encoding='utf-8').rstrip()
        lang = 'Verilog' if file.endswith('.v') else ''
        options = '[language='+lang+']' if lang else ''
        return anchor+heading+'\\begin{lstlisting}'+options+'\n'+code+'\n\\end{lstlisting}\n'
    source = re.sub(r'\\lstinputlisting\[(.*?)\]\{([^}]+)\}', listing, source, flags=re.S)
    def crossref(match):
        label = match[1]
        number = labels.get(label, '')
        name = ('第 '+number+' 节' if label.startswith('sec:') else
                ('表 ' if label.startswith('tab:') else '图 ' if label.startswith('fig:') else '代码 ')+number)
        url = '#'+label if label.startswith(('sec:04','tab:ch4','fig:ch4','lst:ch4')) else '../../../../index.html'
        return '\\href{'+url+'}{'+name+'}'
    source = re.sub(r'\\cref\{([^}]+)\}', crossref, source)
    source = re.sub(r'\\caption\{([^}]+)\}\s*\\label\{([^}]+)\}',
                    lambda m:'\\caption{'+('表 ' if m[2].startswith('tab:') else '图 ')+labels.get(m[2],'')+' '+m[1]+'}\\label{'+m[2]+'}',source)
    source = re.sub(r'\\label\{([^}]+)\}', r'\\hypertarget{\1}{}', source)
    source = re.sub(r'\\includegraphics\[[^]]*\]\{([^}]+)\}', lambda m:'\\includegraphics{../../'+m[1]+'.svg}', source)
    return source


def main():
    aux = (ROOT/'build/main.aux').read_text(encoding='utf-8')
    labels = dict(re.findall(r'\\newlabel\{([^}]+)\}\{\{([^}]*)\}',aux))
    text = '\n\n'.join(preprocess((CH/name).read_text(encoding='utf-8'),section,labels)
                       for name,section in [('04-pipeline.tex','4.04'),('05-hazard.tex','4.05')])
    temp = ROOT/'build/rtl-pipeline/reader.tex'
    temp.write_text(text,encoding='utf-8')
    converted = subprocess.run([os.environ.get('PANDOC','pandoc'),str(temp),'-f','latex','-t','html5',
                               '--math-method=mathml','--shift-heading-level-by=1','--citeproc',
                               '--bibliography',str(CH/'refs.bib'),'-M','link-citations=true','--wrap=none'],
                               capture_output=True,text=True,encoding='utf-8',check=True)
    (ROOT/'build/rtl-pipeline/reader-conversion.log').write_text(converted.stderr,encoding='utf-8')
    body = converted.stdout
    body = body.replace('<div id="refs"', '<h2 id="references">参考文献</h2>\n<div id="refs"')
    assert body.count('<table') >= 8 and body.count('<figure') == 6
    visible = re.sub(r'<annotation.*?</annotation>', '', body, flags=re.S)
    assert body.count('<pre') >= 7 and '\\begin{' not in visible
    body = re.sub(r'<table([^>]*)>(.*?)</table>',r'<div class="table-scroll"><table\1>\2</table></div>',body,flags=re.S)
    # Reuse the simulator-backed explorer rather than introducing a second dataset.
    explorer = (SRC/'explorer.html').read_text(encoding='utf-8')
    panel = re.search(r'<section id="explorer">.*?</section>',explorer,re.S).group()
    panel_script = re.search(r'<script>(.*?)</script>',explorer,re.S)[1]
    template = (SRC/'reader-template.html').read_text(encoding='utf-8')
    result = template.replace('<!-- TEXTBOOK -->',body).replace('<!-- EXPLORER -->',panel).replace('/* EXPLORER_SCRIPT */',panel_script)
    (SRC/'index.html').write_text(result,encoding='utf-8')
    print('PASS: complete HTML reader, tables, 6 figures, source-code excerpts, MathML and live cycle explorer')


if __name__ == '__main__': main()
