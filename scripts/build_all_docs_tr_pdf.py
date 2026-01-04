import asyncio
import glob
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage


FENCE_RE = re.compile(r"```.*?```", re.DOTALL)


def log(msg: str) -> None:
    print(msg, flush=True)


def _split_preserving_fences(md: str):
    """Split markdown into segments; fenced code blocks are kept as opaque segments."""
    parts = []
    last = 0
    for m in FENCE_RE.finditer(md):
        if m.start() > last:
            parts.append((False, md[last : m.start()]))
        parts.append((True, md[m.start() : m.end()]))
        last = m.end()
    if last < len(md):
        parts.append((False, md[last:]))
    return parts


def _chunk_text(text: str, max_chars: int = 7000):
    """Chunk plain markdown text (outside code fences) into safe sized blocks."""
    text = text.strip("\n")
    if not text:
        return []
    paras = re.split(r"\n\n+", text)
    chunks = []
    buf = ""
    for p in paras:
        cand = (buf + "\n\n" + p).strip() if buf else p
        if len(cand) <= max_chars:
            buf = cand
            continue
        if buf:
            chunks.append(buf)
            buf = ""
        if len(p) <= max_chars:
            buf = p
        else:
            # hard split very long paragraphs
            for i in range(0, len(p), max_chars):
                chunks.append(p[i : i + max_chars])
    if buf:
        chunks.append(buf)
    return chunks


async def _translate_chunk(chat: LlmChat, text: str, max_attempts: int = 4) -> str:
    for attempt in range(1, max_attempts + 1):
        try:
            msg = UserMessage(
                text=(
                    "Translate the following markdown text to Turkish. "
                    "Preserve markdown formatting. Output ONLY the translated markdown.\n\n" + text
                )
            )
            resp = await chat.send_message(msg)
            return resp.strip()
        except Exception as exc:
            if attempt >= max_attempts:
                raise
            sleep_s = 2 * attempt
            log(f"WARN: translate attempt {attempt} failed: {type(exc).__name__}. Retrying in {sleep_s}s")
            time.sleep(sleep_s)
    raise RuntimeError("unreachable")


async def translate_markdown(md: str, api_key: str, session_id: str) -> str:
    parts = _split_preserving_fences(md)
    out = []

    system_rules = (
        "You are a professional technical translator. Translate English to Turkish. "
        "Preserve markdown structure. Do NOT translate fenced code blocks. "
        "Do NOT translate shell commands, URLs, file paths, JSON/YAML keys. "
        "Keep headings and bullet formatting."
    )

    chat = LlmChat(api_key=api_key, session_id=session_id, system_message=system_rules).with_model("openai", "gpt-5.2")

    for is_fence, content in parts:
        if is_fence:
            out.append(content)
            continue

        chunks = _chunk_text(content)
        if not chunks:
            out.append(content)
            continue

        translated_chunks = []
        for i, c in enumerate(chunks, start=1):
            translated = await _translate_chunk(chat, c)
            translated_chunks.append(translated)
            log(f"  chunk {i}/{len(chunks)} done")

        out.append("\n\n".join(translated_chunks))

    return "".join(out)


def find_md_files(repo_root: str):
    paths = glob.glob(os.path.join(repo_root, "**/*.md"), recursive=True)
    filtered = []
    for p in paths:
        rp = os.path.relpath(p, repo_root)
        if any(seg in rp.split(os.sep) for seg in ["node_modules", ".git", "__pycache__"]):
            continue
        filtered.append(rp)
    return sorted(set(filtered))


def _ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _looks_english(text: str) -> bool:
    # lightweight heuristic: many English stopwords and not many Turkish chars
    if not text.strip():
        return False
    has_tr_chars = bool(re.search(r"[çğıöşüİÇĞÖŞÜ]", text))
    has_en_words = bool(re.search(r"\b(the|and|with|deploy|installation|setup|usage|runbook|troubleshoot)\b", text, re.IGNORECASE))
    return has_en_words and (not has_tr_chars)


