from pathlib import Path
import sys
import unittest
from unittest.mock import patch

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'tools'))
read_text = Path.read_text
read_bytes = Path.read_bytes


def without_build_text(path, *args, **kwargs):
    if path.is_relative_to(root / 'Binaries'):
        raise FileNotFoundError('CI has no local Unreal build output: ' + str(path))
    return read_text(path, *args, **kwargs)


def without_build_bytes(path, *args, **kwargs):
    if path.is_relative_to(root / 'Binaries'):
        raise FileNotFoundError('CI has no local Unreal build output: ' + str(path))
    return read_bytes(path, *args, **kwargs)


with patch.object(Path, 'read_text', without_build_text), patch.object(Path, 'read_bytes', without_build_bytes):
    suite = unittest.defaultTestLoader.discover(str(root / 'tools'), pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
