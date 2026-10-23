import os
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import start_qt
from tools.test_range_launcher_core import temporary_directory


class QtLauncherTests(unittest.TestCase):
    def test_version_directories_are_distinct(self):
        a = start_qt.executable_path('5.15.2', 'widgets')
        b = start_qt.executable_path('6.8.3', 'quick')
        self.assertNotEqual(a.parent, b.parent)
        self.assertEqual(a.name, 'qt-widgets-range.exe')
        self.assertEqual(b.name, 'qt-quick-range.exe')

    def test_launch_environment_removes_other_qt_plugins(self):
        with patch.dict(os.environ, {'QT_PLUGIN_PATH': 'bad', 'QML2_IMPORT_PATH': 'bad',
                                    'QML_IMPORT_PATH': 'bad', 'QT_QPA_PLATFORM_PLUGIN_PATH': 'bad'}):
            env = start_qt.runtime_environment()
        for key in ('QT_PLUGIN_PATH', 'QML2_IMPORT_PATH', 'QML_IMPORT_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH'):
            self.assertNotIn(key, env)

    def test_missing_deployment_fails_before_launch(self):
        with patch.object(start_qt, 'QT_ROOT', Path('missing-qt-fixture')):
            with self.assertRaises(FileNotFoundError):
                start_qt.validate_artifact('6.8.3', 'widgets')

    def test_multiple_versions_and_frontends_parse(self):
        args = start_qt.parse_args(['--versions', '5.15.2', '6.8.3', '--frontends',
                                    'widgets', 'quick', '--form-mode', 'random', '--no-launch'])
        self.assertEqual(args.versions, ['5.15.2', '6.8.3'])
        self.assertEqual(args.frontends, ['widgets', 'quick'])
        self.assertEqual(args.form_mode, 'random')

    def test_missing_noncore_runtime_is_detected(self):
        with temporary_directory() as directory:
            root = Path(directory)
            deploy = root / 'dist/5.15.2'
            deploy.mkdir(parents=True)
            files = {'qt-widgets-range.exe': b'exe', 'Qt5Core.dll': b'core',
                     'platforms/qwindows.dll': b'platform', 'Qt5Widgets.dll': b'widgets'}
            manifest = {}
            for name, content in files.items():
                path = deploy / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
                manifest[name] = start_qt.sha256(path)
            (deploy / 'manifest.json').write_text(json.dumps({'qt_version': '5.15.2', 'files': manifest}))
            with patch.object(start_qt, 'QT_ROOT', root):
                start_qt.validate_artifact('5.15.2', 'widgets')
                (deploy / 'Qt5Widgets.dll').unlink()
                with self.assertRaises(FileNotFoundError):
                    start_qt.validate_artifact('5.15.2', 'widgets')

    def test_runtime_keeps_user_dpi_settings(self):
        with patch.dict(os.environ, {'QT_SCALE_FACTOR': '1.25'}):
            self.assertEqual(start_qt.runtime_environment().get('QT_SCALE_FACTOR'), '1.25')


if __name__ == '__main__':
    unittest.main()
