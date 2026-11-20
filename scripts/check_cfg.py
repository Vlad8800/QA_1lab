"""Count nodes and edges in the Lab 6 Mermaid control flow graphs."""

import re
from pathlib import Path


for path in sorted(Path("docs/lab6").glob("cfg-*.mmd")):
    source = path.read_text(encoding="utf-8")
    nodes = set(re.findall(r"\b([A-Za-z]\w*)(?=[\[\{(])", source))
    edges = source.count("-->")
    print(f"{path.name}: V={len(nodes)}, E={edges}, CC=E-V+2={edges-len(nodes)+2}")
