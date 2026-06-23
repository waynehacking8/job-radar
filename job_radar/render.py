"""Presentation: the Markdown digest (Strong fits first), and a minimal Markdown
-> email-safe HTML converter (carried over from gh-radar — generic)."""
import re
from html import escape as html_escape

SOURCE_NAMES = {"workday": "Workday", "greenhouse": "Greenhouse", "lever": "Lever"}
FIT_ICON = {"strong": "🟢", "medium": "🔵"}


def _posted(job):
    return f" · {job.posted}" if job.posted else ""


def render_md(jobs, when):
    used = sorted({SOURCE_NAMES.get(j.source, j.source) for j in jobs})
    strong = [j for j in jobs if j.fit == "strong"]
    medium = [j for j in jobs if j.fit != "strong"]
    lines = [f"# Job Radar — {when}", "",
             f"_{len(jobs)} new Taiwan ML / LLM / GPU openings via {', '.join(used)}._", ""]

    i = 0
    for label, group in (("🟢 Strong fit", strong), ("🔵 Adjacent", medium)):
        if not group:
            continue
        lines += [f"## {label} ({len(group)})", ""]
        for j in group:
            i += 1
            tags = " · ".join(j.tags[:6])
            lines.append(f"### {i}. [{j.title}]({j.url})")
            lines.append(f"**{j.company}** · {j.location}{_posted(j)}")
            if tags:
                lines.append(f"`{tags}`")
            lines.append(f"[Apply →]({j.url}) · via {SOURCE_NAMES.get(j.source, j.source)}")
            lines.append("")
    return "\n".join(lines)


def _inline(s):
    """HTML-escape text, THEN convert our markdown links/bold/code, so a title
    containing <, >, & or quotes can't break the email."""
    s = html_escape(s, quote=True)
    s = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def md_to_html(md):
    """Minimal Markdown -> HTML good enough for email clients."""
    out = []
    for line in md.split("\n"):
        if line.startswith("### "):
            out.append(f"<h3>{_inline(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{_inline(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{_inline(line[2:])}</h1>")
        elif line.strip() == "":
            out.append("<br>")
        else:
            out.append(f"<p style='margin:2px 0'>{_inline(line)}</p>")
    return ("<div style=\"font-family:-apple-system,Segoe UI,Roboto,sans-serif;"
            "max-width:680px;margin:auto;line-height:1.45\">" + "\n".join(out) + "</div>")
