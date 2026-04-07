package taskwarrior

import (
	"fmt"
	"strconv"
	"strings"

	"charm.land/lipgloss/v2"
)

// TaskStyle holds parsed color attributes for a taskwarrior color rule.
type TaskStyle struct {
	Fg        *int // ANSI color code 0-255, nil if unset
	Bg        *int // ANSI color code 0-255, nil if unset
	Bold      bool
	Underline bool
}

// Merge returns a new TaskStyle where other's non-zero fields override.
func (s TaskStyle) Merge(other TaskStyle) TaskStyle {
	result := s
	if other.Fg != nil {
		result.Fg = other.Fg
	}
	if other.Bg != nil {
		result.Bg = other.Bg
	}
	if other.Bold {
		result.Bold = true
	}
	if other.Underline {
		result.Underline = true
	}
	return result
}

// ToLipgloss converts to a lipgloss.Style.
func (s TaskStyle) ToLipgloss() lipgloss.Style {
	style := lipgloss.NewStyle()
	if s.Fg != nil {
		style = style.Foreground(lipgloss.ANSIColor(*s.Fg))
	}
	if s.Bg != nil {
		style = style.Background(lipgloss.ANSIColor(*s.Bg))
	}
	if s.Bold {
		style = style.Bold(true)
	}
	if s.Underline {
		style = style.Underline(true)
	}
	return style
}

var colorIndexes = map[string]int{
	"black":   0,
	"red":     1,
	"green":   2,
	"yellow":  3,
	"blue":    4,
	"magenta": 5,
	"cyan":    6,
	"white":   7,
}

// ParseColorConfig extracts color rules from `task show` output.
func ParseColorConfig(output string) map[string]TaskStyle {
	colors := make(map[string]TaskStyle)
	for _, line := range strings.Split(output, "\n") {
		line = strings.TrimSpace(line)
		if !strings.HasPrefix(line, "color.") {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) < 2 {
			continue
		}
		// Extract attribute name after first dot: "color.overdue" -> "overdue"
		attribute := strings.SplitN(parts[0], ".", 2)[1]
		colorSpec := strings.Join(parts[1:], " ")
		style := parseStyle(colorSpec)
		colors[attribute] = style
	}
	return colors
}

// parseStyle parses a taskwarrior style string like "bold red on blue".
func parseStyle(styleConfig string) TaskStyle {
	var s TaskStyle

	// Extract modifiers
	inverse := false
	if strings.Contains(styleConfig, "bold") {
		s.Bold = true
		styleConfig = strings.ReplaceAll(styleConfig, "bold", "")
	}
	if strings.Contains(styleConfig, "underline") {
		s.Underline = true
		styleConfig = strings.ReplaceAll(styleConfig, "underline", "")
	}
	if strings.Contains(styleConfig, "inverse") {
		inverse = true
		styleConfig = strings.ReplaceAll(styleConfig, "inverse", "")
	}
	styleConfig = strings.TrimSpace(styleConfig)

	// Split on " on " for foreground/background
	parts := strings.SplitN(styleConfig, " on ", 2)
	if fg := strings.TrimSpace(parts[0]); fg != "" {
		if code, err := parseColor(fg); err == nil {
			s.Fg = &code
		}
	}
	if len(parts) == 2 {
		if bg := strings.TrimSpace(parts[1]); bg != "" {
			if code, err := parseColor(bg); err == nil {
				s.Bg = &code
			}
		}
	}

	// Apply inverse: swap fg and bg
	if inverse {
		s.Fg, s.Bg = s.Bg, s.Fg
	}

	return s
}

// parseColor parses a taskwarrior color string into an ANSI color code.
func parseColor(colorStr string) (int, error) {
	colorStr = strings.TrimSpace(colorStr)

	// Check for "bright" prefix
	bright := false
	if strings.HasPrefix(colorStr, "bright") {
		bright = true
		colorStr = strings.TrimSpace(strings.TrimPrefix(colorStr, "bright"))
	}

	// Named colors
	if code, ok := colorIndexes[colorStr]; ok {
		if bright {
			code += 8
		}
		return code, nil
	}

	// color<N> format (0-255)
	if strings.HasPrefix(colorStr, "color") {
		numStr := strings.TrimPrefix(colorStr, "color")
		code, err := strconv.Atoi(strings.TrimSpace(numStr))
		if err != nil {
			return 0, fmt.Errorf("invalid color code: %s", colorStr)
		}
		return code, nil
	}

	// rgb<R><G><B> format (each digit 0-5)
	if strings.HasPrefix(colorStr, "rgb") && len(colorStr) == 6 {
		r := int(colorStr[3] - '0')
		g := int(colorStr[4] - '0')
		b := int(colorStr[5] - '0')
		return 16 + r*36 + g*6 + b, nil
	}

	// gray<N> format (0-23)
	if strings.HasPrefix(colorStr, "gray") {
		numStr := colorStr[4:]
		code, err := strconv.Atoi(numStr)
		if err != nil {
			return 0, fmt.Errorf("invalid gray code: %s", colorStr)
		}
		return 232 + code, nil
	}

	return 0, fmt.Errorf("unknown color: %s", colorStr)
}
