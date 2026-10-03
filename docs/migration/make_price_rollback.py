"""Build a Price rollback image with its startup sample writer removed."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import subprocess

root=Path(__file__).resolve().parents[2]
folder=root/'ts-modulith/target/legacy-price-rollback'
folder.mkdir(parents=True,exist_ok=True)
source=root/'ts-modulith/target/legacy-price.jar'
output=folder/'rollback.jar'
initializer='BOOT-INF/classes/price/init/InitData.class'
with ZipFile(source) as original,ZipFile(output,'w') as patched:
    assert initializer in original.namelist()
    for entry in original.infolist():
        if entry.filename!=initializer:patched.writestr(entry,original.read(entry.filename))
with ZipFile(source) as original,ZipFile(output) as patched:
    assert set(original.namelist())-{initializer}==set(patched.namelist())
    assert all(original.read(name)==patched.read(name) for name in patched.namelist())
(folder/'Dockerfile.rollback').write_text('''FROM codewisdom/ts-price-service@sha256:PLACEHOLDER
COPY rollback.jar /app/ts-price-service-1.0.jar
'''.replace('PLACEHOLDER',subprocess.check_output(
    ['docker','image','inspect','codewisdom/ts-price-service:0.2.0','--format','{{index .RepoDigests 0}}'],
    text=True).strip().split('@sha256:')[1]))
subprocess.run(['docker','build','-f',str(folder/'Dockerfile.rollback'),'-t',
                'train-ticket/price-legacy-no-seed:0.2.0',str(folder)],check=True)
report={'original_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'rollback_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'removed_class':initializer}
evidence=root/'ts-modulith/target/evidence';evidence.mkdir(parents=True,exist_ok=True)
(evidence/'price-rollback-image.json').write_text(json.dumps(report,indent=2))
print('Price rollback image built; only startup sample writer removed')
