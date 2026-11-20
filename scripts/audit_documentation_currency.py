"""Read-only, experiment-scoped documentation audit; not a universal semantic verifier."""
import argparse
import datetime
import json
import subprocess
from pathlib import Path


def git(*args):
    return subprocess.check_output(['git', *args]).decode('utf-8-sig').strip()


def _contains_tokens(document, tokens):
    return all(token in document for token in tokens)


def _documentation_checks(docs, changed):
    rules = {
        'readme_user_behavior': ('README.md', ('/api/v1/shipping/policy',)),
        'readme_startup': ('README.md', ('shipping-policy.example.json',)),
        'sdd_contract_and_component': ('docs/sdd.md', ('/api/v1/shipping/policy', 'shipping_policy.py', 'ContainerDb(policyfile')),
        'isd_provision_before_api': ('docs/isd.md', ('shipping-policy.example.json', 'SHIPPING_POLICY_FILE')),
    }
    if not changed:
        return dict.fromkeys(rules, True)
    return {name: _contains_tokens(docs[path], tokens) for name, (path, tokens) in rules.items()}


def audit(ref):
    docs={p:git('show',ref+':'+p) for p in ['README.md','docs/sdd.md','docs/isd.md']}
    source=git('show',ref+':app/main.py')
    changed='/api/v1/shipping/policy' in source
    checks=_documentation_checks(docs,changed)
    metrics=[]
    for p in docs:
        date=git('log','-1','--format=%cs',ref,'--',p)
        sha=git('log','-1','--format=%H',ref,'--',p)
        nc=int(git('rev-list','--count',ref,'--','app'))
        nd=int(git('rev-list','--count',ref,'--',p))
        metrics.append({'document':p,'last_updated':date,'age_days':(datetime.date(2026,11,15)-datetime.date.fromisoformat(date)).days,'code_commits':nc,'doc_commits':nd,'ratio':round(nc/nd,2),'code_commits_since_doc':int(git('rev-list','--count',sha+'..'+ref,'--','app'))})
    return {'ref':git('rev-parse',ref),'as_of':'2026-11-15','policy_component_present':changed,'checks':checks,'status':'PASS' if all(checks.values()) else 'FAIL','metrics':metrics}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--ref',default='HEAD')
    parser.add_argument('--output')
    args=parser.parse_args()
    result=audit(args.ref)
    value=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:
        path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(value,encoding='utf8')
    print(value)
    raise SystemExit(0 if result['status']=='PASS' else 1)
