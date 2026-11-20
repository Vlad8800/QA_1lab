"""Resolve Obsidian wikilinks and publish root-owned pages from one source."""
from pathlib import Path
import re
import posixpath

ROOT = Path(__file__).resolve().parents[1]

def on_page_markdown(markdown, page, config, files, **kwargs):
    if page.file.src_uri == 'developer/contributing.md':
        markdown=(ROOT/'CONTRIBUTING.md').read_text(encoding='utf-8')
        markdown=re.sub(r'^---\n.*?\n---\n', '', markdown, count=1, flags=re.S)
    def link(match):
        target, _, label=match.group(1).partition('|')
        path=target+'.md'
        if not (ROOT/'docs'/path).is_file():
            raise ValueError('Unresolved wikilink: '+target)
        rel=posixpath.relpath(path,posixpath.dirname(page.file.src_uri) or '.')
        return '['+(label or target)+']('+rel+')'
    markdown=canonical_links(markdown,page.file.src_uri)
    return re.sub(r'\[\[([^\]]+)\]\]',link,markdown)

def on_post_page(output, page, config, **kwargs):
    """Old document addresses redirect while preserving an auditable source stub."""
    if page.meta.get('status') == 'deprecated' and page.meta.get('replacement'):
        target=posixpath.normpath(posixpath.join(posixpath.dirname(page.file.src_uri),page.meta['replacement']))
        target_url=target.removesuffix('.md')+'/'
        current=posixpath.dirname(page.file.dest_uri)
        relative=posixpath.relpath(target_url,current or '.')+'/'
        output=output.replace('</head>',f'<meta http-equiv="refresh" content="0; url={relative}"></head>')
    return output


def canonical_links(markdown, src_uri):
    """Resolve legacy document links for the site, retaining immutable source ADRs."""
    from urllib.parse import urlsplit, unquote, quote
    def replace(match):
        label,target=match.group(1),match.group(2)
        url=urlsplit(target)
        if url.scheme or url.netloc or not url.path:
            return match.group(0)
        path=posixpath.normpath(posixpath.join(posixpath.dirname(src_uri),unquote(url.path)))
        fragment=url.fragment
        if path in {'sdd.md','isd.md'}:
            path='architecture/'+path
        elif path=='index.md' and fragment:
            path='developer/local.md' if 'quick-start' in fragment else 'developer/index.md'
            fragment=''
        if path.startswith('../'):
            target='https://github.com/Vlad8800/QA_1lab/blob/lab11-documentation-as-code/'+quote(path[3:],safe='/')
        elif path.startswith(('lab6/','lab7/','lab10/')):
            target='https://github.com/Vlad8800/QA_1lab/blob/lab11-documentation-as-code/docs/'+quote(path,safe='/')
        else:
            target=posixpath.relpath(path,posixpath.dirname(src_uri) or '.')
        if fragment:target+='#'+fragment
        return '['+label+']('+target+')'
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',replace,markdown)
