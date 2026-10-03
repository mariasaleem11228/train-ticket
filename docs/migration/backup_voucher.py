"""Save the live Voucher table before changing its writer."""
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
backup = root/'deployment/migration/.state/backups/voucher.sql'
backup.parent.mkdir(parents=True,exist_ok=True)
data = subprocess.check_output(['docker','exec','train-ticket-ts-voucher-mysql-1',
                                'mysqldump','-uroot','-proot','--set-gtid-purged=OFF',
                                '--single-transaction','voucherservice'])
if b'CREATE TABLE `voucher`' not in data:
    raise RuntimeError('Voucher table absent from backup')
backup.write_bytes(data)
print('Voucher MySQL table backup saved:',backup,'bytes:',len(data))
