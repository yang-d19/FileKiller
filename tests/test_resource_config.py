import json
import tempfile
import unittest
from pathlib import Path

from filekiller.config import ResourceConfig, ResourceConfigError


class ResourceConfigTests(unittest.TestCase):
    def test_grandpa_stone_is_the_default_config(self):
        config = ResourceConfig.load()

        self.assertEqual(config.source_path.name, "grandpa-stone.json")
        self.assertEqual(config.dialog_text, "孩子们，是这颗吗？")
        self.assertEqual(config.choice_delay_ms, 600)
        self.assertEqual(config.context_menu_label, "召唤金爷爷击落")
        self.assertTrue(Path(config.background_path).is_file())
        for name in ("bgm", "voice", "explosion"):
            self.assertTrue(Path(config.audio(name)["path"]).is_file())
        for name in ("walk", "point", "kick", "explosion", "arrival", "departure"):
            self.assertTrue(Path(config.sprite(name)["path"]).is_file())
        self.assertIsNotNone(config.animation_group("below_target"))
        self.assertIsNotNone(config.orbit_effect())
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
            self.assertEqual(group["bounce_height"], 0)
            self.assertEqual(config.choice_delay_ms, 0)
            self.assertEqual(config.context_menu_label, "召唤大将怪兽摧毁")
            self.assertEqual(group["items"][0]["path"], str(asset.resolve()))
            self.assertEqual(group["items"][0]["start_frame"], 0)

    def test_grandpa_theme_has_six_bouncing_cats(self):
        project_root = Path(__file__).resolve().parents[1]
        config = ResourceConfig.load(project_root / "config" / "grandpa-stone.json")

        group = config.animation_group("below_target")
        walk = config.sprite("walk")
        self.assertEqual((walk["cols"], walk["rows"]), (4, 4))
        self.assertEqual(walk["offset_y"], 81)
        self.assertFalse(walk["stabilize_x"])
        self.assertTrue(config.sprite("point")["stabilize_x"])
        self.assertTrue(config.sprite("kick")["stabilize_x"])
        self.assertTrue(config.sprite("arrival")["stabilize_x"])
        departure = config.sprite("departure")
        self.assertEqual(departure["move_duration_ms"], 4000)
        self.assertEqual(departure["move_wave_cycles"], 6)
        self.assertEqual(departure["move_wave_strength"], 0.1)
        self.assertTrue(departure["stabilize_x"])
        self.assertEqual(len(group["items"]), 6)
        self.assertEqual(group["offset_y"], 156)
        self.assertEqual(group["duration_ms"], 0)
        self.assertEqual(group["bounce_height"], 18)
        self.assertEqual(group["bounce_period_ms"], 650)
        self.assertEqual(group["bounce_fps"], 30)
        self.assertEqual(
            [item["start_frame"] for item in group["items"]],
            [0, 3, 6, 9, 12, 14],
        )
        self.assertEqual(len({item["path"] for item in group["items"]}), 1)
        for item in group["items"]:
            self.assertTrue(Path(item["path"]).is_file())

        self.assertIsNone(config.optional_audio("victory"))
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
