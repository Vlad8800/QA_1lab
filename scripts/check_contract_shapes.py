"""Dependency-free live smoke check of the JSON Schema keywords used by this contract.

This complements, rather than replaces, the full OpenAPI/jsonschema CI validator.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import json

ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/'docs/api/openapi.yaml').read_text(encoding='utf-8'))

def _resolve_schema(schema):
    if '$ref' in schema:
        return SPEC['components']['schemas'][schema['$ref'].rsplit('/', 1)[1]]
    return schema


def _type_matches(value):
    return {
        'object': isinstance(value, dict),
        'array': isinstance(value, list),
        'string': isinstance(value, str),
        'number': isinstance(value, (int, float)) and not isinstance(value, bool),
        'integer': isinstance(value, int) and not isinstance(value, bool),
        'boolean': isinstance(value, bool),
        'null': value is None,
    }


def _check_type(value, schema):
    types = schema.get('type', [])
    if isinstance(types, str):
        types = [types]
    matches = _type_matches(value)
    assert not types or any(matches[t] for t in types), (types, value)


def _check_enum(value, schema):
    if 'enum' in schema:
        assert value in schema['enum'], value


def _check_object(value, schema):
    if not isinstance(value, dict):
        return
    assert all(key in value for key in schema.get('required', [])), value
    for key, child_schema in schema.get('properties', {}).items():
        if key in value:
            shape(value[key], child_schema)


def _check_array(value, schema):
    if isinstance(value, list):
        for item in value:
            shape(item, schema.get('items', {}))


def _check_bounds(value, schema):
    if isinstance(value, str) and 'minLength' in schema:
        assert len(value) >= schema['minLength']
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        if 'minimum' in schema:
            assert value >= schema['minimum']
        if 'exclusiveMinimum' in schema:
            assert value > schema['exclusiveMinimum']


def shape(value, schema):
    schema = _resolve_schema(schema)
    _check_type(value, schema)
    _check_enum(value, schema)
    _check_object(value, schema)
    _check_array(value, schema)
    _check_bounds(value, schema)

if __name__=='__main__':
    cases=[('GET','/api/v1/shipping/policy',None,200),('POST','/api/v1/orders/calculate',SPEC['components']['schemas']['OrderRequest']['example'],200),('POST','/api/policy-gate/check',SPEC['components']['schemas']['PolicyGateRequest']['example'],200),('POST','/api/v1/orders/calculate',{},422),('POST','/api/policy-gate/check',{'user_id':'demo-user','purpose':'INVALID'},422)]
    result=[]
    for method,path,body,expected in cases:
        request=Request('http://127.0.0.1:8000'+path,method=method,headers={'Content-Type':'application/json'},data=json.dumps(body).encode() if body is not None else None)
        try:
            with urlopen(request,timeout=10) as response:status=response.status;data=json.load(response)
        except HTTPError as response:status=response.code;data=json.load(response)
        assert status==expected,(path,status,data)
        schema=SPEC['paths'][path][method.lower()]['responses'][str(status)]['content']['application/json']['schema']
        shape(data,schema)
        if path.endswith('/calculate') and status==200:assert data['final_total']==52 and data['subtotal']==50
        result.append({'method':method,'path':path,'status':status,'result':'PASS','response':data})
    print(json.dumps({'validator':'local subset: type, required, enum, properties, items, bounds; full OpenAPI CI validation remains separate','checks':result},ensure_ascii=False,indent=2))
