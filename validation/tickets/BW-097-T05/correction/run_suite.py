from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
import sys

root = Path('/Users/le-evanmcpheron/Documents/Godot/briarwake')
output = root / 'artifacts/t05-correction-final-suite'
output.mkdir(exist_ok=False)
revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
if subprocess.run(['git','diff','--quiet'],cwd=root).returncode:
    raise SystemExit('Source must be frozen before this suite.')
cases = [
 ('outlines-invalid-settings','outlines','invalid-settings',1),
 ('outlines-missing-report','outlines','missing-report',1),
 ('outlines-check-failure','outlines','check-failure',1),
 ('outlines-recovery','outlines','pass',0),
 ('capabilities-regression','capabilities','pass',0),
 ('viewport-regression','viewport','pass',0),
 ('reference-regression','reference','pass',0),
 ('camera-regression','camera','pass',0),
]
report={'source_revision':revision,'started_at_utc':datetime.now(timezone.utc).isoformat(),'runs':[]}
for name, case, control, expected_exit in cases:
    print('Starting '+name,flush=True)
    command=[sys.executable,'tools/run_rendering_probe.py','--case',case,'--control',control,'--output',str(output/name)]
    with (output/(name+'.log')).open('w') as log:
        process=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
    actual=json.loads((output/name/'run.json').read_text())
    matched=process.returncode==expected_exit
    if expected_exit==0:
        matched=matched and actual['result']=='Passed'
    elif control=='invalid-settings':
        matched=matched and actual['execution_state']=='Not Executed' and actual['automated_evidence'] is None
    elif control=='missing-report':
        matched=matched and actual['execution_state']=='Executed' and actual['automated_evidence'] is None
    else:
        matched=matched and actual['automated_evidence']['status']=='failed' and any(
            finding['code']=='deliberate-failure' for finding in actual['automated_evidence']['findings'])
    report['runs'].append({'name':name,'command':command,'exit_status':process.returncode,
        'expected_exit_status':expected_exit,'expectation_met':matched,
        'actual_result':actual['result'],'report':name+'/run.json',
        'checks':actual.get('actual',{}).get('checks',[]),
        'failure':actual.get('failure')})
    (output/'suite.json').write_text(json.dumps(report,indent=2)+'\n')
    print(name+': '+('expected outcome' if matched else 'UNEXPECTED FAILURE'),flush=True)
    if not matched:
        raise SystemExit(1)
report['finished_at_utc']=datetime.now(timezone.utc).isoformat()
report['all_expectations_met']=True
(output/'suite.json').write_text(json.dumps(report,indent=2)+'\n')
print('Suite finished '+revision,flush=True)
