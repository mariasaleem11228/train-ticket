"""Build a Travel2 rollback image with its startup sample-trip seeder removed."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import subprocess

root = Path(__file__).resolve().parents[2]
folder = root / 'ts-modulith/target/legacy-travel2-rollback'
folder.mkdir(parents=True, exist_ok=True)
source = root / 'ts-modulith/target/travel2-deployed.jar'
output = folder / 'rollback.jar'
initializer = 'BOOT-INF/classes/travel2/init/InitData.class'
with ZipFile(source) as original, ZipFile(output, 'w') as patched:
    assert initializer in original.namelist()
    for entry in original.infolist():
        if entry.filename != initializer:
            patched.writestr(entry, original.read(entry.filename))
with ZipFile(source) as original, ZipFile(output) as patched:
    assert set(original.namelist()) - {initializer} == set(patched.namelist())
    assert all(original.read(name) == patched.read(name) for name in patched.namelist())
digest = subprocess.check_output(['docker', 'image', 'inspect',
    'codewisdom/ts-travel2-service:0.2.0', '--format', '{{index .RepoDigests 0}}'],
    text=True).strip()
(folder / 'Dockerfile.rollback').write_text(
    'FROM ' + digest + '\nCOPY rollback.jar /app/ts-travel2-service-1.0.jar\n',
    encoding='utf-8')
subprocess.run(['docker', 'build', '-q', '-f', str(folder / 'Dockerfile.rollback'),
                '-t', 'train-ticket/travel2-legacy-no-seed:0.2.0', str(folder)], check=True)
report = {'original_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'rollback_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
          'removed_class': initializer}
evidence = root / 'ts-modulith/target/evidence'
evidence.mkdir(parents=True, exist_ok=True)
(evidence / 'travel2-rollback-image.json').write_text(json.dumps(report, indent=2))
print('Travel2 rollback image built; only startup sample writer removed')
