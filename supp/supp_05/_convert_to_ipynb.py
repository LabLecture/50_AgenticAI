# -*- coding: utf-8 -*-
"""supp_05 m*.py -> .ipynb 변환 + supp/venv 실행(출력 임베딩).
m05_gradio_app 는 demo.launch() 가 블로킹이라 실행 제외(노트북 구조만 생성)."""
import glob, re, os
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
from nbclient import NotebookClient

HERE = os.path.dirname(os.path.abspath(__file__))
import sys as _s
SKIP_EXEC = {"m05_gradio_app"}   # 대화형 웹서버 — 실행 시 무한 블로킹
pys = sorted(p for p in glob.glob(os.path.join(HERE, "m[0-9]*.py")) if not os.path.basename(p).startswith("_"))
if len(_s.argv) > 1:
    only = set(_s.argv[1:])
    pys = [p for p in pys if os.path.basename(p) in only or os.path.basename(p)[:-3] in only]

def docstring_of(src):
    m = re.match(r'\s*(?:#[^\n]*\n)*\s*("""|\'\'\')(.*?)\1', src, re.S)
    return (m.group(2).strip() if m else "")

results = []
for p in pys:
    name = os.path.basename(p); stem = name[:-3]
    src = open(p, encoding="utf-8").read(); doc = docstring_of(src)
    setup = (f"import os, sys, ssl, certifi\n"
             f"ssl.SSLContext.load_default_certs = lambda self, *a, **k: self.load_verify_locations(certifi.where())\n"
             f"import nest_asyncio; nest_asyncio.apply()\n"
             f"__file__ = os.path.join(os.getcwd(), {name!r})\n"
             f"sys.path.insert(0, os.path.abspath('..'))")
    cells = [new_markdown_cell(f"# {stem}\n\n{doc}" if doc else f"# {stem}"),
             new_code_cell(setup), new_code_cell(src.rstrip("\n"))]
    nb = new_notebook(cells=cells,
        metadata={"kernelspec": {"display_name": "Python 3 (supp)", "language": "python", "name": "python3"},
                  "language_info": {"name": "python"}})
    out = os.path.join(HERE, stem + ".ipynb")
    if stem in SKIP_EXEC:
        nb.cells[0]["source"] += "\n\n> ⚠️ **대화형 Gradio 앱** — `demo.launch()` 가 블로킹이라 노트북 자동 실행에서 제외. `python m05_gradio_app.py` 로 직접 구동(http://127.0.0.1:7860)."
        nbformat.write(nb, out); results.append((name, "SKIP(interactive)", 0))
        print(f"  {name:32s} SKIP(interactive)", flush=True); continue
    try:
        NotebookClient(nb, timeout=600, kernel_name="python3",
                       resources={"metadata": {"path": HERE}}).execute()
        status = "OK"
    except Exception as e:
        status = f"ERR:{type(e).__name__}:{str(e)[:60]}"
    errs = sum(1 for c in nb.cells if c.cell_type=="code" for o in c.outputs if o.get("output_type")=="error")
    nbformat.write(nb, out); results.append((name, status, errs))
    print(f"  {name:32s} {status}  cell_errs={errs}", flush=True)

print("\n=== 요약 ===")
ok = sum(1 for _,s,e in results if e==0)
print(f"  무오류: {ok}/{len(results)}")
for n,s,e in results:
    if e: print(f"  WARN {n}: {s} (err={e})")
