#!/usr/bin/env python3
"""Split article.mdx body into translatable blocks and chunks, preserving MDX."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
SRC = APP / "src/content/article.mdx"
WORK = ROOT / "work"
CHUNKS = WORK / "chunks"
OUT = WORK / "out"
WORD = re.compile(r"[A-Za-z][A-Za-z'’\-]*")

def is_fence(line): return line.lstrip().startswith("```")
def is_blank(line): return not line.strip()
def is_heading(line): return re.match(r"^#{1,6}\s+", line)
def is_list(line): return re.match(r"^\s{0,3}([-*+]|\d+\.)\s+", line)
def is_table(line): return line.lstrip().startswith("|")
def is_indented_code(line): return line.startswith("    ") and line.strip()

def component_end(lines, start, tag):
    """Find first line index >= start containing </tag> (or /> on start line)."""
    if re.search(r"/>\s*$", lines[start]) or tag.lower() in {"img","br","hr","iframe"}:
        return start
    close = re.compile(r"</" + re.escape(tag) + r"\s*>", re.I)
    for j in range(start, len(lines)):
        if close.search(lines[j]): return j
    return None

def block_type(lines, i):
    line = lines[i]
    if is_fence(line): return "code"
    if is_blank(line): return "blank"
    if is_heading(line): return "heading"
    if is_table(line): return "table"
    if is_list(line): return "list"
    m = re.match(r"^<([A-Za-z][\w:-]*)(\s|>|/)", line)
    if m:
        return "component"
    if line.startswith("<!--"): return "component"
    return "para"

def main():
    CHUNKS.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
    text = SRC.read_text()
    idx = text.index("\n## Introduction")
    prefix = text[:idx]
    body = text[idx:]
    lines = body.splitlines(keepends=True)
    blocks = []
    i = 0
    while i < len(lines):
        t = block_type(lines, i)
        if t == "blank":
            j = i
            while j < len(lines) and is_blank(lines[j]): j += 1
            blocks.append({"type": "blank", "text": "".join(lines[i:j]), "trans": False})
            i = j; continue
        if t == "code":
            j = i + 1
            while j < len(lines) and not (is_fence(lines[i]) and is_fence(lines[j])): j += 1
            j = min(j + 1, len(lines))
            blocks.append({"type": "code", "text": "".join(lines[i:j]), "trans": False})
            i = j; continue
        if t == "heading":
            blocks.append({"type": "heading", "text": lines[i], "trans": True})
            i += 1; continue
        if t == "table":
            j = i
            while j < len(lines) and is_table(lines[j]): j += 1
            blocks.append({"type": "table", "text": "".join(lines[i:j]), "trans": True})
            i = j; continue
        if t == "list":
            j = i
            while j < len(lines):
                if is_blank(lines[j]): break
                if is_list(lines[j]) or re.match(r"^\s{2,}\S", lines[j]): j += 1
                else: break
            blocks.append({"type": "list", "text": "".join(lines[i:j]), "trans": True})
            i = j; continue
        if t == "component":
            m = re.match(r"^<([A-Za-z][\w:-]*)", lines[i])
            tag = m.group(1) if m else "div"
            j = component_end(lines, i, tag)
            if j is None:
                # fall back to paragraph
                j = i
                while j < len(lines) and not is_blank(lines[j]): j += 1
                blocks.append({"type": "component", "text": "".join(lines[i:j]), "trans": False})
            else:
                raw = "".join(lines[i:j+1])
                low = raw.lower()
                trans = not any(x in low for x in ("<canvas", "<script", "<style", "<svg"))
                blocks.append({"type": "component", "text": raw, "trans": trans})
                i = j + 1; continue
            i = j; continue
        # paragraph
        j = i
        while j < len(lines) and not is_blank(lines[j]) and not (
            is_heading(lines[j]) or is_table(lines[j]) or is_list(lines[j]) or is_fence(lines[j])
        ):
            j += 1
        # don't swallow a component start after the first line
        k = i + 1
        while k < j:
            if re.match(r"^<([A-Za-z][\w:-]*)(\s|>|/)", lines[k]):
                j = k; break
            k += 1
        blocks.append({"type": "para", "text": "".join(lines[i:j]), "trans": True})
        i = j
    # assign ids and words
    for n, b in enumerate(blocks):
        b["id"] = f"b{n:04d}"
        b["words"] = len(WORD.findall(re.sub(r"<[^>]+>", " ", b["text"]))) if b["trans"] else 0
    # group translatable blocks into chunks
    chunks=[]; cur=[]; cw=0
    for b in blocks:
        if not b["trans"]:
            continue
        if cur and cw + b["words"] > 1200:
            chunks.append(cur); cur=[]; cw=0
        cur.append(b); cw += b["words"]
    if cur: chunks.append(cur)
    manifest=[]
    for n,ch in enumerate(chunks,1):
        cid=f"chunk-{n:03d}"
        out=[]
        for b in ch:
            out.append(f"<<<BLOCK {b['id']}>>>")
            out.append(b["text"].rstrip("\n"))
        out.append("<<<END>>>")
        (CHUNKS/f"{cid}.txt").write_text("\n".join(out)+"\n")
        manifest.append({"id":cid,"blocks":[b["id"] for b in ch],"words":sum(b["words"] for b in ch),
                         "file":str(CHUNKS/f"{cid}.txt"),"out":str(OUT/f"{cid}.txt")})
    (WORK/"blocks.json").write_text(json.dumps(blocks,ensure_ascii=False,indent=1))
    (WORK/"prefix.txt").write_text(prefix)
    (WORK/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(len(blocks),"blocks,",len(chunks),"chunks,",sum(c["words"] for c in manifest),"words")
    from collections import Counter
    print(Counter(b["type"] for b in blocks))
    for c in manifest[:5]: print(c["id"],c["words"],len(c["blocks"]))

if __name__=="__main__": main()
