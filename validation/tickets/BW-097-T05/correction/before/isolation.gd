extends "res://tests/rendering/outlines_probe.gd"

func _execute() -> void:
	var modes: Array[Dictionary] = [
		{"id": "pbr", "toon": false, "silhouettes": false, "highlights": false},
		{"id": "toon", "toon": true, "silhouettes": false, "highlights": false},
		{"id": "silhouettes-only", "toon": false, "silhouettes": true, "highlights": false},
		{"id": "highlights-only", "toon": false, "silhouettes": false, "highlights": true},
		{"id": "toon-silhouettes", "toon": true, "silhouettes": true, "highlights": false},
		{"id": "toon-highlights", "toon": true, "silhouettes": false, "highlights": true},
		{"id": "combined", "toon": true, "silhouettes": true, "highlights": true}]
	var observations: Array[Dictionary] = []
	_path_index = 0
	_frame = 0
	_antialiasing.select(0)
	for zoom: int in range(2):
		_zooms.select(zoom)
		for lighting: int in range(3):
			_lights.select(lighting)
			for mode: Dictionary in modes:
				_toon.button_pressed = mode["toon"]
				_silhouettes.button_pressed = mode["silhouettes"]
				_highlights.button_pressed = mode["highlights"]
				var screenshot: Image = await _image(_policy["views"].find("combined"))
				var filename: String = "courtyard-z%d-l%d-%s.png" % [zoom, lighting, mode["id"]]
				_save(filename, screenshot)
				observations.append({"filename": filename, "mode": mode,
					"zoom": zoom, "lighting": lighting, "frame": _frame,
					"camera": _presentation.diagnostic(), "regions": _reference.projected_regions()})
			_toon.button_pressed = true
			for label: String in ["raw-depth", "view-depth", "view-normal", "silhouettes", "highlights", "masks"]:
				var diagnostic_image: Image = await _image(_policy["views"].find(label))
				_save("courtyard-z%d-l%d-%s.png" % [zoom, lighting, label], diagnostic_image)
	_toon.button_pressed = false
	_apply()
	var material_inventory: Array[Dictionary] = []
	var meshes: Array[MeshInstance3D] = []
	ReferenceWorld.AssetLibrary.collect_meshes(_reference, meshes)
	for mesh: MeshInstance3D in meshes:
		if mesh == _posts[_reference]:
			continue
		for surface: int in range(mesh.mesh.get_surface_count()):
			var source: Material = mesh.get_active_material(surface)
			if not source is StandardMaterial3D:
				_fail("Expected original StandardMaterial3D while inventorying.")
				return
			material_inventory.append({"mesh": str(_reference.get_path_to(mesh)), "surface": surface,
				"name": source.resource_name, "albedo_color": source.albedo_color.to_html(),
				"albedo_texture": source.albedo_texture != null,
				"normal_enabled": source.normal_enabled, "normal_texture": source.normal_texture != null,
				"normal_scale": source.normal_scale, "metallic": source.metallic,
				"metallic_texture": source.metallic_texture != null,
				"roughness": source.roughness, "roughness_texture": source.roughness_texture != null,
				"specular": source.metallic_specular, "transparency": source.transparency,
				"alpha_cutoff": source.alpha_scissor_threshold, "cull_mode": source.cull_mode,
				"uv_scale": source.uv1_scale, "uv_offset": source.uv1_offset,
				"texture_filter": source.texture_filter})
	print(JSON.stringify({"event": "isolation-report", "observations": observations,
		"materials": material_inventory, "captures": _captures, "source_assets": _reference.loaded_assets,
		"settings": _policy, "viewport": _settings.source}))
	get_tree().quit(0)
