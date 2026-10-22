#!/usr/bin/env python3
"""Generate book statistics for the GitHub Pages PDF preview."""

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
BEIJING = ZoneInfo("Asia/Shanghai")
CHAPTER_TITLE = re.compile(r"\\chapter\*?\{([^{}]*)\}")
SECTION_TITLE = re.compile(r"\\section\*?\{([^{}]*)\}")
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
LATIN_WORD = re.compile(r"[A-Za-z0-9]+(?:[._+\-][A-Za-z0-9]+)*")
INCLUDEGRAPHICS = re.compile(
    r"\\includegraphics\*?\s*(?:\[[^\]]*\])?\s*\{([^{}]+)\}",
)
IMAGE_SUFFIXES = (".pdf", ".png", ".jpg", ".jpeg", ".svg", ".eps")
EXCLUDED_ENVIRONMENTS = re.compile(
    r"\\begin\{(lstlisting|verbatim|equation\*?|align\*?|gather\*?|multline\*?)\}"
    r"[\s\S]*?\\end\{\1\}",
)


def git_value(*args):
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def strip_comments(source):
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in source.splitlines())


def strip_latex_for_counting(source):
    source = strip_comments(source)
    source = EXCLUDED_ENVIRONMENTS.sub(" ", source)
    source = re.sub(r"\\verb\*?(.)(.*?)\1", " ", source, flags=re.DOTALL)
    source = re.sub(r"\$[^$]*\$", " ", source, flags=re.DOTALL)
    source = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", source)
    return re.sub(r"[{}]", " ", source)


def count_text(source):
    text = strip_latex_for_counting(source)
    cjk_characters = len(CJK.findall(text))
    latin_words = len(LATIN_WORD.findall(CJK.sub(" ", text)))
    return {
        "word_count": cjk_characters + latin_words,
        "cjk_characters": cjk_characters,
        "latin_words": latin_words,
    }


def resolve_graphic_path(value, base_dir):
    raw = value.strip()
    if not raw or raw.startswith("#"):
        return None
    candidates = [raw]
    if Path(raw).suffix.lower() not in IMAGE_SUFFIXES:
        candidates.extend(raw + suffix for suffix in IMAGE_SUFFIXES)
    for candidate in candidates:
        path = (base_dir / candidate).resolve()
        if path.is_file():
            return path
    return None


def count_images(source, base_dir=None, section_stem=None):
    source = EXCLUDED_ENVIRONMENTS.sub(" ", strip_comments(source))
    direct_paths = [
        resolve_graphic_path(value, base_dir) if base_dir else None
        for value in INCLUDEGRAPHICS.findall(source)
        if not value.strip().startswith("#")
    ]
    image_count = len([value for value in INCLUDEGRAPHICS.findall(source)
                       if not value.strip().startswith("#")])

    if base_dir and section_stem:
        section_dir = base_dir / "figures" / section_stem
        section_images = {
            path.resolve() for path in section_dir.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        } if section_dir.is_dir() else set()
        directly_referenced = {path for path in direct_paths if path is not None}
        image_count += len(section_images - directly_referenced)

    return image_count


def count_source(paths):
    cjk_characters = 0
    latin_words = 0
    for path in paths:
        source = path.read_text(encoding="utf-8")
        counts = count_text(source)
        cjk_characters += counts["cjk_characters"]
        latin_words += counts["latin_words"]
    return {
        "word_count": cjk_characters + latin_words,
        "cjk_characters": cjk_characters,
        "latin_words": latin_words,
    }


def chapter_info():
    chapters = []
    for chapter_dir in sorted((ROOT / "chapters").iterdir()):
        entry = chapter_dir / "chapter.tex"
        if not chapter_dir.is_dir() or not entry.is_file():
            continue
        title_match = CHAPTER_TITLE.search(entry.read_text(encoding="utf-8"))
        title = title_match.group(1).strip() if title_match else chapter_dir.name
        number_match = re.match(r"^(\d+)", chapter_dir.name)
        number = int(number_match.group(1)) if number_match else None
        section_paths = sorted(
            path for path in chapter_dir.glob("[0-9][0-9]-*.tex")
            if path.is_file()
        )
        sections = []
        for section_path in section_paths:
            source = section_path.read_text(encoding="utf-8")
            match = SECTION_TITLE.search(source)
            counts = count_text(source)
            sections.append({
                "title": match.group(1).strip() if match else section_path.stem,
                "word_count": counts["word_count"],
                "image_count": count_images(source, chapter_dir, section_path.stem),
            })
        chapters.append({
            "number": number,
            "title": title,
            "section_count": len(sections),
            "word_count": sum(section["word_count"] for section in sections),
            "image_count": sum(section["image_count"] for section in sections),
            "sections": sections,
        })
    return chapters


def source_paths():
    paths = []
    preface = ROOT / "frontmatter" / "preface.tex"
    appendix = ROOT / "backmatter" / "appendix.tex"
    if preface.is_file():
        paths.append(preface)
    if appendix.is_file():
        paths.append(appendix)
    for chapter_dir in sorted((ROOT / "chapters").iterdir()):
        if chapter_dir.is_dir():
            paths.extend(sorted(chapter_dir.glob("[0-9][0-9]-*.tex")))
    return paths


def pdf_page_count():
    log_path = ROOT / "build" / "main.log"
    if not log_path.is_file():
        return None
    match = re.search(
        r"Output written on .*?\((\d+) pages?",
        log_path.read_text(encoding="utf-8", errors="replace"),
    )
    return int(match.group(1)) if match else None


def updated_at():
    value = git_value("log", "-1", "--format=%cI")
    if value:
        return datetime.fromisoformat(value).astimezone(BEIJING)
    return datetime.fromtimestamp(
        (ROOT / "main.tex").stat().st_mtime,
        tz=BEIJING,
    )


def build_info():
    chapters = chapter_info()
    counts = count_source(source_paths())
    image_count = sum(chapter["image_count"] for chapter in chapters)
    for path in (ROOT / "frontmatter" / "preface.tex", ROOT / "backmatter" / "appendix.tex"):
        if path.is_file():
            image_count += count_images(path.read_text(encoding="utf-8"), ROOT)
    pdf_path = ROOT / "build" / "main.pdf"
    changed = updated_at()
    return {
        "updated_at": changed.date().isoformat(),
        "updated_at_iso": changed.isoformat(),
        "built_at": datetime.now(BEIJING).date().isoformat(),
        "commit": git_value("rev-parse", "--short", "HEAD") or "unknown",
        "chapter_count": len(chapters),
        "section_count": sum(chapter["section_count"] for chapter in chapters),
        "word_count": counts["word_count"],
        "cjk_characters": counts["cjk_characters"],
        "latin_words": counts["latin_words"],
        "image_count": image_count,
        "page_count": pdf_page_count(),
        "pdf_bytes": pdf_path.stat().st_size if pdf_path.is_file() else None,
        "chapters": chapters,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="Path to write book-info.json")
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build_info(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