def md_to_pdf_simple(md_path: str, pdf_path: str):
    """Simple markdown->PDF via reportlab Paragraphs; dependency-light.

    Registers DejaVuSans so Turkish characters render correctly.
    """

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

    text = Path(md_path).read_text(encoding="utf-8")

    styles = getSampleStyleSheet()
    normal = styles["BodyText"]
    code_style = styles["Code"]

    # Apply font if available
    if "DejaVuSans" in pdfmetrics.getRegisteredFontNames():
        for st in styles.byName.values():
            try:
                st.fontName = "DejaVuSans"
            except Exception:
                pass
        code_style.fontName = "DejaVuSans"

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    story = []

    lines = text.splitlines()
    buf = []
    in_code = False
    code_buf = []

    def flush_paragraph():
        nonlocal buf
        if not buf:
            return
        paragraph = "\n".join(buf).strip()
        buf = []
        if not paragraph:
            return
        if paragraph.startswith("#"):
            level = len(paragraph) - len(paragraph.lstrip("#"))
            title = paragraph.lstrip("#").strip()
            style = styles["Heading1"] if level == 1 else styles["Heading2"] if level == 2 else styles["Heading3"]
            story.append(Paragraph(title, style))
            story.append(Spacer(1, 0.2 * cm))
            return

        if paragraph.strip() == "---":
            story.append(Spacer(1, 0.3 * cm))
            return

        # Some markdown files embed HTML line breaks inside tables (e.g. <br>). Convert them to newlines.
        # Normalize any inline HTML breaks so reportlab doesn't choke on <br> (non-self-closing).
        paragraph = (
            paragraph.replace("<br/>", "__BR__")
            .replace("<br />", "__BR__")
            .replace("<br>", "__BR__")
        )

        # Escape all HTML, then re-insert ONLY our safe <br/> tags.
        paragraph = paragraph.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        paragraph = paragraph.replace("__BR__", "<br/>")
        paragraph = paragraph.replace("\n", "<br/>")

        # reportlab can't handle certain constructs in Paragraph (esp. markdown tables). Fallback safely.
        try:
            story.append(Paragraph(paragraph, normal))
            story.append(Spacer(1, 0.2 * cm))
        except Exception:
            from reportlab.platypus import Preformatted
            safe = (
                paragraph.replace("<br/>", "\n")
                .replace("&lt;br&gt;", "\n")
                .replace("&lt;br/&gt;", "\n")
                .replace("&lt;br /&gt;", "\n")
            )
            story.append(Preformatted(safe, code_style))
            story.append(Spacer(1, 0.2 * cm))

    for ln in lines:
        if ln.strip().startswith("```"):
            if not in_code:
                flush_paragraph()
                in_code = True
                code_buf = []
            else:
                in_code = False
                code_text = "\n".join(code_buf)
                story.append(Preformatted(code_text, code_style))
                story.append(Spacer(1, 0.2 * cm))
                code_buf = []
            continue

        if in_code:
            code_buf.append(ln)
            continue

        if ln.strip() == "":
            flush_paragraph()
            continue

        if ln.strip() == "[[PAGEBREAK]]":
            flush_paragraph()
            story.append(PageBreak())
            continue

        buf.append(ln)

    flush_paragraph()
    doc.build(story)


async def main():
    load_dotenv("/app/backend/.env")
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        raise SystemExit("EMERGENT_LLM_KEY is missing in /app/backend/.env")

    repo_root = "/app"
    md_files = find_md_files(repo_root)

    cache_root = "/app/tmp/docs_tr_cache"
    Path(cache_root).mkdir(parents=True, exist_ok=True)

    merged = []
    merged.append("# Tüm Sistem Dokümantasyonu (Türkçe)\n")
    merged.append("Bu doküman repo içindeki tüm `.md` dosyalarının Türkçe birleşimidir.\n")
    merged.append("---\n")

    total = len(md_files)
    log(f"Found {total} markdown files")

    for idx, rp in enumerate(md_files, start=1):
        abs_path = os.path.join(repo_root, rp)
        raw = Path(abs_path).read_text(encoding="utf-8", errors="ignore")

        cache_path = os.path.join(cache_root, rp + ".tr.md")
        _ensure_parent(cache_path)

        if os.path.exists(cache_path):
            translated = Path(cache_path).read_text(encoding="utf-8", errors="ignore")
            log(f"[{idx}/{total}] cache hit: {rp}")
        else:
            log(f"[{idx}/{total}] translating: {rp}")
            if _looks_english(raw):
                translated = await translate_markdown(raw, api_key=key, session_id=f"docs-tr-{idx}")
            else:
                translated = raw
            Path(cache_path).write_text(translated, encoding="utf-8")
            log(f"[{idx}/{total}] saved cache")

        merged.append(f"\n\n[[PAGEBREAK]]\n\n# Dosya: `{rp}`\n")
        merged.append(translated)
        merged.append("\n")

    out_md = "/app/ALL_DOCS_TR.md"
    Path(out_md).write_text("\n".join(merged), encoding="utf-8")
    log(f"Wrote {out_md}")

    out_pdf = "/app/ALL_DOCS_TR.pdf"
    md_to_pdf_simple(out_md, out_pdf)
    log(f"Wrote {out_pdf}")


if __name__ == "__main__":
    asyncio.run(main())
