import asyncio
import glob
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage


FENCE_RE = re.compile(r"```.*?```", re.DOTALL)


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


def _chunk_text(text: str, max_chars: int = 9000):
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


async def translate_markdown(md: str, chat: LlmChat) -> str:
    parts = _split_preserving_fences(md)
    out = []

    system_rules = (
        "You are a professional technical translator. Translate English to Turkish. "
        "Preserve markdown structure. Do NOT translate fenced code blocks, shell commands, URLs, "
        "file paths, JSON/YAML keys. Keep headings and bullet formatting."
    )

    # Make a dedicated chat per file for better consistency
    chat = LlmChat(api_key=chat.api_key, session_id=chat.session_id + "-file", system_message=system_rules).with_model("openai", "gpt-5.2")

    for is_fence, content in parts:
        if is_fence:
            out.append(content)
            continue

        chunks = _chunk_text(content)
        if not chunks:
            out.append(content)
            continue

        translated_chunks = []
        for c in chunks:
            msg = UserMessage(
                text=(
                    "Translate the following markdown text to Turkish. "
                    "Do not add commentary. Output ONLY the translated markdown.\n\n" + c
                )
            )
            resp = await chat.send_message(msg)
            translated_chunks.append(resp.strip())

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


def md_to_pdf_simple(md_path: str, pdf_path: str):
    """Simple markdown->PDF via reportlab Paragraphs; keeps it robust and dependency-light."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
    from reportlab.lib.units import cm

    text = Path(md_path).read_text(encoding="utf-8")

    styles = getSampleStyleSheet()
    normal = styles["BodyText"]
    code_style = styles["Code"]

    doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)

    story = []

    # Very lightweight renderer: headings + paragraphs + code fences.
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
        # crude heading detection
        if paragraph.startswith("#"):
            level = len(paragraph) - len(paragraph.lstrip("#"))
            title = paragraph.lstrip("#").strip()
            style = styles["Heading1"] if level == 1 else styles["Heading2"] if level == 2 else styles["Heading3"]
            story.append(Paragraph(title, style))
            story.append(Spacer(1, 0.2 * cm))
        elif paragraph.strip() == "---":
            story.append(Spacer(1, 0.3 * cm))
        else:
            # escape minimal xml
            paragraph = paragraph.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            paragraph = paragraph.replace("\n", "<br/>")
            story.append(Paragraph(paragraph, normal))
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

        # page break marker
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

    chat = LlmChat(api_key=key, session_id="docs-tr", system_message="You are a helpful assistant.").with_model("openai", "gpt-5.2")

    merged = []
    merged.append("# Tüm Sistem Dokümantasyonu (Türkçe)\n")
    merged.append("Bu doküman repo içindeki tüm `.md` dosyalarının Türkçe birleşimidir.\n")
    merged.append("---\n")

    for rp in md_files:
        abs_path = os.path.join(repo_root, rp)
        raw = Path(abs_path).read_text(encoding="utf-8", errors="ignore")

        # Heuristic: if contains many non-ascii Turkish already, skip translation
        needs_translation = bool(re.search(r"\b(the|and|with|deploy|installation|setup|usage)\b", raw, re.IGNORECASE))

        if needs_translation:
            translated = await translate_markdown(raw, chat)
        else:
            translated = raw

        merged.append(f"\n\n[[PAGEBREAK]]\n\n# Dosya: `{rp}`\n")
        merged.append(translated)
        merged.append("\n")

    out_md = "/app/ALL_DOCS_TR.md"
    Path(out_md).write_text("\n".join(merged), encoding="utf-8")

    out_pdf = "/app/ALL_DOCS_TR.pdf"
    md_to_pdf_simple(out_md, out_pdf)

    print("OK")
    print(out_md)
    print(out_pdf)


if __name__ == "__main__":
    asyncio.run(main())
