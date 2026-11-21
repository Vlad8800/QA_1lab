"""Configuration-only restore drill in a temporary directory."""
import hashlib
import json
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.shipping_policy import load_shipping_policy

def main():
    start=time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='qa1lab-restore-') as directory:
        root=Path(directory)
        original=Path('config/shipping-policy.example.json')
        backup=root/'backup.json'; restored=root/'restored.json'
        shutil.copy2(original,backup)
        expected=hashlib.sha256(backup.read_bytes()).hexdigest()
        restored.write_text('broken',encoding='utf-8')
        shutil.copy2(backup,restored)
        assert hashlib.sha256(restored.read_bytes()).hexdigest()==expected
        policy=load_shipping_policy(restored)
        backup.write_text('corrupted',encoding='utf-8')
        corruption_detected=hashlib.sha256(backup.read_bytes()).hexdigest()!=expected
        assert corruption_detected
    elapsed=time.perf_counter()-start
    result={'utc':datetime.now(timezone.utc).isoformat(),'scope':'configuration only; not RAM user data','status':'PASS','sha256':expected,'policy':policy,'corruption_detected':corruption_detected,'elapsed_seconds':elapsed,'rto_target_seconds':900,'within_rto':elapsed<900,'offsite_encryption_exercised':False}
    p=Path('Lab12/evidence/restore-drill.json');p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
