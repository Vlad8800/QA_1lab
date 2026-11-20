"""Validate the API-first contract against live HTTP responses and error cases."""
from pathlib import Path
import argparse, json, sys
import httpx, yaml
from jsonschema import Draft202012Validator, RefResolver
from openapi_spec_validator import validate

ROOT=Path(__file__).resolve().parents[1]

def run(base):
    spec=yaml.safe_load((ROOT/'docs/api/openapi.yaml').read_text(encoding='utf-8'))
    validate(spec)
    resolver=RefResolver.from_schema(spec)
    cases=[('GET','/api/v1/shipping/policy',None,200),
           ('POST','/api/v1/orders/calculate',spec['components']['schemas']['OrderRequest']['example'],200),
           ('POST','/api/policy-gate/check',spec['components']['schemas']['PolicyGateRequest']['example'],200),
           ('POST','/api/v1/orders/calculate',{},422),
           ('POST','/api/policy-gate/check',{'user_id':'demo-user','purpose':'INVALID'},422)]
    results=[]
    with httpx.Client(base_url=base,timeout=10,trust_env=False) as client:
        for method,path,payload,status in cases:
            response=client.request(method,path,**({'json':payload} if payload is not None else {}))
            assert response.status_code==status,(path,response.status_code,response.text)
            schema=spec['paths'][path][method.lower()]['responses'][str(status)]['content']['application/json']['schema']
            data=response.json();Draft202012Validator(schema,resolver=resolver).validate(data)
            if path.endswith('/calculate') and status==200:
                assert data['subtotal']==50 and data['final_total']==52, data
            if path.endswith('/check') and status==200:
                assert data['decision']=='DENY',data
            results.append({'method':method,'path':path,'status':status,'result':'PASS','response':data})
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base-url',default='http://127.0.0.1:8000');args=parser.parse_args()
    print(json.dumps(run(args.base_url),ensure_ascii=False,indent=2))
