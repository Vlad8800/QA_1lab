"""Validate document ownership, lifecycle and next review date; never silently rewrite."""
from pathlib import Path
from datetime import date
import argparse
import json
import sys
import yaml

ROOT=Path(__file__).resolve().parents[1]

def audit(today):
    errors=[]; overdue=[]; deprecated=[]; count=0
    paths=[ROOT/'README.md',ROOT/'CONTRIBUTING.md',ROOT/'CHANGELOG.md',*sorted((ROOT/'docs').rglob('*.md'))]
    for p in paths:
        count+=1; rel=p.relative_to(ROOT).as_posix(); text=p.read_text(encoding='utf-8')
        if not text.startswith('---\n'):
            errors.append(rel+': missing YAML front matter'); continue
        try:
            meta=yaml.safe_load(text.split('---',2)[1])
            assert meta.get('owner') and meta.get('status') in {'draft','in-review','published','deprecated'}
            review=date.fromisoformat(str(meta['review_date']))
            if meta['status']=='deprecated':
                replacement=meta.get('replacement')
                if not replacement or not (p.parent/replacement).is_file():
                    errors.append(rel+': deprecated requires existing replacement')
                deprecated.append({'document':rel,'replacement':replacement})
            elif review<today:overdue.append({'document':rel,'review_date':str(review)})
        except (ValueError,KeyError,AssertionError,TypeError,yaml.YAMLError) as exc:
            errors.append(rel+': invalid passport '+str(exc))
    return {'date':str(today),'checked':count,'overdue':overdue,'deprecated':deprecated,'errors':errors}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--today',default=str(date.today()));args=parser.parse_args()
    result=audit(date.fromisoformat(args.today));print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(1 if result['errors'] or result['overdue'] else 0)
