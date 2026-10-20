from pathlib import Path
import json
import re
import shutil
import subprocess
import sys

GAME = Path('/Users/le-evanmcpheron/Documents/Godot/briarwake')
OUTPUT = Path(__file__).resolve().parent
sys.path.insert(0, str(GAME / 'tools'))
from check_content_admission import pinned_fixture_project
from reference_assets import DEFAULT_ASSETS, validate_reference_assets
from build_baseline import file_sha256

report = {'purpose': 'Requested high-resolution source PBR screenshot; supplemental view, not T05 acceptance evidence',
          'game_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=GAME, text=True).strip(),
          'output': 'courtyard-pbr-4k.png', 'steps': []}
assets = validate_reference_assets(DEFAULT_ASSETS)
with pinned_fixture_project(None, report) as (workspace, command):
    (workspace / 'project.godot').write_text('config_version=5\n[application]\nconfig/name="Briarwake PBR Screenshot"\nrun/flush_stdout_on_print=true\n[display]\nwindow/size/viewport_width=1100\nwindow/size/viewport_height=760\n[rendering]\nrenderer/rendering_method="forward_plus"\n')
    for directory in ('fixtures/rendering', 'tests/rendering'):
        shutil.copytree(GAME / directory, workspace / directory)
    shutil.copyfile(OUTPUT / 'capture.gd', workspace / 'capture.gd')
    (workspace / 'capture.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://capture.gd" id="1"]\n[node name="Capture" type="Control"]\nscript = ExtResource("1")\n')
    local_assets = workspace / 'local-assets'
    local_assets.mkdir()
    for asset in assets['exports']:
        shutil.copyfile(DEFAULT_ASSETS / asset['file'], local_assets / asset['file'])
    reference = json.loads((GAME / 'fixtures/rendering/reference.json').read_text())
    camera = json.loads((GAME / 'fixtures/rendering/camera.json').read_text())
    outline = json.loads((GAME / 'fixtures/rendering/outlines.json').read_text())
    request = {'run_id': 'user-requested-pbr-4k', 'output': str(OUTPUT), 'control': 'pass',
               'interactive': False, 'reference_settings': reference['settings'],
               'camera_settings': camera['settings'], 'outline_settings': outline['settings'],
               'anchors': camera['anchors'], 'asset_directory': str(local_assets)}
    (workspace / 'request.json').write_text(json.dumps(request))
    for label, launch in [('import', command + ['--editor', '--quit']),
                          ('capture', [part for part in command if part != '--headless'] +
                           ['res://capture.tscn', '--', str(workspace / 'request.json')])]:
        print(label, flush=True)
        process = subprocess.run(launch, cwd=workspace, capture_output=True, text=True, timeout=120)
        captured = process.stdout + process.stderr
        (OUTPUT / (label + '.log')).write_text(captured)
        report['steps'].append({'name': label, 'exit_status': process.returncode})
        if process.returncode or re.search(r'(?m)^(SCRIPT ERROR|ERROR|WARNING):', captured):
            (OUTPUT / 'capture-report.json').write_text(json.dumps(report, indent=2) + '\n')
            raise SystemExit(captured)
        if label == 'capture':
            report['capture'] = [json.loads(line) for line in captured.splitlines()
                                 if line.startswith('{') and 'screenshot-captured' in line][0]
report['sha256'] = file_sha256(OUTPUT / report['output'])
report['capture_script_sha256'] = file_sha256(OUTPUT / 'capture.gd')
(OUTPUT / 'capture-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(str(OUTPUT / report['output']), flush=True)
