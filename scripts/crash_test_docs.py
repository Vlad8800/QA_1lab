"""Record an actual local strict-build FAIL/PASS experiment in separate commits."""
from pathlib import Path
import subprocess,sys,json,argparse

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'Lab11/evidence'
def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()
def build(name,structure_only=False):
    args=[sys.executable,'scripts/check_docs_structure.py'] if structure_only else [sys.executable,'-m','mkdocs','build','--strict']
    p=subprocess.run(args,cwd=ROOT,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=180)
    log=p.stdout+p.stderr
    (EVIDENCE/(name+'.log')).write_text(log+'\nExit Code: '+str(p.returncode)+'\n',encoding='utf-8')
    return p.returncode

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--structure-only',action='store_true',help='Preflight fallback; does not claim a MkDocs strict result');args=parser.parse_args()
    mode='structure' if args.structure_only else 'strict'
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    assert not git('status','--porcelain'),'Commit baseline changes first'
    baseline=git('rev-parse','HEAD')
    assert build('baseline-'+mode,args.structure_only)==0,'Baseline must pass before injecting a defect'
    page=ROOT/'docs/index.md';clean=page.read_text(encoding='utf-8')
    page.write_text(clean+'\n[Controlled broken reference](missing-lab11-page.md)\n',encoding='utf-8')
    git('add','docs/index.md')
    git('commit','-m','docs(ci): inject broken reference into strict build, FAIL')
    fail=git('rev-parse','HEAD')
    (EVIDENCE/'fail.diff').write_text(git('show','--format=fuller',fail,'--','docs/index.md')+'\n',encoding='utf-8')
    fail_exit=build('fail-'+mode,args.structure_only)
    page.write_text(clean,encoding='utf-8')
    if fail_exit!=1:raise SystemExit('Expected real strict-build Exit Code 1, got '+str(fail_exit))
    assert build('pass-'+mode,args.structure_only)==0,'Restored page must pass cleanly'
    git('add','docs/index.md')
    git('commit','-m','docs(ci): restore strict build pipeline, PASS')
    passed=git('rev-parse','HEAD')
    (EVIDENCE/'pass.diff').write_text(git('show','--format=fuller',passed,'--','docs/index.md')+'\n',encoding='utf-8')
    scope='local structure/link preflight only; MkDocs strict and GitHub Actions NOT verified' if args.structure_only else 'local MkDocs strict build, not GitHub Actions'
    (EVIDENCE/'crash-test.json').write_text(json.dumps({'scope':scope,'baseline':baseline,'fail':fail,'fail_exit':fail_exit,'pass':passed,'pass_exit':0},indent=2),encoding='utf-8')
    print('Local FAIL -> PASS verified',fail,passed)
