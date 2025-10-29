# ruff: noqa: F841
from rich.color import Color
from rich.style import Style

COLOR_INDEXES = {
    "black": 0,
    "red": 1,
    "green": 2,
    "yellow": 3,
    "blue": 4,
    "magenta": 5,
    "cyan": 6,
    "white": 7,
}


class Config:
    color: dict[str, Style]

    def __init__(self, config_data: str) -> None:
        self.color = self._parse_colors(config_data)

    def _parse_colors(self, config_data: str) -> dict[str, Style]:
        color_config: dict[str, Style] = {}
        for config_line in config_data.split("\n"):
            config_line = config_line.strip()
            if not config_line.startswith("color."):
                continue
            config_line_split = config_line.split()
            attribute = config_line_split[0].split(".", maxsplit=1)[1]
            config_line_colors = " ".join(config_line_split[1:])
            style = self._parse_style(config_line_colors)
            color_config[attribute] = style
        return color_config

    def _parse_style(self, style_config: str) -> Style:
        fg: Color | None = None
        bg: Color | None = None
        bold: bool | None = None
        underline: bool | None = None
        inverse: bool = False
        if "bold" in style_config:
            bold = True
            style_config = style_config.replace("bold", "").strip()
        if "underline" in style_config:
            underline = True
            style_config = style_config.replace("underline", "").strip()
        if "inverse" in style_config:
            inverse = True
            style_config = style_config.replace("inverse", "").strip()
        fb_bg_split = style_config.split("on ")
        len_color_conf = len(fb_bg_split)
        if len_color_conf == 1:
            fg_color = self._parse_color(fb_bg_split[0])

        ret = Style(color=fg)

    def _parse_color(self, color_str: str) -> Color:
        bright = True if "bright" in color_str else False
        color_str = color_str.replace("bright", "").strip()
        if color_str in COLOR_INDEXES:
            color_code = COLOR_INDEXES[color_str]
            if bright:
                color_code += 8
        elif color_str.startswith("color"):
            color_code = int(color_str.replace("color", "").strip())
            # TODO consider bright
        elif color_str.startswith("rgb"):
            red = int(color_str[3])
            green = int(color_str[4])
            blue = int(color_str[5])
            color_code = 16 + red * 36 + green * 6 + blue
        elif color_str.startswith("gray"):
            pass
        else:
            raise ValueError(f"Unknown color {color_str}")

        return Color.from_ansi(color_code)
