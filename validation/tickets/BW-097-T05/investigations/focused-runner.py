import sys,json,shutil,subprocess
from pathlib import Path
sys.path.insert(0,'tools')
from check_content_admission import pinned_fixture_project
from reference_assets import DEFAULT_ASSETS
from extract_content_contracts import encoded
root=Path.cwd()
with pinned_fixture_project(None,{}) as (w,command):
 (w/'project.godot').write_text('config_version=5\n[application]\nconfig/name="T05 stationary debug"\n[rendering]\nrenderer/rendering_method="forward_plus"\n')
 for folder in ('fixtures/rendering','tests/rendering'):
  shutil.copytree(root/folder,w/folder)
 toon=w/'fixtures/rendering/toon.gdshader'
 toon.write_text(toon.read_text().replace('ROUGHNESS = 1.0;', 'ROUGHNESS = 1.0; SPECULAR = 0.0;'))
 shader=w/'fixtures/rendering/outlines.gdshader'
 shader.write_text(shader.read_text())
 s=(w/'tests/rendering/outlines_probe.gd').read_text();s=s[:s.index('func _execute() -> void:')]+'''func _execute() -> void:
\tfor mode: int in range(6):
\t\tvar hashes: Dictionary[String, bool] = {}
\t\tvar base: PackedByteArray
\t\tvar max_changed: int = 0
\t\tvar max_delta: int = 0
\t\t_lights.select(mode % 3)
\t\t_zooms.select(mode / 3)
\t\t_select_fixture()
\t\t_path_index = 0
\t\t_frame = 0
\t\t_views.select(8)
\t\t_apply()
\t\tfor warmup: int in range(4):
\t\t\tawait _settle()
\t\tfor frame: int in range(32):
\t\t\tif false:
\t\t\t\t_apply()
\t\t\tif false:
\t\t\t\tawait _image(6)
\t\t\t\tawait _image(8)
\t\t\tif false:
\t\t\t\t_reference.set_lighting(0)
\t\t\tawait _settle()
\t\t\tvar image: Image = _world.get_texture().get_image()
\t\t\timage.convert(Image.FORMAT_RGB8)
\t\t\tvar bytes: PackedByteArray = image.get_data()
\t\t\tif frame == 0:
\t\t\t\tbase = bytes
\t\t\tvar changed: int = 0
\t\t\tfor index: int in range(bytes.size()):
\t\t\t\tchanged += int(bytes[index] != base[index])
\t\t\t\tmax_delta = maxi(max_delta, absi(bytes[index] - base[index]))
\t\t\tmax_changed = maxi(max_changed, changed)
\t\t\tvar hash: HashingContext = HashingContext.new()
\t\t\thash.start(HashingContext.HASH_SHA256)
\t\t\thash.update(bytes)
\t\t\thashes[hash.finish().hex_encode()] = true
\t\tprint(JSON.stringify({"debug_mode": mode, "hash_count": hashes.size(), "max_changed_channels": max_changed, "max_delta": max_delta, "debanding": _world.use_debanding}))
\tget_tree().quit()
'''
 (w/'tests/rendering/outlines_probe.gd').write_text(s)
 out=root/'artifacts/t05-debug';out.mkdir(exist_ok=True)
 req={'run_id':'debug','output':str(out),'control':'pass','interactive':False,'outline_settings':json.load(open('fixtures/rendering/outlines.json'))['settings'],'camera_settings':json.load(open('fixtures/rendering/camera.json'))['settings'],'reference_settings':json.load(open('fixtures/rendering/reference.json'))['settings'],'anchors':json.load(open('fixtures/rendering/camera.json'))['anchors'],'asset_directory':str(DEFAULT_ASSETS)}
 (w/'request.json').write_bytes(encoded(req))
 imp=subprocess.run(command+['--editor','--quit'],capture_output=True,text=True);print(imp.stdout,imp.stderr)
 result=subprocess.run([p for p in command if p!='--headless']+['res://tests/rendering/outlines_probe.tscn','--',str(w/'request.json')],capture_output=True,text=True,timeout=120)
 (out/'debug.log').write_text(result.stdout+result.stderr);print(result.stdout,result.stderr)
