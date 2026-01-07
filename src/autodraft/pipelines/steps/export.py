from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from autodraft.db.models import Draft
from autodraft.db.repos import DraftRepo
from autodraft.settings import settings


def escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def md_to_basic_html(md: str) -> str:
    """
    데모용 초간단 MD→HTML 변환기.
    (운영에서는 markdown 라이브러리 도입 추천)
    """
    lines = md.splitlines()
    html_lines: list[str] = []
    for line in lines:
        if line.startswith("# "):
            html_lines.append(f"<h1>{escape_html(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{escape_html(line[3:].strip())}</h2>")
        elif line.startswith("> "):
            html_lines.append(f"<blockquote>{escape_html(line[2:].strip())}</blockquote>")
        elif line.startswith("- "):
            html_lines.append(f"<li>{escape_html(line[2:].strip())}</li>")
        elif re.match(r"^\d+\.\s+", line):
            html_lines.append(f"<p>{escape_html(line.strip())}</p>")
        elif line.strip() == "":
            html_lines.append("<br/>")
        else:
            html_lines.append(f"<p>{escape_html(line.strip())}</p>")
    return "\n".join(_wrap_list_items(html_lines))


def _wrap_list_items(html_lines: list[str]) -> list[str]:
    out: list[str] = []
    in_ul = False
    for l in html_lines:
        if l.startswith("<li>") and not in_ul:
            out.append("<ul>")
            in_ul = True
            out.append(l)
        elif l.startswith("<li>") and in_ul:
            out.append(l)
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(l)
    if in_ul:
        out.append("</ul>")
    return out


def export_draft_html(db: Session, draft: Draft) -> Draft:
    """
    draft.content_md를 HTML 파일로 저장하고 export_html_ref에 경로를 기록.
    """
    export_dir = Path(settings.export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    body = md_to_basic_html(draft.content_md)
    path = export_dir / f"{draft.id}.html"
    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{escape_html(draft.title)}</title>
</head>
<body>
{body}
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")

    draft.export_html_ref = str(path)
    draft.updated_at = datetime.utcnow()
    return DraftRepo.save(db, draft)
