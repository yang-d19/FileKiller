import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import resource_config
from filekiller.cli import parse_arguments
from filekiller.config import ResourceConfig
from filekiller.filesystem import move_to_trash
from filekiller.platform_windows import build_context_menu_command


class CompatibilityTests(unittest.TestCase):
    def test_old_resource_config_import_reexports_canonical_class(self):
        self.assertIs(resource_config.ResourceConfig, ResourceConfig)

    def test_cli_accepts_config_and_target(self):
        args = parse_arguments(["--config", "theme.json", "target.txt"])

        self.assertEqual(args.config, "theme.json")
        self.assertEqual(args.target, "target.txt")


class WindowsCommandTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
