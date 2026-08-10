# Image generation prompt set

Generation mode: built-in `image_gen` tool.

Shared visual direction: original satirical 2D retro East Asian schoolbook illustration with subtle screen-print texture. The elderly statesman has a round expressive face, tall swept-back dark hair with gray temples, oversized square dark glasses, an olive zip-front tunic and matching trousers, and black shoes. No flags, political emblems, real application logos, readable text, or watermarks.

## Background

A 16:9 monumental courtyard at blue-hour dusk, with a flower bed and pebbles in the foreground, warm institutional buildings and distant hills. The upper sky contains only varied retro-futuristic communications and scientific satellites following graceful curved orbital paths; no computer windows, application icons, UI panels, charts, or file icons. Leave clear central ground space for animation. No people or destruction.

## Satellite

One compact cream-and-teal retro-futuristic communications satellite with symmetrical dark-blue solar-panel wings, a parabolic dish, antenna rods, and warm golden highlights. Clear three-quarter view, horizontal silhouette readable at small size, flat `#ff00ff` chroma-key background, no markings, flags, text, logos, extra objects, or shadows.

## Walk

A completely redrawn 4×4 sprite sheet containing a seamless 16-frame right-facing walk cycle. The first eight full-body keyframes form one exact loop and frames 9-16 repeat those keyframes pixel-for-pixel. Both hands remain below the waist and make a modest natural counter-swing close to the thighs; the hands are relaxed and hold no pebble or other object. Every frame contains one continuous full body from head through jacket, pelvis, legs, and shoes, with no cut line, gap, collage seam, or separate upper/lower-body layers.

Lock the head center, shoulders, jacket zipper, waist, pelvis, character scale, and ground baseline across all frames. Only the arms and legs articulate; no torso rocking, leaning, zooming, or vertical bounce. Keyframes 1-4 show the light leg making heel contact, loading, and passing while the dark leg swings forward. Keyframes 5-8 show the dark leg making heel contact, loading, and passing while the light leg swings forward. Contact poses must show one shoe far ahead and the other far behind. After generation, uniformly normalize each complete figure to one visible height and align all frames to one upper-body anchor and ground baseline using `scripts/stabilize_spritesheet.py --normalize-height`.

## Point

A 5×3 sprite sheet containing a coherent 15-frame sequence: stop, bend down, pick up a flower-bed pebble, straighten, then point upward at an application target. Preserve the walk-sheet character design exactly.

## Throw

A 5×3 sprite sheet containing a coherent 15-frame heroic throw. Frames 1–5 wind up, frame 6 releases the pebble diagonally upward, and frames 7–15 complete the follow-through and end in a confident skyward pose.

## Impact

A 5×3 sprite sheet containing a coherent 15-frame effect: a gray pebble approaches a generic cream-and-teal application window, strikes it, produces opaque golden sparks, cracks it into chunky geometric fragments, and sends the fragments downward.

## Victory

A 5×3 sprite sheet containing a coherent 15-frame sequence: watch the application fall, adjust the jacket, nod with satisfaction, then raise one hand in a dignified wave.

## Departure

A 5×3 sprite sheet containing a coherent 15-frame looping victory walk to the right while waving goodbye. Preserve the established character design and keep the first and last poses loop-compatible.

## Chroma-key constraints for all sprite sheets

Perfectly flat solid `#ff00ff` background; no shadows, gradients, floor plane, grid lines, borders, labels, numbers, text, watermarks, cropped limbs, or extra characters. Do not use the key color in the subject. Chroma sources were converted to RGBA PNGs using the image generation skill's `remove_chroma_key.py` helper with soft matte and despill.

## Happy cat

One 5x3 sprite sheet contains a consistent gray-and-white domestic kitten standing upright and swinging both front paws outward and overhead in a seamless cheering loop. A user-provided blurry cat photo was used only as a visual reference for the upright pose, natural anatomy, gray-and-white fur, low-resolution phone-video compression, soft focus, and slight paw motion blur. The room and objects from the reference were not reproduced. The result deliberately avoids illustration, cartoon, anime, mascot, and polished studio-photography aesthetics.

The application reuses this single sheet for four instances with `start_frame` values `0`, `3`, `6`, and `9` so their cheering remains rhythmically staggered.
