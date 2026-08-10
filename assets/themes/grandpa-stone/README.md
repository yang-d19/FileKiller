# Grandpa Stone theme

An original satirical theme in which an exaggerated elderly statesman picks up a pebble and knocks a generic application window out of the sky.

The visual concept is inspired by the structure of the Chinese internet parody known as “恩情课文”. No images from the referenced web page are included, and all PNG artwork was newly generated for this project.

The configured BGM is the user-supplied local recording `ni-ruo-san-dong-dj.mp3`. It is not produced by `scripts/generate_grandpa_stone_audio.py`; make sure you have the necessary rights before redistributing it. The script still generates the original fallback `bgm.wav` and the two sound effects.

After targeting, three satellites orbit the selected point until the impact begins. The orbit sprite and motion parameters are configured by `resources.orbit_effect`. After a real file is successfully moved to the recycle bin, the optional `resources.audio.victory` cue plays the Korean phrase “조선민주주의인민공화국 만세!”.

The walk sheet is a 4×4, 16-frame loop drawn as a continuous full body with both empty hands below the waist. Its first eight keyframes contain explicit light-leg-forward and dark-leg-forward half-cycles, then repeat once pixel-for-pixel for a seamless loop. It is post-processed by `scripts/stabilize_spritesheet.py --normalize-height`, which uniformly scales each complete figure and aligns every frame to the same upper-body anchor and ground baseline without separating the torso and legs. Its vertical path can be moved per theme with `resources.sprites.walk.offset_y`; this theme uses `55` pixels to keep the character below the skyward target.

One original realistic cheering-cat sprite sheet is stored as `sprites/happy-cats/happy-cat-cheer.png`. The theme config reuses it for four cats in a centered row well below the selected target. They appear when the walk begins and remain visible until the elderly character finishes departing. Their starting frames are offset so the cats cheer out of phase. Layout, size, speed, spacing, vertical offset, duration, and phase offsets are controlled by `resources.animations.below_target` in `config/grandpa-stone.json`; `duration_ms: 0` keeps them alive for the complete main sequence.

Load the theme with:

```powershell
.\.venv\Scripts\python.exe main.py --config config\grandpa-stone.json
```
