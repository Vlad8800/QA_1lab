"""Isolated storage fault injection. No production process or repository is modified."""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.export.repository import UserDataRepository

def now():
    return datetime.now(timezone.utc).isoformat()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['FAIL','PASS'], required=True)
    args=parser.parse_args()
    start=time.perf_counter()
    result={'phase':args.phase,'scope':'isolated ASGI TestClient; repository read fault; no production users','started_utc':now(),'timeline':[],'requests':[]}
    def record(event):
        result['timeline'].append({'utc':now(),'event':event})
    client=TestClient(app,raise_server_exceptions=False)
    path='/api/v1/users/usr_101/personal-data'
    headers={'X-Actor-ID':'usr_101'}
    record('baseline probe')
    assert client.get(path,headers=headers).status_code==200
    record('block repository reads using OSError injection')
    with patch.object(UserDataRepository,'get_user_by_id',side_effect=OSError('simulated store unavailable')):
        for i in range(5):
            t=time.perf_counter()
            response=client.get(path,headers=headers)
            result['requests'].append({'utc':now(),'status':response.status_code,'duration_ms':round((time.perf_counter()-t)*1000,3),'retry_after':response.headers.get('retry-after'),'pii_in_error':any(s in response.text for s in ['password_hash','oleksandr.kovalenko','simulated store unavailable'])})
        record('fault observed; no automatic restart of live API')
    record('restore dependency by exiting isolated fault context')
    result['recovery_statuses']=[client.get(path,headers=headers).status_code for _ in range(3)]
    record('three recovery probes complete')
    result['finished_utc']=now()
    result['elapsed_seconds']=round(time.perf_counter()-start,6)
    result['affected_requests']=sum(r['status']>=500 for r in result['requests'])
    result['affected_subjects']=1
    result['production_sla_breach']='not inferred; isolated drill, not a 30-day production window'
    expected=500 if args.phase=='FAIL' else 503
    assert all(r['status']==expected for r in result['requests']),result
    assert result['recovery_statuses']==[200]*3
    if args.phase=='PASS':
        assert all(r['retry_after']=='30' and not r['pii_in_error'] for r in result['requests'])
    p=Path('Lab12/evidence')/(args.phase+'.json');p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
