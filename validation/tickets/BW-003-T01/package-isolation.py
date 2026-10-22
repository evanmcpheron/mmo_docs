import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path.cwd() / 'tools'))
from inspect_client import inspect_directory

parser = argparse.ArgumentParser()
parser.add_argument('--validation', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
temporary = args.output / 'tmp'
temporary.mkdir()
tempfile.tempdir = str(temporary.resolve())
executables = {
    'game': args.validation / 'game-package/package/Mac/Briarwake.app/Contents/MacOS/Briarwake',
    'server': args.validation / 'server-package/package/MacServer/Briarwake/Binaries/Mac/BriarwakeServer',
}
markers = ['Briarwake.RuntimeFixtures.Evidence', 'BriarwakeFixture', 'fixture-evidence', 'invalid-specification-']
results = {}
for target, path in executables.items():
    contents = path.read_bytes()
    found = [marker for marker in markers if any(marker.encode(encoding) in contents
             for encoding in ('ascii', 'utf-16-le', 'utf-16-be', 'utf-32-le', 'utf-32-be'))]
    assert not found, (target, found)
    results[target] = {'executable': str(path), 'sha256': hashlib.sha256(contents).hexdigest(),
                       'bytes': len(contents), 'forbidden_markers': markers, 'found': found}
inspection = inspect_directory(args.validation / 'server-package/package/MacServer',
                               Path('/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealPak'))
assert inspection['result'] == 'Passed', inspection['findings']
report = {'command': sys.argv, 'result': 'Passed', 'executables': results, 'server_package': inspection,
          'scope': 'Normal Game/Server artifact exclusion of fixture code, controls and inputs. No connected-client or gameplay-command certification.'}
(args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print('Game/Server fixture code markers absent; decoded Server package has no private fixture paths or contents.')
