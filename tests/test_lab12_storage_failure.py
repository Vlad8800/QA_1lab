"""Regressions for both export aliases, security and recovery after store failure."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.export.repository import UserDataRepository

@pytest.mark.parametrize('prefix',['/api/users','/api/v1/users'])
def test_storage_failure_is_retryable_without_leak(prefix):
    client=TestClient(app,raise_server_exceptions=False)
    url=f'{prefix}/usr_101/personal-data'
    with patch.object(UserDataRepository,'get_user_by_id',side_effect=OSError('secret-store-password')):
        assert client.get(url).status_code==401
        assert client.get(url,headers={'X-Actor-ID':'usr_102'}).status_code==403
        response=client.get(url,headers={'X-Actor-ID':'usr_101'})
        assert response.status_code==503
        assert response.headers['retry-after']=='30'
        assert response.json()=={'detail':'Personal data store temporarily unavailable'}
        assert 'secret-store-password' not in response.text
    recovered=client.get(url,headers={'X-Actor-ID':'usr_101'})
    assert recovered.status_code==200
    assert 'password_hash' not in recovered.text
