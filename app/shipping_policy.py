"""Load the deployment-owned shipping policy descriptor before API startup."""
import json
import os
from pathlib import Path


def load_shipping_policy(path=None):
    policy_path = Path(path or os.environ.get('SHIPPING_POLICY_FILE', 'runtime/shipping-policy.json'))
    try:
        policy = json.loads(policy_path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise RuntimeError('Prepare a valid shipping policy file before starting API: ' + str(policy_path)) from exc
    if not isinstance(policy, dict) or policy.get('schema_version') != '1.0' or not isinstance(policy.get('policy_version'), str) or not policy['policy_version'].strip():
        raise RuntimeError('Shipping policy requires schema_version=1.0 and nonempty policy_version')
    return {'schema_version': policy['schema_version'], 'policy_version': policy['policy_version']}
