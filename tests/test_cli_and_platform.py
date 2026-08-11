import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import resource_config
from register_menu import preferred_executable
from filekiller.cli import parse_arguments
from filekiller.config import ResourceConfig
from filekiller.filesystem import move_to_trash
from filekiller.platform_windows import (
    build_context_menu_command,
    register_context_menu,
)
from filekiller.window import _should_play_victory


class CompatibilityTests(unittest.TestCase):
    def test_old_resource_config_import_reexports_canonical_class(self):
        self.assertIs(resource_config.ResourceConfig, ResourceConfig)

    def test_cli_accepts_config_and_target(self):
        args = parse_arguments(["--config", "theme.json", "target.txt"])

        self.assertEqual(args.config, "theme.json")
        self.assertEqual(args.target, "target.txt")


class WindowsCommandTests(unittest.TestCase):
    def test_menu_installer_prefers_packaged_windowed_executable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            packaged = project_root / "dist" / "FileKiller.exe"
            packaged.parent.mkdir()
            packaged.write_bytes(b"test executable")

            selected = preferred_executable(
                project_root, interpreter="C:/Python/python.exe"
            )

        self.assertEqual(selected, packaged)

    def test_source_command_quotes_every_path(self):
        command, icon = build_context_menu_command(
            "D:/Themes/my theme.json",
            executable="C:/Python/python.exe",
            entry_script="D:/Code/File Killer/main.py",
            frozen=False,
        )

        self.assertEqual(
            command,
            '"C:/Python/python.exe" "D:\\Code\\File Killer\\main.py" '
            '--config "D:\\Themes\\my theme.json" "%1"',
        )
        self.assertEqual(icon, "shell32.dll,32")

    def test_packaged_command_does_not_include_source_script(self):
        command, icon = build_context_menu_command(
            executable="D:/Apps/FileKiller.exe",
            frozen=True,
        )

        self.assertEqual(command, '"D:/Apps/FileKiller.exe" "%1"')
        self.assertEqual(icon, '"D:/Apps/FileKiller.exe",0')

    def test_registration_writes_theme_label(self):
        fake_winreg = MagicMock()
        registry_key = object()
        fake_winreg.CreateKey.return_value.__enter__.return_value = registry_key

        with (
            patch("filekiller.platform_windows.sys.platform", "win32"),
            patch.dict("sys.modules", {"winreg": fake_winreg}),
        ):
            self.assertTrue(register_context_menu(label="召唤金爷爷击落"))

        fake_winreg.SetValue.assert_any_call(
            registry_key, "", fake_winreg.REG_SZ, "召唤金爷爷击落"
        )


class FilesystemTests(unittest.TestCase):
    def test_existing_file_is_delegated_to_send2trash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "target.txt"
            target.write_text("safe test", encoding="utf-8")

            with patch("filekiller.filesystem.send2trash") as mocked_send:
                self.assertTrue(move_to_trash(target))

            mocked_send.assert_called_once_with(str(target))

    def test_missing_file_is_not_delegated(self):
        with (
            patch("filekiller.filesystem.send2trash") as mocked_send,
            patch("builtins.print"),
        ):
            self.assertFalse(move_to_trash("missing-file.txt"))

        mocked_send.assert_not_called()


class VictoryPlaybackTests(unittest.TestCase):
    def test_preview_mode_plays_complete_victory_cue(self):
        self.assertTrue(_should_play_victory(None, deleted=False))

    def test_successful_deletion_plays_victory_cue(self):
        self.assertTrue(_should_play_victory("target.txt", deleted=True))

    def test_failed_real_deletion_does_not_play_victory_cue(self):
        self.assertFalse(_should_play_victory("missing.txt", deleted=False))


if __name__ == "__main__":
    unittest.main()
