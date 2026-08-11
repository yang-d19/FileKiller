import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QWidget

from filekiller.animation import SpriteAnimator, SpriteLoader
from filekiller.config import ResourceConfig
from filekiller.effects import AnimationGroupController
from filekiller.widgets import ChoicesWidget
from filekiller.window import FileKillerWindow, _walking_progress


class SpriteAnimatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_adjacent_stabilized_clips_share_one_screen_anchor(self):
        project_root = Path(__file__).resolve().parents[1]
        resources = ResourceConfig.load(
            project_root / "config" / "grandpa-stone.json"
        )
        animator = SpriteAnimator()
        animator.move(100, 50)
        loader = SpriteLoader(resources)

        screen_anchors = []
        for name in ("point", "kick", "arrival"):
            loader.load_named(animator, name)
            for index in range(len(animator.frames)):
                animator.current_frame = index
                animator._update_frame()
                screen_anchors.append(
                    animator.x() + animator._frame_anchors_x[index]
                )

        self.assertEqual(len(set(screen_anchors)), 1)

        loader.load_named(animator, "departure")
        self.assertTrue(animator.stabilize_x)
        animator.motion_position = QPoint(300, 50)
        departure_anchors = []
        for index in range(len(animator.frames)):
            animator.current_frame = index
            animator._update_frame()
            departure_anchors.append(
                animator.x() + animator._frame_anchors_x[index]
            )
        self.assertEqual(len(set(departure_anchors)), 1)

        loader.load_named(animator, "walk")
        self.assertFalse(animator.stabilize_x)
        self.assertEqual(animator.pos(), QPoint(300, 50))

    def test_walking_speed_wave_always_moves_forward(self):
        values = [
            _walking_progress(index / 240, cycles=6, strength=0.28)
            for index in range(241)
        ]
        steps = [right - left for left, right in zip(values, values[1:])]

        self.assertAlmostEqual(values[0], 0.0)
        self.assertAlmostEqual(values[-1], 1.0)
        self.assertTrue(all(step > 0 for step in steps))
        self.assertGreater(max(steps), min(steps) * 1.5)

    def test_below_target_cats_jump_in_a_staggered_wave(self):
        project_root = Path(__file__).resolve().parents[1]
        resources = ResourceConfig.load(
            project_root / "config" / "grandpa-stone.json"
        )
        group = resources.animation_group("below_target")
        host = QWidget()
        host.resize(1200, 800)
        controller = AnimationGroupController(host, SpriteLoader(resources))
        self.addCleanup(controller.stop)

        controller.start(QPoint(600, 200), group)
        self.assertEqual(len(controller.animators), 6)

        controller._apply_bounce(group["bounce_period_ms"] // 4)
        jumps = [
            base.y() - animator.y()
            for animator, base in zip(
                controller.animators, controller.base_positions
            )
        ]

        self.assertEqual(jumps[0], group["bounce_height"])
        self.assertTrue(all(0 <= jump <= group["bounce_height"] for jump in jumps))
        self.assertGreater(len(set(jumps)), 1)

    def test_confirmation_buttons_include_matching_emoji(self):
        choices = ChoicesWidget()
        self.addCleanup(choices.close)

        self.assertEqual(choices.btn1.text(), "是的 😡")
        self.assertEqual(choices.btn2.text(), "嘤嘤嘤就是这个 🥺")

    def test_choices_appear_after_the_theme_delay(self):
        project_root = Path(__file__).resolve().parents[1]
        resources = ResourceConfig.load(
            project_root / "config" / "grandpa-stone.json"
        )
        window = FileKillerWindow(None, resources)
        self.addCleanup(window.close)

        window.show_dialog()
        self.assertTrue(window.bubble.isVisible())
        self.assertFalse(window.choices.isVisible())
        self.assertTrue(window.choice_timer.isActive())

        QTest.qWait(resources.choice_delay_ms + 50)
        self.assertTrue(window.choices.isVisible())
        self.assertFalse(window.choice_timer.isActive())


if __name__ == "__main__":
    unittest.main()
