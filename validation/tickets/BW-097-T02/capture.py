import builtins
import json
from pathlib import Path

import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUTPUT = ROOT / 'artifacts/bw-097-t02/rendered'
OUTPUT.mkdir(parents=True, exist_ok=True)
COMMAND = OUTPUT / 'command.json'
state = {'command_id': json.loads(COMMAND.read_text())['id'] if COMMAND.exists() else None, 'run': None}


def vector(value):
    return [value.x, value.y, value.z]


def finish(error=None):
    run = state['run']
    if not run:
        return
    if error:
        run['error'] = str(error)
    (OUTPUT / (run['case'] + '.json')).write_text(json.dumps(run, indent=2))
    state['run'] = None
    unreal.log('BW097_CAPTURE_FINISHED ' + run['case'] + (' ERROR ' + str(error) if error else ''))


def tick(delta):
    if state.get('failed'):
        return
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if not world:
            return
        controller = unreal.GameplayStatics.get_player_controller(world, 0)
        if not controller or not controller.get_controlled_pawn():
            return
        pawn = controller.get_controlled_pawn()
        rig = pawn.get_component_by_class(unreal.ReferenceCameraRig)
        if not rig:
            return
        if COMMAND.exists():
            command = json.loads(COMMAND.read_text())
            if command['id'] != state['command_id']:
                state['command_id'] = command['id']
                if command['action'] == 'run':
                    finish('Superseded before completion')
                    pawn.set_editor_property('route', getattr(unreal.ReferenceCameraRoute, command['route']))
                    rig.set_editor_property('preview_view', unreal.ReferenceCameraView.OVERVIEW)
                    unreal.SystemLibrary.execute_console_command(world, 't.maxfps ' + str(command['cap']))
                    run = {'case': command['id'], 'command': command, 'frames': [], 'events': [],
                           'start': unreal.GameplayStatics.get_time_seconds(world), 'last_shot': -1.0,
                           'width_height': controller.get_viewport_size()}
                    state['run'] = run
                elif command['action'] == 'wheel':
                    accepted = rig.add_wheel_input(command['detents'])
                    (OUTPUT / (command['id'] + '.json')).write_text(json.dumps({'accepted': accepted}))
                elif command['action'] == 'snapshot':
                    camera = pawn.get_component_by_class(unreal.CameraComponent)
                    arm = pawn.get_component_by_class(unreal.SpringArmComponent)
                    position = pawn.get_actor_location()
                    projected = {}
                    for label, point in {'foot': position, 'head': position + unreal.Vector(0,0,163), 'cube': unreal.Vector(600,0,60), 'sphere': unreal.Vector(0,600,60), 'cone': unreal.Vector(-600,-600,60)}.items():
                        pixel = unreal.GameplayStatics.project_world_to_screen(controller, point, False)
                        projected[label] = [pixel.x, pixel.y] if pixel else None
                    data = {'zoom': rig.get_editor_property('zoom_fraction'), 'projection': str(camera.get_editor_property('projection_mode')), 'screen': projected, 'fov': camera.get_editor_property('field_of_view'), 'arm_cm': arm.get_editor_property('target_arm_length'), 'aim': str(pawn.get_base_aim_rotation()), 'size': controller.get_viewport_size()}
                    (OUTPUT / (command['id'] + '.json')).write_text(json.dumps(data, indent=2))
                    unreal.SystemLibrary.execute_console_command(world, 'Shot filename="' + str(OUTPUT / (command['id'] + '.png')) + '" -nosuffix')
        run = state['run']
        if not run:
            return
        now = unreal.GameplayStatics.get_time_seconds(world) - run['start']
        events = [(1.0, 'CLOSE'), (2.3, 'OVERVIEW'), (2.45, 'CLOSE'),
                  (3.0, 'OVERVIEW'), (4.2, 'CLOSE'), (5.5, 'OVERVIEW')]
        for index, (at, endpoint) in enumerate(events):
            if now >= at and index >= len(run['events']):
                rig.set_editor_property('preview_view', getattr(unreal.ReferenceCameraView, endpoint))
                run['events'].append({'time': now, 'endpoint': endpoint})
        camera = pawn.get_component_by_class(unreal.CameraComponent)
        arm = pawn.get_component_by_class(unreal.SpringArmComponent)
        position = pawn.get_actor_location()
        points = {'foot': position, 'head': position + unreal.Vector(0, 0, 163),
                  'cube': unreal.Vector(600, 0, 60), 'sphere': unreal.Vector(0, 600, 60),
                  'cone': unreal.Vector(-600, -600, 60)}
        screen = {}
        for name, point in points.items():
            projected = unreal.GameplayStatics.project_world_to_screen(controller, point, False)
            screen[name] = [projected.x, projected.y] if projected is not None else None
        aim = pawn.get_base_aim_rotation()
        run['frames'].append({'time': now, 'delta': unreal.GameplayStatics.get_world_delta_seconds(world),
                              'zoom': rig.get_editor_property('zoom_fraction'),
                              'projection': str(camera.get_editor_property('projection_mode')),
                              'position': vector(position), 'aim': [aim.pitch, aim.yaw, aim.roll],
                              'screen': screen, 'arm_cm': arm.get_editor_property('target_arm_length'),
                              'fov': camera.get_editor_property('field_of_view')})
        if now - run['last_shot'] >= 0.1:
            run['last_shot'] = now
            image_path = OUTPUT / (run['case'] + '-' + str(len(run['frames'])).zfill(4) + '.png')
            unreal.SystemLibrary.execute_console_command(world, 'Shot filename="' + str(image_path) + '" -nosuffix')
        if now >= 6.8:
            finish()
    except Exception as error:
        state['failed'] = True
        unreal.log_error('BW097_CAPTURE_ERROR ' + str(error))
        finish(error)


(OUTPUT / 'ready.json').write_text(json.dumps({'project': str(ROOT), 'engine': unreal.SystemLibrary.get_engine_version(),
                                             'projector_doc': unreal.GameplayStatics.project_world_to_screen.__doc__}))
if hasattr(builtins, 'bw_camera_probe_handle'):
    unreal.unregister_slate_post_tick_callback(builtins.bw_camera_probe_handle)
handle = unreal.register_slate_post_tick_callback(tick)
builtins.bw_camera_probe_handle = handle
unreal.log('BW097_CAPTURE_READY')
