import json
import tempfile
import unittest
from pathlib import Path

from filekiller.config import ResourceConfig, ResourceConfigError


class ResourceConfigTests(unittest.TestCase):
    def test_default_config_resolves_every_resource(self):
        config = ResourceConfig.load()

        self.assertTrue(Path(config.background_path).is_file())
        for name in ("bgm", "voice", "explosion"):
            self.assertTrue(Path(config.audio(name)["path"]).is_file())
        for name in ("walk", "point", "kick", "explosion", "arrival", "departure"):
            self.assertTrue(Path(config.sprite(name)["path"]).is_file())
        self.assertIsNone(config.animation_group("below_target"))
        self.assertIsNone(config.orbit_effect())
        self.assertIsNone(config.optional_audio("victory"))

    def test_custom_paths_are_relative_to_the_config_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            asset = root / "skin.asset"
            asset.write_bytes(b"test")
            config_path = root / "skin.json"
            config_path.write_text(
                json.dumps(
                    {
                        "resources": {
                            "background": "skin.asset",
                            "audio": {
                                name: {"path": "skin.asset"}
                                for name in ("bgm", "voice", "explosion")
                            },
                            "sprites": {
                                name: {"path": "skin.asset"}
                                for name in (
                                    "walk",
                                    "point",
                                    "kick",
                                    "explosion",
                                    "arrival",
                                    "departure",
                                )
                            },
                            "animations": {
                                "below_target": {
                                    "offset_y": 64,
                                    "spacing": 10,
                                    "duration_ms": 2400,
                                    "items": [
                                        {
                                            "path": "skin.asset",
                                            "cols": 1,
                                            "rows": 1,
                                            "target_height": 80,
                                            "fps": 12,
                                        }
                                    ],
                                }
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )

            config = ResourceConfig.load(config_path)

            self.assertEqual(config.background_path, str(asset.resolve()))
            self.assertEqual(config.audio("bgm")["path"], str(asset.resolve()))
            self.assertEqual(config.sprite("walk")["path"], str(asset.resolve()))
            group = config.animation_group("below_target")
            self.assertEqual(group["offset_y"], 64)
            self.assertEqual(group["items"][0]["path"], str(asset.resolve()))
            self.assertEqual(group["items"][0]["start_frame"], 0)

    def test_grandpa_theme_has_four_below_target_animations(self):
        project_root = Path(__file__).resolve().parents[1]
        config = ResourceConfig.load(project_root / "config" / "grandpa-stone.json")

        group = config.animation_group("below_target")
        walk = config.sprite("walk")
        self.assertEqual((walk["cols"], walk["rows"]), (4, 4))
        self.assertEqual(walk["offset_y"], 55)
        self.assertEqual(len(group["items"]), 4)
        self.assertEqual(group["offset_y"], 130)
        self.assertEqual(group["duration_ms"], 0)
        self.assertEqual(
            [item["start_frame"] for item in group["items"]], [0, 3, 6, 9]
        )
        self.assertEqual(len({item["path"] for item in group["items"]}), 1)
        for item in group["items"]:
            self.assertTrue(Path(item["path"]).is_file())

        victory = config.optional_audio("victory")
        self.assertTrue(Path(victory["path"]).is_file())
        orbit = config.orbit_effect()
        self.assertTrue(Path(orbit["path"]).is_file())
        self.assertEqual(orbit["count"], 3)

    def test_missing_resource_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "broken.json"
            config_path.write_text(
                json.dumps({"resources": {"background": "missing.png"}}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ResourceConfigError, "Resource file not found"):
                ResourceConfig.load(config_path)

    def test_unknown_schema_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "future.json"
            config_path.write_text(
                json.dumps({"schema_version": 2, "resources": {}}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ResourceConfigError, "Unsupported schema_version"):
                ResourceConfig.load(config_path)


if __name__ == "__main__":
    unittest.main()
