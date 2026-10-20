extends "res://tests/rendering/toon_lighting_check.gd"

func _ready() -> void:
	super._ready()
	var request: Variant = JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
	_output = request["output"]

func _execute() -> void:
	var candidates: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://band-candidates.json"))
	var rows: Array[Dictionary] = []
	var captures: Array[String] = []
	for candidate: Dictionary in candidates:
		for child: Node in _world.get_children():
			if child is MeshInstance3D and child.material_override is ShaderMaterial:
				var material: ShaderMaterial = child.material_override
				material.set_shader_parameter("band_thresholds", Vector2(candidate["thresholds"][0], candidate["thresholds"][1]))
				material.set_shader_parameter("band_values", Vector3(candidate["values"][0], candidate["values"][1], candidate["values"][2]))
				material.set_shader_parameter("band_transition", candidate["transition"])
		_sun.light_energy = 1.0
		_environment.ambient_light_energy = 0.3
		for frame: int in range(16):
			await RenderingServer.frame_post_draw
		var image: Image = _world.get_texture().get_image()
		image.convert(Image.FORMAT_RGB8)
		var filename: String = candidate["id"] + "-swatches.png"
		if image.save_png(_output.path_join(filename)) != OK:
			push_error("Cannot retain band swatches.")
			get_tree().quit(2)
			return
		captures.append(filename)
		rows.append({"candidate": candidate, "filename": filename,
			"rows": ["Source Lambert", "T05 candidate"], "fixtures": _samples})
	print(JSON.stringify({"event": "isolation-report", "observations": rows, "captures": captures}))
	get_tree().quit(0)
