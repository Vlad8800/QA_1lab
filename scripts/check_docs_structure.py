"""Check navigation, local document targets and Obsidian graph connectivity."""
from pathlib import Path
import re,json,posixpath
from urllib.parse import unquote,urlsplit
import yaml

ROOT=Path(__file__).resolve().parents[1]
class ConfigLoader(yaml.SafeLoader):
    pass
# Inspect MkDocs' named formatter without importing or executing the Python name.
ConfigLoader.add_multi_constructor('tag:yaml.org,2002:python/name:',lambda loader,suffix,node:suffix)
config=yaml.load((ROOT/'mkdocs.yml').read_text(encoding='utf-8'),Loader=ConfigLoader)
docs=ROOT/'docs';errors=[]
def values(node):
    if isinstance(node,str):yield node
    elif isinstance(node,list):
        for child in node:yield from values(child)
    elif isinstance(node,dict):
        for child in node.values():yield from values(child)
nav=set(values(config['nav']))
pages={p.relative_to(docs).as_posix():p for p in docs.rglob('*.md') if not any(x in p.relative_to(docs).parts for x in ['lab6','lab7','lab10'])}
edges={name:set() for name in pages}
for name,p in pages.items():
    if name not in nav:errors.append('Orphan: '+name)
    text=p.read_text(encoding='utf-8')
    targets=re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)',text)
    targets+= [posixpath.relpath(x.split('|')[0]+'.md',posixpath.dirname(name) or '.') for x in re.findall(r'\[\[([^\]]+)\]\]',text)]
    for target in targets:
        url=urlsplit(target)
        if url.scheme or url.netloc or not url.path:continue
        path=unquote(url.path)
        resolved=(p.parent/path).resolve()
        if not resolved.exists():errors.append(name+': missing '+target)
        elif resolved.suffix=='.md':
            try:
                other=resolved.relative_to(docs.resolve()).as_posix()
                if other in pages:edges[name].add(other);edges[other].add(name)
            except ValueError:pass
for name in nav:
    if name not in pages:errors.append('Missing nav target: '+name)
seen=set();pending=['index.md']
while pending:
    name=pending.pop()
    if name not in seen:seen.add(name);pending.extend(edges.get(name,set())-seen)
isolated=sorted(set(pages)-seen)
if isolated:errors.append('Disconnected graph pages: '+', '.join(isolated))
print(json.dumps({'pages':len(pages),'nav':len(nav),'connected':len(seen),'errors':errors},ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
