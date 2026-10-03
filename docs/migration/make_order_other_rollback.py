"""Build a local legacy rollback image without its startup sample-order writer."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import subprocess

root=Path(__file__).resolve().parents[2]
folder=root/'ts-modulith/target/legacy-order-other'
source=folder/'order-other.jar'
output=folder/'rollback.jar'
initializer='BOOT-INF/classes/other/init/InitData.class'
with ZipFile(source) as original,ZipFile(output,'w') as patched:
    assert initializer in original.namelist()
    for entry in original.infolist():
        if entry.filename!=initializer:patched.writestr(entry,original.read(entry.filename))
with ZipFile(source) as original,ZipFile(output) as patched:
    assert set(original.namelist())-{initializer}==set(patched.namelist())
    assert all(original.read(name)==patched.read(name) for name in patched.namelist())
(folder/'Dockerfile.rollback').write_text('''FROM codewisdom/ts-order-other-service@sha256:4306fe9da9e5494fa34afcb63a83db4d2c60da139187aa18eb09e5e3b33484d8
COPY rollback.jar /app/ts-order-other-service-1.0.jar
''')
subprocess.run(['docker','build','-f',str(folder/'Dockerfile.rollback'),'-t','train-ticket/order-other-legacy-no-seed:0.2.0',str(folder)],check=True)
report={'original_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'rollback_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'removed_class':initializer}
(root/'ts-modulith/target/evidence/order-other-rollback-image.json').write_text(json.dumps(report,indent=2))
print('Rollback image built; only OrderOther startup sample writer removed')
