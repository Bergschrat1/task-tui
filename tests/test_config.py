import pytest
from rich.color import Color
from rich.style import Style

from task_tui.config import Config


class TestParseColorConfig:
    def test_color_attributes_are_found(self) -> None:
        styles = Config._parse_color_config("""
            foo
            color.active              blue
            color.alternate       blue
            color.blocked             blue
            foo.color.bar
            color.due.today              blue
            no.color     foo
            """)
        assert all(atr in styles for atr in ["active", "alternate", "blocked", "due.today"])
        assert "color" not in styles

    def test_parse_style_correctly_called(self) -> None:
        pass


class TestParseStyle:
    def test_only_foreground_color(self) -> None:
        style = Config._parse_style("blue")
        assert style == Style(color=Color.from_ansi(4), bgcolor=None)

    def test_fg_and_bg(self) -> None:
        style = Config._parse_style("blue on red")
        assert style == Style(color=Color.from_ansi(4), bgcolor=Color.from_ansi(1))

    def test_only_background(self) -> None:
        style = Config._parse_style("on red")
        assert style == Style(color=None, bgcolor=Color.from_ansi(1))

    def test_bold(self) -> None:
        style = Config._parse_style("bold red")
        assert style == Style(color=Color.from_ansi(1), bgcolor=None, bold=True)

    def test_modifier_position(self) -> None:
        style = Config._parse_style("red bold")
        assert style == Style(color=Color.from_ansi(1), bgcolor=None, bold=True)

    def test_underline(self) -> None:
        style = Config._parse_style("underline red")
        assert style == Style(color=Color.from_ansi(1), bgcolor=None, underline=True)

    def test_inverse(self) -> None:
        style = Config._parse_style("inverse red on blue")
        assert style == Style(color=Color.from_ansi(4), bgcolor=Color.from_ansi(1))

    def test_all_modifiers(self) -> None:
        style = Config._parse_style("bold underline inverse red")
        assert style == Style(color=None, bgcolor=Color.from_ansi(1), underline=True, bold=True)


class TestParseColor:
    @pytest.mark.parametrize(
        "color,expected_index",
        [
            ("black", 0),
            ("red", 1),
            ("green", 2),
            ("yellow", 3),
            ("blue", 4),
            ("magenta", 5),
            ("cyan", 6),
            ("white", 7),
        ],
    )
    def test_words_are_parsed(self, color: str, expected_index: int) -> None:
        parsed_color = Config._parse_color(color)
        assert parsed_color == Color.from_ansi(expected_index)

    @pytest.mark.parametrize(
        "color,expected_index",
        [
            ("bright black", 8),
            ("bright red", 9),
            ("bright green", 10),
            ("bright yellow", 11),
            ("bright blue", 12),
            ("bright magenta", 13),
            ("bright cyan", 14),
            ("bright white", 15),
        ],
    )
    def test_bright_words_are_parsed(self, color: str, expected_index: int) -> None:
        parsed_color = Config._parse_color(color)
        assert parsed_color == Color.from_ansi(expected_index)

    @pytest.mark.parametrize(
        "color_str,expected_index",
        [
            ("color17", 17),
            ("color141", 141),
            ("color200", 200),
        ],
    )
    def test_colorN_is_parsed(self, color_str: str, expected_index: int) -> None:
        parsed_color = Config._parse_color(color_str)
        assert parsed_color == Color.from_ansi(expected_index)

    @pytest.mark.parametrize(
        "rgb,expected_index",
        [
            ("rgb000", 16),
            ("rgb105", 16 + 1 * 36 + 0 * 6 + 5),  # 57
            ("rgb540", 16 + 5 * 36 + 4 * 6 + 0),  # 238
        ],
    )
    def test_rgb_is_parsed(self, rgb: str, expected_index: int) -> None:
        parsed_color = Config._parse_color(rgb)
        assert parsed_color == Color.from_ansi(expected_index)

    @pytest.mark.parametrize(
        "gray,expected_index",
        [
            ("gray0", 232),
            ("gray11", 243),
            ("gray23", 255),
        ],
    )
    def test_gray_is_parsed(self, gray: str, expected_index: int) -> None:
        parsed_color = Config._parse_color(gray)
        assert parsed_color == Color.from_ansi(expected_index)

    def test_invalid_color_raises_error(self) -> None:
        with pytest.raises(ValueError, match=r"Unknown color invalid"):
            Config._parse_color("invalid")
