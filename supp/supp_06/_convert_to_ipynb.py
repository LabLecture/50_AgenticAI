# -*- coding: utf-8 -*-
"""supp_06 .py -> .ipynb 변환 + supp/venv 실행(출력 임베딩).
노트북엔 __file__ 없으므로 setup 셀 주입. .cypher/.sh 는 대상 아님(파이썬만)."""
import glob, re, os
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
from nbclient import NotebookClient

HERE = os.path.dirname(os.path.abspath(__file__))
import sys as _s
pys = sorted(p for p in glob.glob(os.path.join(HERE, "[0-9]*.py")) if not os.path.basename(p).startswith("_"))
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
             f"# Windows 인증서 저장소 손상 우회(임베딩/HTTPS 로드 SSL 에러 방지)\n"
             f"ssl.SSLContext.load_default_certs = lambda self, *a, **k: self.load_verify_locations(certifi.where())\n"
             f"# 노트북 커널엔 이미 이벤트 루프가 돌아 스크립트의 asyncio.run() 이 깨짐 → nest_asyncio 로 중첩 허용\n"
             f"import nest_asyncio; nest_asyncio.apply()\n"
             f"# 노트북 커널엔 __file__ 이 없으므로 스크립트 호환 위해 정의 + supp/ 를 import 경로에 추가\n"
             f"__file__ = os.path.join(os.getcwd(), {name!r})\n"
             f"sys.path.insert(0, os.path.abspath('..'))")
    nb = new_notebook(cells=[
        new_markdown_cell(f"# {stem}\n\n{doc}" if doc else f"# {stem}"),
        new_code_cell(setup),
        new_code_cell(src.rstrip("\n")),
    ], metadata={"kernelspec": {"display_name": "Python 3 (supp)", "language": "python", "name": "python3"},
                 "language_info": {"name": "python"}})
    out = os.path.join(HERE, stem + ".ipynb")
    try:
        NotebookClient(nb, timeout=900, kernel_name="python3",
                       resources={"metadata": {"path": HERE}}).execute()
        status = "OK"
    except Exception as e:
        status = f"ERR:{type(e).__name__}:{str(e)[:60]}"
    errs = sum(1 for c in nb.cells if c.cell_type=="code" for o in c.outputs if o.get("output_type")=="error")
    nbformat.write(nb, out); results.append((name, status, errs))
    print(f"  {name:32s} {status}  cell_errs={errs}", flush=True)

print("\n=== 요약 ===")
ok = sum(1 for _,s,e in results if e==0)
print(f"  성공(에러0): {ok}/{len(results)}")
for n,s,e in results:
    if e: print(f"  WARN {n}: {s} (err={e})")
