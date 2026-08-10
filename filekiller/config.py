"""Load, validate, and resolve FileKiller theme configuration files."""

import json
import os
import sys
from pathlib import Path


DEFAULT_CONFIG_RELATIVE_PATH = Path("config") / "default.json"
CONFIG_ENV_VAR = "MONSTER_DELETER_CONFIG"
REQUIRED_AUDIO = ("bgm", "voice", "explosion")
REQUIRED_SPRITES = ("walk", "point", "kick", "explosion", "arrival", "departure")


class ResourceConfigError(RuntimeError):
    """Raised when a configuration or referenced resource is invalid."""


def application_base_path() -> Path:
    """Return the project/bundle root used for built-in resources."""

    bundled_path = getattr(sys, "_MEIPASS", None)
    if bundled_path:
        return Path(bundled_path)
    return Path(__file__).resolve().parents[1]


def find_config_path(config_path=None) -> Path:
    """Resolve CLI/env/default config precedence to one absolute path."""

    override = config_path or os.environ.get(CONFIG_ENV_VAR)
    if override:
        path = Path(os.path.expandvars(override)).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.resolve()

    if getattr(sys, "frozen", False):
        external_path = (
            Path(sys.executable).resolve().parent / DEFAULT_CONFIG_RELATIVE_PATH
        )
        if external_path.is_file():
            return external_path

    return (application_base_path() / DEFAULT_CONFIG_RELATIVE_PATH).resolve()


