import sys,json,shutil,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,'tools')
from check_content_admission import pinned_fixture_project
from reference_assets import DEFAULT_ASSETS
from extract_content_contracts import encoded
from run_baseline import source_build_revision
root=Path.cwd();output=root/'artifacts/t05-corrected-pairs-preview';output.mkdir()
with pinned_fixture_project(None,{}) as (workspace,command):
 (workspace/'project.godot').write_text('config_version=5\n[application]\nconfig/name="T05 corrected pair preview"\n[rendering]\nrenderer/rendering_method="forward_plus"\n')
 sources={}
 for folder in ('fixtures/rendering','tests/rendering'):
  shutil.copytree(root/folder,workspace/folder)
  for f in (root/folder).glob('*'):sources[str(f.relative_to(root))]=hashlib.sha256(f.read_bytes()).hexdigest()
 p=workspace/'tests/rendering/outlines_probe.gd';s=p.read_text();s=s[:s.index('func _execute() -> void:')]+'''func _execute() -> void:
	for zoom: int in range(2):
		for label: String in _policy["model_cases"]:
			await _still(label, zoom, 0, 0)
	for label: String in ["actors-touching", "actors-overlap"]:
		await _sequence(label, 0, 0, 2)
	var output: FileAccess = FileAccess.open(_request["output"].path_join("preview.json"), FileAccess.WRITE)
	output.store_string(JSON.stringify({"observations": _observations, "sequences": _sequences,
		"captures": _captures, "outline_settings": _policy}))
	output.close()
	get_tree().quit()
''';p.write_text(s)
 request={'run_id':'corrected-pairs-preview','output':str(output),'control':'pass','interactive':False,'outline_settings':json.load(open('fixtures/rendering/outlines.json'))['settings'],'camera_settings':json.load(open('fixtures/rendering/camera.json'))['settings'],'reference_settings':json.load(open('fixtures/rendering/reference.json'))['settings'],'anchors':json.load(open('fixtures/rendering/camera.json'))['anchors'],'asset_directory':str(DEFAULT_ASSETS)}
 (workspace/'request.json').write_bytes(encoded(request))
 imp=subprocess.run(command+['--editor','--quit'],capture_output=True,text=True);(output/'import.log').write_text(imp.stdout+imp.stderr)
 proc=subprocess.run([v for v in command if v!='--headless']+['res://tests/rendering/outlines_probe.tscn','--',str(workspace/'request.json')],capture_output=True,text=True,timeout=120)
 (output/'graphical.log').write_text(proc.stdout+proc.stderr)
 (output/'identity.json').write_bytes(encoded({'purpose':'Focused corrected character pair still/motion preview; not a full matrix pass','revision':source_build_revision(),'source_sha256':sources,'overridden_probe_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'exit_status':proc.returncode}))
 print(proc.stdout,proc.stderr)
 sys.exit(proc.returncode)
