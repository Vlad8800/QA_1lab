import json
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('shipping_policy_unit', Path(__file__).parents[1] / 'app/shipping_policy.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_missing_policy_blocks_startup(tmp_path):
    with pytest.raises(RuntimeError, match='before starting API'):
        module.load_shipping_policy(tmp_path / 'missing.json')


def test_policy_returns_only_public_descriptor(tmp_path):
    path = tmp_path / 'policy.json'
    path.write_text(json.dumps({'schema_version':'1.0','policy_version':'demo','extra':'not exported'}))
    assert module.load_shipping_policy(path) == {'schema_version':'1.0','policy_version':'demo'}


@pytest.mark.parametrize('value', ['invalid json', '{"schema_version":"2.0","policy_version":"demo"}', '{"schema_version":"1.0","policy_version":""}'])
def test_invalid_policy_blocks_startup(tmp_path, value):
    path = tmp_path / 'policy.json'
    path.write_text(value)
    with pytest.raises(RuntimeError):
        module.load_shipping_policy(path)
