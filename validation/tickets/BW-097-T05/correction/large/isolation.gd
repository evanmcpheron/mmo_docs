extends "res://tests/rendering/outlines_probe.gd"

func _execute() -> void:
	_path_index = 0
	_frame = 0
	_zooms.select(0)
	_lights.select(0)
	_antialiasing.select(0)
	var output_view: SubViewport = SubViewport.new()
	output_view.size = Vector2i(3840, 2160)
	output_view.disable_3d = true
	output_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(output_view)
	_clip.reparent(output_view)
	_rectangle = Rect2i(0, 0, 3840, 2160)
	_clip.position = Vector2.ZERO
	_clip.size = Vector2(_rectangle.size)
	var rows: Array[Dictionary] = []
	for mode: String in ["pbr", "toon-only", "full-t05", "masks"]:
		_toon.set_pressed_no_signal(mode != "pbr")
		_silhouettes.set_pressed_no_signal(mode == "full-t05")
		_highlights.set_pressed_no_signal(mode == "full-t05")
		_views.select(_policy["views"].find("masks" if mode == "masks" else
			"combined" if mode == "full-t05" else "source"))
		_apply()
		for frame: int in range(8):
			await RenderingServer.frame_post_draw
		var image: Image = output_view.get_texture().get_image()
		image.convert(Image.FORMAT_RGB8)
		_save(mode + "-gameplay-3840x2160.png", image)
		var original: Image = _reference.get_texture().get_image()
		original.convert(Image.FORMAT_RGB8)
		_save(mode + "-guarded-386x218.png", original)
		rows.append({"mode": mode, "logical_resolution": [384, 216], "guarded_resolution": [386, 218],
			"presentation": "10x nearest through the T04 TextureRect presentation, GPU readback",
			"output_resolution": [image.get_width(), image.get_height()],
			"camera": _presentation.diagnostic(), "source_settings": _policy})
	_toon.set_pressed_no_signal(true)
	_views.select(0)
	_apply()
	_reference.size = Vector2i(3840, 2160)
	_reference.camera.size = _settings.orthographic_size
	_reference.msaa_3d = Viewport.MSAA_4X
	for frame: int in range(16):
		await RenderingServer.frame_post_draw
	var detail: Image = _reference.get_texture().get_image()
	detail.convert(Image.FORMAT_RGB8)
	_save("toon-material-detail-native-3840x2160.png", detail)
	rows.append({"mode": "native material detail", "logical_resolution": [3840, 2160],
		"msaa": "4x", "outlines": false, "highlights": false,
		"purpose": "Supplemental material inspection only; not gameplay pixel/outline/stability evidence"})
	print(JSON.stringify({"event": "isolation-report", "observations": rows, "captures": _captures}))
	get_tree().quit(0)
