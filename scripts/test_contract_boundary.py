"""Verify shared errors, CORS and the contract's single source against the app."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app.main import app

class ContractBoundaryTests(unittest.TestCase):
    def setUp(self):self.client=TestClient(app,raise_server_exceptions=False)

    def test_published_contract_is_the_source_file(self):
        expected=json.loads((Path(__file__).resolve().parents[1]/'docs/api/openapi.yaml').read_text(encoding='utf-8'))
        response=self.client.get('/contract/openapi.json')
        self.assertEqual(200,response.status_code)
        self.assertEqual(expected,response.json())

    def test_invalid_request_uses_common_error(self):
        response=self.client.post('/api/v1/orders/calculate',json={})
        self.assertEqual(422,response.status_code)
        self.assertEqual({'code':'VALIDATION_ERROR','detail':'Request validation failed'},response.json())

    def test_unexpected_error_does_not_expose_internal_details(self):
        with patch('app.main.calculate_shipping_cost',side_effect=RuntimeError('private internals')):
            response=self.client.post('/api/v1/orders/calculate',json={'items':[{'name':'Mouse','price':25,'quantity':2}]})
        self.assertEqual(500,response.status_code)
        self.assertEqual({'code':'INTERNAL_ERROR','detail':'Internal server error'},response.json())

    def test_documentation_origin_is_allowed(self):
        response=self.client.options('/api/v1/orders/calculate',headers={'Origin':'http://127.0.0.1:8001','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type'})
        self.assertEqual(200,response.status_code)
        self.assertEqual('http://127.0.0.1:8001',response.headers['access-control-allow-origin'])

if __name__=='__main__':unittest.main()
