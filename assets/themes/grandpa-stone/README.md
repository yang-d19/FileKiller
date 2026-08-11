# Grandpa Stone theme

An original satirical theme in which an exaggerated elderly statesman picks up a pebble and knocks a generic application window out of the sky.

The visual concept is inspired by the structure of the Chinese internet parody known as “恩情课文”. No images from the referenced web page are included, and all PNG artwork was newly generated for this project.

The configured BGM is the user-supplied local recording `ni-ruo-san-dong-dj.mp3`. It is not produced by `scripts/generate_grandpa_stone_audio.py`; make sure you have the necessary rights before redistributing it. The script still generates the original fallback `bgm.wav` and the two sound effects.

After targeting, three satellites orbit the selected point until the impact begins. The orbit sprite and motion parameters are configured by `resources.orbit_effect`. This theme does not configure a victory voice cue.

The walk sheet is a 4×4, 16-frame loop drawn as a continuous full body with both empty hands below the waist. Its first eight keyframes contain explicit light-leg-forward and dark-leg-forward half-cycles, then repeat once pixel-for-pixel for a seamless loop. It is post-processed by `scripts/stabilize_spritesheet.py --normalize-height`, which uniformly scales each complete figure and aligns every frame to the same upper-body anchor and ground baseline without separating the torso and legs. Its vertical path can be moved per theme with `resources.sprites.walk.offset_y`; this theme uses `81` pixels so the pointing fingertip aligns with the selected target.

The point/pickup, throw, and victory clips enable `stabilize_x`. During
playback, the sprite compensates for each frame's horizontal upper-body offset.
Adjacent stabilized clips retain the same screen anchor, preventing sideways
sway or a jump at the transition while the character stops, picks up the
pebble, knocks down the target, and celebrates.

One original realistic cheering-cat sprite sheet is stored as `sprites/happy-cats/happy-cat-cheer.png`. The theme config reuses it for six cats in a centered row well below the selected target. They appear when the walk begins and remain visible until the elderly character finishes departing. Their starting frames are offset so the cats cheer out of phase, while a staggered upward-only bounce makes the row jump like a wave. Layout, size, speed, spacing, vertical offset, duration, bounce height, bounce period, bounce FPS, and phase offsets are controlled by `resources.animations.below_target` in `config/grandpa-stone.json`; `duration_ms: 0` keeps them alive for the complete main sequence.

This is FileKiller's default theme. Load it with:

```powershell
uv run python main.py
```
