extends "res://tests/rendering/outlines_probe.gd"

func _execute() -> void:
	var candidates: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://band-candidates.json"))
	var surfaces: Array[ShaderMaterial] = []
	var meshes: Array[MeshInstance3D] = []
	ReferenceWorld.AssetLibrary.collect_meshes(_reference, meshes)
	for mesh: MeshInstance3D in meshes:
		if mesh == _posts[_reference]:
			continue
		for index: int in range(mesh.mesh.get_surface_count()):
			var material: Material = mesh.get_active_material(index)
			if material is ShaderMaterial:
				surfaces.append(material)
	var rows: Array[Dictionary] = []
	_path_index = 0
	_frame = 0
	_antialiasing.select(0)
	_toon.button_pressed = true
	for candidate: Dictionary in candidates:
		for material: ShaderMaterial in surfaces:
			material.set_shader_parameter("band_thresholds", Vector2(candidate["thresholds"][0], candidate["thresholds"][1]))
			material.set_shader_parameter("band_values", Vector3(candidate["values"][0], candidate["values"][1], candidate["values"][2]))
			material.set_shader_parameter("band_transition", candidate["transition"])
		for zoom: int in range(2):
			_zooms.select(zoom)
			for lighting: int in range(3):
				_lights.select(lighting)
				for view: String in ["source", "combined"]:
					var image: Image = await _image(_policy["views"].find(view))
					var filename: String = "%s-z%d-l%d-%s.png" % [candidate["id"], zoom, lighting, view]
					_save(filename, image)
					rows.append({"candidate": candidate, "zoom": zoom, "lighting": lighting,
						"view": view, "camera": _presentation.diagnostic(), "filename": filename})
	print(JSON.stringify({"event": "isolation-report", "observations": rows,
		"captures": _captures, "source_settings": _policy}))
	get_tree().quit(0)
