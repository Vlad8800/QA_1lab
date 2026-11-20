"""Run real local checks and preserve their output without inventing PASS states."""
from pathlib import Path
import subprocess,sys,json,os,time

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'Lab11/evidence';EVIDENCE.mkdir(parents=True,exist_ok=True)
def run(name,args):
    proc=subprocess.run(args,cwd=ROOT,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=180)
    output=proc.stdout+proc.stderr
    (EVIDENCE/(name+'.log')).write_text('$ '+' '.join(args)+'\n'+output+'\nExit Code: '+str(proc.returncode)+'\n',encoding='utf-8')
    print(name,proc.returncode,flush=True)
    return proc.returncode

if __name__=='__main__':
    results={}
    for name,args in [
        ('review-dates',[sys.executable,'scripts/check_review_dates.py']),
        ('structure',[sys.executable,'scripts/check_docs_structure.py']),
        ('review-policy-tests',[sys.executable,'scripts/test_review_policy.py']),
        ('contract-boundary-tests',[sys.executable,'scripts/test_contract_boundary.py']),
        ('spectral',['node','node_modules/@stoplight/spectral-cli/dist/index.js','lint','docs/api/openapi.yaml','--fail-severity','warn']),
        ('markdownlint',['node','node_modules/markdownlint-cli2/markdownlint-cli2.mjs']),
        ('strict-build',[sys.executable,'-m','mkdocs','build','--strict'])
    ]:
        try:results[name]=run(name,args)
        except Exception as exc:results[name]='BLOCKED: '+str(exc)
    api_log=(EVIDENCE/'api-server.log').open('w',encoding='utf-8')
    server=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000'],cwd=ROOT,stdout=api_log,stderr=subprocess.STDOUT)
    try:
        ready=run('api-startup',[sys.executable,'scripts/wait_api.py'])
        results['api-startup']=ready
        if ready==0:
            results['live-contract-shapes']=run('live-contract-shapes',[sys.executable,'scripts/check_contract_shapes.py'])
            results['live-contract']=run('live-contract',[sys.executable,'scripts/check_contract.py'])
    finally:
        server.terminate()
        try:server.wait(timeout=10)
        except subprocess.TimeoutExpired:server.kill();server.wait()
        api_log.close()
    (EVIDENCE/'checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    raise SystemExit(0 if all(x==0 for x in results.values()) else 1)
