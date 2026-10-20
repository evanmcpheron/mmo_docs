from pathlib import Path
import sys,json,shutil,tempfile,subprocess
sys.path.insert(0,str(Path.cwd()/'tools'))
from run_rendering_probe import PROJECT_ROOT
from check_content_admission import pinned_fixture_project
from check_baseline import run_stage
out=PROJECT_ROOT/'artifacts/camera-stationary-diagnosis-10';out.mkdir();(out/'logs').mkdir()
with pinned_fixture_project(Path('/Applications/Godot.app/Contents/MacOS/Godot'),{}) as (workspace,cmd):
 (workspace/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Camera diagnosis"\n[rendering]\nrenderer/rendering_method="forward_plus"\n')
 for directory in ['tests/rendering','fixtures/rendering']:
  shutil.copytree(PROJECT_ROOT/directory,workspace/directory,dirs_exist_ok=True)
 (workspace/'diagnose.gd').write_text('''extends SceneTree
const Settings = preload("res://tests/rendering/viewport_settings.gd")
const World = preload("res://tests/rendering/reference_world.gd")
const Presentation = preload("res://tests/rendering/camera_presentation.gd")
func _initialize() -> void:
 run.call_deferred()
func run() -> void:
 var settings: Settings = Settings.new()
 settings.read_fixture()
 var world: World = World.new()
 root.add_child(world)
 world.configure(settings, "ASSETS", "res://fixtures/rendering/titan-layout.json", 1.0)
 world.actor.position = Vector3(0.375,0,-0.625)
 world.actor.rotation_degrees.y = 135
 var preview: TextureRect = TextureRect.new()
 root.add_child(preview)
 var presentation: Presentation = Presentation.new()
 presentation.configure(settings, world, world.camera, preview, 1)
 presentation.present(Vector3(0,1,0), 1.0, Rect2i(0,0,1536,864), true)
 var meshes: Array[MeshInstance3D] = []
 collect(world, meshes)
 for variant: String in ["baseline"]:
  var ground: MeshInstance3D = meshes[0]
  var original_ground: StandardMaterial3D = ground.get_active_material(0)
  var ground_material: StandardMaterial3D = StandardMaterial3D.new()
  if variant == "baseline": ground_material = original_ground.duplicate()
  else:
   ground_material.uv1_scale = Vector3(15,15,1)
   ground_material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
   if variant.begins_with("albedo-only"):
    ground_material.albedo_texture = original_ground.albedo_texture
   if variant in ["albedo-only-unshaded", "ground-constant"]:
    ground_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
  ground.material_override = ground_material
  if variant == "no-crate":
   for mesh: MeshInstance3D in meshes:
    if mesh.get_active_material(0).resource_name.begins_with("TitanCrate"): mesh.visible = false
  if variant == "no-shadow-cast":
   for mesh: MeshInstance3D in meshes:
    if mesh.get_active_material(0).resource_name.begins_with("TitanCrate"): mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  if variant == "no-texture":
   for mesh: MeshInstance3D in meshes:
    if mesh.get_active_material(0).resource_name.begins_with("TitanCrate"):
     print("crate ",mesh.name)
     for index: int in range(mesh.mesh.get_surface_count()):
      var original: Material = mesh.get_active_material(index)
      if original is StandardMaterial3D:
       var material: StandardMaterial3D = original.duplicate()
       material.albedo_texture = null
       material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
       material.albedo_color = Color.WHITE
       mesh.set_surface_override_material(index, material)
  if variant == "nearest":
   for mesh: MeshInstance3D in meshes:
    for index: int in range(mesh.mesh.get_surface_count()):
     var mat: Material = mesh.get_active_material(index)
     if mat is StandardMaterial3D: mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
  if variant == "no-shadows":
   for child: Node in world.get_children():
    if child is Light3D: child.shadow_enabled = false
  if variant == "no-reflection":
   for child: Node in world.get_children():
    if child is WorldEnvironment: child.environment.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
  if variant in ["no-normal", "unshaded"]:
   for mesh: MeshInstance3D in meshes:
    for index: int in range(mesh.mesh.get_surface_count()):
     var original: Material = mesh.get_active_material(index)
     if original is StandardMaterial3D:
      var material: StandardMaterial3D = original.duplicate()
      if variant == "no-normal": material.normal_enabled = false
      else: material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
      mesh.set_surface_override_material(index, material)
  for warmup: int in range(8): await RenderingServer.frame_post_draw
  var hashes: Dictionary = {}
  var atlas: Image = Image.create(386*8,218*8,false,Image.FORMAT_RGB8)
  for frame: int in range(64):
   await RenderingServer.frame_post_draw
   var im: Image = world.get_texture().get_image()
   im.convert(Image.FORMAT_RGB8)
   hashes[im.get_data().hex_encode().sha256_text()] = true
   atlas.blit_rect(im,Rect2i(0,0,386,218),Vector2i(frame%8,floori(frame/8.0))*Vector2i(386,218))
  if variant == "baseline" or hashes.size() == 1: atlas.save_webp("OUTPUT/"+variant+".webp",false)
  print(JSON.stringify({"variant":variant,"unique_frames":hashes.size()}))
 quit()
func collect(node: Node, meshes: Array[MeshInstance3D]) -> void:
 if node is MeshInstance3D: meshes.append(node)
 for child: Node in node.get_children(): collect(child,meshes)
'''.replace('ASSETS',str(PROJECT_ROOT/'artifacts/titan-export-work/exports')).replace('OUTPUT',str(out)))
 stage,logs=run_stage('import',cmd+['--editor','--quit'],workspace,out,[],40)
 print(stage,logs)
 stage,logs=run_stage('diagnosis',[x for x in cmd if x!='--headless']+['--script','res://diagnose.gd'],workspace,out,[],180)
 print(stage,logs)
