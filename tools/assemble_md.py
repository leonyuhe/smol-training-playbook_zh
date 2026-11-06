#!/usr/bin/env python3
"""Put translated blocks back into article.mdx and add stable heading anchors."""
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; WORK=ROOT/"work"; SRC=ROOT/"app/src/content/article.mdx"

def parse_blocks(text):
    d={}; pat=re.compile(r"^<<<BLOCK ([^>\s]+)>>>[ \t]*$",re.M); ms=list(pat.finditer(text))
    for i,m in enumerate(ms):
        end=ms[i+1].start() if i+1<len(ms) else len(text)
        d[m.group(1)]=re.sub(r"\n?<<<END>>>\s*$","",text[m.end():end]).strip("\n")
    return d

def main():
    blocks=json.loads((WORK/"blocks.json").read_text())
    man=json.loads((WORK/"manifest.json").read_text())
    trans={}
    for c in man:
        p=Path(c["out"])
        if not p.exists(): print("MISSING",p.name); continue
        trans.update(parse_blocks(p.read_text()))
    hmap=json.loads((WORK/"heading_map.json").read_text())
    ids={}
    for i,item in enumerate(hmap):
        ids[i]=item[2] or "references"
    text=SRC.read_text()
    last=0
    for m in re.finditer(r"^import .*?;\s*$", text, re.M):
        last=m.end()
    prefix=text[:last]+"\n"
    body_parts=[]; hi=0
    for b in blocks:
        if b["id"] in trans:
            t=trans[b["id"]].strip("\n")
        else:
            t=b["text"]
        if b["type"]=="heading":
            aid=ids.get(hi,"")
            hi+=1
            if aid and not t.startswith("<a id="):
                t=f'<a id="{aid}"></a>\n\n{t}'
        if t and not t.endswith("\n"):
            t+="\n"
        body_parts.append(t)
    out=prefix+"".join(body_parts)
    SRC.write_text(out)
    print("wrote",SRC,"blocks",len(blocks),"translated",len(trans),"headings",hi,"anchors",sum(1 for v in ids.values() if v))

if __name__=="__main__": main()
