from unittest import TestCase

from task_tui.config import Config


class ConfigParsing(TestCase):
    pass


class ColorTestCase(TestCase):
    def test_color_from_word() -> None:
        Config._parse_colors("""
            color.active              blue on green
            color.alternate           on magenta
            color.blocked             white on white
            color.due                 red
            """)

    def test_inverse() -> None:
        pass
