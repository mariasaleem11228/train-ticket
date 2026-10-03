"""Back up the live Notification Mongo database before cutover."""
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
target=root/'deployment/migration/.state/backups/notification.archive'
target.parent.mkdir(parents=True,exist_ok=True)
archive=subprocess.check_output(['docker','exec','migration-infra-notification-mongo-1',
                                 'mongodump','--db','ts','--archive'])
target.write_bytes(archive)
print('Notification Mongo backup:',target,'bytes:',len(archive))
