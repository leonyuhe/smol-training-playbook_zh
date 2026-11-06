#!/usr/bin/env python3
"""Prefix root-absolute public asset URLs for GitHub Pages project hosting."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DIST=ROOT/"app/dist"; BASE="/smol-training-playbook_zh"
PAT=re.compile(r'([\"\'(`=])/(data/|scripts/|embeds/|thumb\.png|smol-llm\.pdf)')
SUF={".html",".js",".css",".json",".txt",".xml"}
def main():
    n=0
    for p in DIST.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in SUF: continue
        try: s=p.read_text()
        except UnicodeDecodeError: continue
        t=PAT.sub(lambda m:f'{m.group(1)}{BASE}/{m.group(2)}',s)
        t=t.replace('href="/"',f'href="{BASE}/"')
        t=t.replace('"./data/',f'"{BASE}/data/').replace("'./data/",f"'{BASE}/data/")
        t=t.replace('"./assets/data/',f'"{BASE}/data/').replace("'./assets/data/",f"'{BASE}/data/")
        t=t.replace('&#34;./data/',f'&#34;{BASE}/data/').replace('&quot;./data/',f'&quot;{BASE}/data/')
        if t!=s: p.write_text(t); n+=1
    print("rewrote",n,"files")
if __name__=="__main__": main()
