"""Align sprite frames to a stable upper-body anchor and ground baseline."""

import argparse
import statistics
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image


def remove_small_edge_components(frame, alpha_threshold=8):
    """Remove small disconnected fragments bleeding in from adjacent cells."""
    pixels = np.asarray(frame).copy()
    mask = pixels[:, :, 3] > alpha_threshold
    visited = np.zeros(mask.shape, dtype=bool)
    components = []
    height, width = mask.shape

    for seed_y, seed_x in np.argwhere(mask):
        if visited[seed_y, seed_x]:
            continue
        queue = deque([(int(seed_y), int(seed_x))])
        visited[seed_y, seed_x] = True
        component = []
        touches_edge = False

        while queue:
            y, x = queue.popleft()
            component.append((y, x))
            touches_edge = touches_edge or x == 0 or x == width - 1
            for next_y in range(max(0, y - 1), min(height, y + 2)):
                for next_x in range(max(0, x - 1), min(width, x + 2)):
                    if mask[next_y, next_x] and not visited[next_y, next_x]:
                        visited[next_y, next_x] = True
                        queue.append((next_y, next_x))

        components.append((component, touches_edge))

    largest = max((len(component) for component, _touches in components), default=0)
    for component, touches_edge in components:
        if touches_edge and len(component) < largest * 0.15:
            ys, xs = zip(*component)
            pixels[np.asarray(ys), np.asarray(xs), :] = 0

    return Image.fromarray(pixels, "RGBA")


def frame_anchor(frame, alpha_threshold=24, upper_fraction=0.42):
    alpha = np.asarray(frame.getchannel("A"))
    ys, xs = np.nonzero(alpha > alpha_threshold)
    if not len(xs):
        raise ValueError("Sprite frame contains no visible pixels")

    top = int(ys.min())
    bottom = int(ys.max())
    upper_limit = top + (bottom - top) * upper_fraction
    upper_xs = xs[ys <= upper_limit]
    return float(np.median(upper_xs)), bottom, int(xs.min()), int(xs.max())


def normalize_visible_height(frame, target_height, alpha_threshold=24):
    """Uniformly scale one complete body without splitting or compositing it."""
    alpha = np.asarray(frame.getchannel("A"))
    ys, xs = np.nonzero(alpha > alpha_threshold)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    visible = frame.crop(box)
    scale = target_height / visible.height
    width = round(visible.width * scale)
    visible = visible.resize((width, target_height), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    x = (frame.width - visible.width) // 2
    y = frame.height - visible.height
    canvas.alpha_composite(visible, (x, y))
    return canvas


def stabilize(source, destination, cols, rows, normalize_height=False):
    sheet = Image.open(source).convert("RGBA")
    frame_width = sheet.width // cols
    frame_height = sheet.height // rows

    frames = []
    anchors = []
    for row in range(rows):
        for col in range(cols):
            box = (
                col * frame_width,
                row * frame_height,
                (col + 1) * frame_width,
                (row + 1) * frame_height,
            )
            frame = remove_small_edge_components(sheet.crop(box))
            frames.append(frame)
            anchors.append(frame_anchor(frame))

    if normalize_height:
        visible_heights = []
        for frame in frames:
            alpha = np.asarray(frame.getchannel("A"))
            ys, _xs = np.nonzero(alpha > 24)
            visible_heights.append(int(ys.max()) - int(ys.min()) + 1)
        target_height = round(statistics.median(visible_heights))
        frames = [normalize_visible_height(frame, target_height) for frame in frames]
        anchors = [frame_anchor(frame) for frame in frames]

    target_x = statistics.median(anchor[0] for anchor in anchors)
    safe_min_x = max(anchor_x - left for anchor_x, _bottom, left, _right in anchors)
    safe_max_x = min(
        anchor_x + (frame_width - 1 - right)
        for anchor_x, _bottom, _left, right in anchors
    )
    if safe_min_x > safe_max_x:
        raise ValueError("Frames have no shared horizontal anchor without clipping")
    target_x = min(max(target_x, safe_min_x), safe_max_x)
    target_bottom = round(statistics.median(anchor[1] for anchor in anchors))
    output = Image.new("RGBA", sheet.size, (0, 0, 0, 0))

    shifts = []
    for index, (frame, (anchor_x, bottom, _left, _right)) in enumerate(
        zip(frames, anchors)
    ):
        shift_x = round(target_x - anchor_x)
        shift_y = target_bottom - bottom
        shifts.append((shift_x, shift_y))

        aligned = Image.new("RGBA", (frame_width, frame_height), (0, 0, 0, 0))
        aligned.alpha_composite(frame, (shift_x, shift_y))
        col = index % cols
        row = index // cols
        output.alpha_composite(aligned, (col * frame_width, row * frame_height))

    destination.parent.mkdir(parents=True, exist_ok=True)
    output.save(destination, optimize=True)
    return target_x, target_bottom, shifts


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Stabilize a transparent sprite sheet around its upper body."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--cols", type=int, default=5)
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument(
        "--normalize-height",
        action="store_true",
        help="Uniformly scale each complete figure to the median visible height.",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    target_x, target_bottom, shifts = stabilize(
        args.source,
        args.destination,
        args.cols,
        args.rows,
        normalize_height=args.normalize_height,
    )
    print(f"Anchor x={target_x:.1f}, ground={target_bottom}, shifts={shifts}")


if __name__ == "__main__":
    main()
