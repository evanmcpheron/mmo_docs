extends "res://tests/rendering/outlines_probe.gd"

func _execute() -> void:
	_playing = false
	set_process(false)
	_toon.button_pressed = false
	_views.select(0)
	_path_index = 0
	_frame = 0
	_apply()
	_reference.size = Vector2i(3840, 2160)
	_reference.camera.size = _settings.orthographic_size
	_reference.msaa_3d = Viewport.MSAA_4X
	_reference.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
	for frame: int in range(32):
		await RenderingServer.frame_post_draw
	var screenshot: Image = _reference.get_texture().get_image()
	screenshot.convert(Image.FORMAT_RGB8)
	if screenshot.save_png(_request["output"].path_join("courtyard-pbr-4k.png")) != OK:
		_fail("Cannot save 4K PBR screenshot.")
		return
	print(JSON.stringify({"event": "screenshot-captured", "width": screenshot.get_width(),
		"height": screenshot.get_height(), "camera_size": _reference.camera.size,
		"materials": "original PBR", "custom_toon": false, "custom_outline": false,
		"msaa": "4x", "camera_position": _reference.camera.position,
		"actor_position": _reference.actor.position}))
	get_tree().quit(0)
