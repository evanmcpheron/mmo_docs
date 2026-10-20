from pathlib import Path
import json
import re
import shutil
import subprocess
import sys

GAME = Path('/Users/le-evanmcpheron/Documents/Godot/briarwake')
SCRIPT = Path(__file__).resolve().parent
sys.path.insert(0, str(GAME / 'tools'))
from check_content_admission import pinned_fixture_project
from reference_assets import DEFAULT_ASSETS, validate_reference_assets
from build_baseline import file_sha256

mode = sys.argv[2] if len(sys.argv) > 2 else 'isolation'
output = Path(sys.argv[1]).resolve()
output.mkdir(exist_ok=False, parents=True)
report = {'purpose': 'Matched T05 effect isolation and material inventory',
          'source_revision': subprocess.check_output(['git','rev-parse','HEAD'],cwd=GAME,text=True).strip(),
          'source_sha256': {str(p.relative_to(GAME)): file_sha256(p)
                            for directory in ('tests/rendering', 'fixtures/rendering')
                            for p in sorted((GAME/directory).glob('*')) if p.is_file()}, 'stages': []}
assets = validate_reference_assets(DEFAULT_ASSETS)
with pinned_fixture_project(None, report) as (workspace, command):
    (workspace/'project.godot').write_text('config_version=5\n[application]\nconfig/name="T05 isolation"\nrun/flush_stdout_on_print=true\n[display]\nwindow/size/viewport_width=1100\nwindow/size/viewport_height=760\n[rendering]\nrenderer/rendering_method="forward_plus"\n')
    for directory in ('fixtures/rendering','tests/rendering'):
        shutil.copytree(GAME/directory, workspace/directory)
    shutil.copyfile(SCRIPT/(mode+'.gd'), workspace/'isolation.gd')
    shutil.copyfile(SCRIPT/(mode+'.gd'), output/'isolation.gd')
    shutil.copyfile(__file__,output/'run.py')
    (workspace/'isolation.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://isolation.gd" id="1"]\n[node name="Isolation" type="Control"]\nscript=ExtResource("1")\n')
    local_assets=workspace/'local-assets'
    local_assets.mkdir()
    for asset in assets['exports']:
        shutil.copyfile(DEFAULT_ASSETS/asset['file'],local_assets/asset['file'])
    def fixture(label): return json.loads((GAME/('fixtures/rendering/'+label+'.json')).read_text())
    request={'run_id':'t05-isolation','output':str(output),'control':'pass','interactive':False,
             'asset_directory':str(local_assets),'reference_settings':fixture('reference')['settings'],
             'camera_settings':fixture('camera')['settings'],'anchors':fixture('camera')['anchors'],
             'outline_settings':fixture('outlines')['settings']}
    (workspace/'request.json').write_text(json.dumps(request))
    for label,launch in [('import',command+['--editor','--quit']),
                         ('graphical',[x for x in command if x!='--headless']+['res://isolation.tscn','--',str(workspace/'request.json')])]:
        print(label,flush=True)
        p=subprocess.run(launch,cwd=workspace,capture_output=True,text=True,timeout=180)
        captured=p.stdout+p.stderr
        (output/(label+'.log')).write_text(captured)
        report['stages'].append({'name':label,'exit_status':p.returncode})
        if p.returncode or re.search(r'(?m)^(SCRIPT ERROR|ERROR|WARNING):',captured):
            (output/'identity.json').write_text(json.dumps(report,indent=2)+'\n')
            raise SystemExit(captured)
        if label=='graphical':
            report['actual']=next(json.loads(x) for x in captured.splitlines() if x.startswith('{') and 'isolation-report' in x)
report['capture_sha256']={x:file_sha256(output/x) for x in report['actual']['captures']}
(output/'identity.json').write_text(json.dumps(report,indent=2)+'\n')
print(output,flush=True)
