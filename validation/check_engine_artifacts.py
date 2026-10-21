"""Reject legacy engine implementation files while preserving reference evidence."""
import os
from pathlib import Path, PurePosixPath
import subprocess


ROOT = Path(__file__).resolve().parents[1]
LEGACY_EXTENSIONS = {'.gd', '.gdc', '.gdshader', '.gdshaderinc', '.gdextension', '.tscn', '.tres'}


def legacy_engine_artifacts(paths):
    violations = []
    for name in paths:
        path = PurePosixPath(name.lower())
        if (path.name == 'project.godot' or '.godot' in path.parts
                or path.suffix in LEGACY_EXTENSIONS):
            violations.append(name)
    return sorted(violations)


def main(root=ROOT):
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).split(b'\0')
    violations = legacy_engine_artifacts([os.fsdecode(path) for path in tracked if path])
    if violations:
        print('Legacy engine implementation artifacts: ' + ', '.join(violations))
        return 1
    print('Legacy engine implementation artifact count: 0; documentation and evidence references are permitted')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
