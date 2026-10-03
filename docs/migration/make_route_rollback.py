"""Build a Route rollback image with its startup sample writer removed."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import subprocess

root=Path(__file__).resolve().parents[2]
folder=root/'ts-modulith/target/legacy-route-rollback'
folder.mkdir(parents=True,exist_ok=True)
source=root/'ts-modulith/target/legacy-route.jar'
output=folder/'rollback.jar'
initializer='BOOT-INF/classes/route/init/InitData.class'
with ZipFile(source) as original,ZipFile(output,'w') as patched:
    assert initializer in original.namelist()
    for entry in original.infolist():
        if entry.filename!=initializer:patched.writestr(entry,original.read(entry.filename))
with ZipFile(source) as original,ZipFile(output) as patched:
    assert set(original.namelist())-{initializer}==set(patched.namelist())
    assert all(original.read(name)==patched.read(name) for name in patched.namelist())
(folder/'Dockerfile.rollback').write_text('''FROM codewisdom/ts-route-service@sha256:fc5947172659ad347c6ed56e1b825ee58cb6221aa9ab34b77eb727e232dbbbd5
COPY rollback.jar /app/ts-route-service-1.0.jar
''')
subprocess.run(['docker','build','-f',str(folder/'Dockerfile.rollback'),'-t',
                'train-ticket/route-legacy-no-seed:0.2.0',str(folder)],check=True)
report={'original_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'rollback_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'removed_class':initializer}
evidence=root/'ts-modulith/target/evidence'
evidence.mkdir(parents=True,exist_ok=True)
(evidence/'route-rollback-image.json').write_text(json.dumps(report,indent=2))
print('Route rollback image built; only startup sample writer removed')