class ResourceConfig:
    """Validated, immutable-by-copy view of one theme JSON document.

    Public accessors return fresh dictionaries so animation code can safely pop
    loader-only fields without mutating the stored configuration.
    """

    def __init__(self, source_path, data):
        self.source_path = Path(source_path).resolve()
        self.base_dir = self.source_path.parent

        if not isinstance(data, dict):
            raise ResourceConfigError("Configuration root must be a JSON object")

        schema_version = data.get("schema_version", 1)
        if schema_version != 1:
            raise ResourceConfigError(
                f"Unsupported schema_version: {schema_version}; expected 1"
            )

        resources = data.get("resources")
        if not isinstance(resources, dict):
            raise ResourceConfigError("Missing object: resources")

        self.background_path = self._resolve_file(
            resources.get("background"), "resources.background"
        )
        self._audio = self._load_audio(resources.get("audio"))
        self._sprites = self._load_sprites(resources.get("sprites"))
        self._animation_groups = self._load_animation_groups(
            resources.get("animations")
        )
        self._orbit_effect = self._load_orbit_effect(resources.get("orbit_effect"))

    @classmethod
    def load(cls, config_path=None):
        source_path = find_config_path(config_path)
        if not source_path.is_file():
            raise ResourceConfigError(f"Configuration file not found: {source_path}")

        try:
            with source_path.open("r", encoding="utf-8") as config_file:
                data = json.load(config_file)
        except (OSError, json.JSONDecodeError) as exc:
            raise ResourceConfigError(
                f"Unable to read configuration {source_path}: {exc}"
            ) from exc

        return cls(source_path, data)

    def audio(self, name):
        try:
            return dict(self._audio[name])
        except KeyError as exc:
            raise ResourceConfigError(f"Unknown audio resource: {name}") from exc

    def optional_audio(self, name):
        spec = self._audio.get(name)
        return dict(spec) if spec is not None else None

    def orbit_effect(self):
        return dict(self._orbit_effect) if self._orbit_effect is not None else None

    def sprite(self, name):
        try:
            spec = dict(self._sprites[name])
            if spec["frame_indices"] is not None:
                spec["frame_indices"] = list(spec["frame_indices"])
            return spec
        except KeyError as exc:
            raise ResourceConfigError(f"Unknown sprite resource: {name}") from exc

    def animation_group(self, name):
        group = self._animation_groups.get(name)
        if group is None:
            return None

        result = dict(group)
        result["items"] = []
        for item in group["items"]:
            item_copy = dict(item)
            if item_copy["frame_indices"] is not None:
                item_copy["frame_indices"] = list(item_copy["frame_indices"])
            result["items"].append(item_copy)
        return result

    def _load_audio(self, audio):
        if not isinstance(audio, dict):
            raise ResourceConfigError("Missing object: resources.audio")

        for name in REQUIRED_AUDIO:
            if name not in audio:
                raise ResourceConfigError(f"Missing object: resources.audio.{name}")

        result = {}
        for name, spec in audio.items():
            label = f"resources.audio.{name}"
            if not isinstance(spec, dict):
                raise ResourceConfigError(f"Missing object: {label}")

            volume = self._number(spec.get("volume", 1.0), f"{label}.volume")
            if not 0.0 <= volume <= 1.0:
                raise ResourceConfigError(f"{label}.volume must be between 0 and 1")

            result[name] = {
                "path": self._resolve_file(spec.get("path"), f"{label}.path"),
                "volume": volume,
            }
        return result

    def _load_orbit_effect(self, effect):
        if effect is None:
            return None
        if not isinstance(effect, dict):
            raise ResourceConfigError("resources.orbit_effect must be an object")

        label = "resources.orbit_effect"
        speed_dps = self._number(effect.get("speed_dps", 90), f"{label}.speed_dps")
        if speed_dps <= 0:
            raise ResourceConfigError(f"{label}.speed_dps must be positive")

        return {
            "path": self._resolve_file(effect.get("path"), f"{label}.path"),
            "count": self._positive_int(effect.get("count", 3), f"{label}.count"),
            "target_width": self._positive_int(
                effect.get("target_width", 80), f"{label}.target_width"
            ),
            "radius_x": self._positive_int(
                effect.get("radius_x", 150), f"{label}.radius_x"
            ),
            "radius_y": self._positive_int(
                effect.get("radius_y", 70), f"{label}.radius_y"
            ),
            "speed_dps": speed_dps,
            "fps": self._positive_int(effect.get("fps", 30), f"{label}.fps"),
        }

    def _load_sprites(self, sprites):
        if not isinstance(sprites, dict):
            raise ResourceConfigError("Missing object: resources.sprites")

        result = {}
        for name in REQUIRED_SPRITES:
            label = f"resources.sprites.{name}"
            result[name] = self._load_sprite_spec(sprites.get(name), label)
        return result

    def _load_animation_groups(self, animations):
        if animations is None:
            return {}
        if not isinstance(animations, dict):
            raise ResourceConfigError("resources.animations must be an object")

        result = {}
        for name, group in animations.items():
            label = f"resources.animations.{name}"
            if not isinstance(group, dict):
                raise ResourceConfigError(f"{label} must be an object")

            items = group.get("items")
            if not isinstance(items, list) or not items:
                raise ResourceConfigError(f"{label}.items must be a non-empty list")

            result[name] = {
                "offset_y": self._integer(
                    group.get("offset_y", 40), f"{label}.offset_y"
                ),
                "spacing": self._non_negative_int(
                    group.get("spacing", 8), f"{label}.spacing"
                ),
                "duration_ms": self._non_negative_int(
                    group.get("duration_ms", 3000), f"{label}.duration_ms"
                ),
                "items": [
                    self._load_sprite_spec(item, f"{label}.items[{index}]")
                    for index, item in enumerate(items)
                ],
            }
        return result

    def _load_sprite_spec(self, spec, label):
        if not isinstance(spec, dict):
            raise ResourceConfigError(f"Missing object: {label}")

        frame_indices = spec.get("frame_indices")
        if frame_indices is not None:
            if not isinstance(frame_indices, list) or any(
                not isinstance(index, int) or index < 0 for index in frame_indices
            ):
                raise ResourceConfigError(
                    f"{label}.frame_indices must be a list of non-negative integers"
                )

        return {
            "path": self._resolve_file(spec.get("path"), f"{label}.path"),
            "cols": self._positive_int(spec.get("cols", 5), f"{label}.cols"),
            "rows": self._positive_int(spec.get("rows", 3), f"{label}.rows"),
            "target_height": self._positive_int(
                spec.get("target_height", 250), f"{label}.target_height"
            ),
            "fps": self._positive_int(spec.get("fps", 8), f"{label}.fps"),
            "start_frame": self._non_negative_int(
                spec.get("start_frame", 0), f"{label}.start_frame"
            ),
            "offset_y": self._integer(spec.get("offset_y", 0), f"{label}.offset_y"),
            "frame_indices": frame_indices,
        }

    def _resolve_file(self, value, label):
        if not isinstance(value, str) or not value.strip():
            raise ResourceConfigError(f"{label} must be a non-empty path")

        path = Path(os.path.expandvars(value)).expanduser()
        if not path.is_absolute():
            path = self.base_dir / path
        path = path.resolve()

        if not path.is_file():
            raise ResourceConfigError(f"Resource file not found for {label}: {path}")
        return str(path)

    @staticmethod
    def _number(value, label):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ResourceConfigError(f"{label} must be a number")
        return float(value)

    @staticmethod
    def _positive_int(value, label):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ResourceConfigError(f"{label} must be a positive integer")
        return value

    @staticmethod
    def _non_negative_int(value, label):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ResourceConfigError(f"{label} must be a non-negative integer")
        return value

    @staticmethod
    def _integer(value, label):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ResourceConfigError(f"{label} must be an integer")
        return value
