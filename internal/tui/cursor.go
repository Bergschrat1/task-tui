package tui

import (
	"strings"

	"charm.land/bubbles/v2/key"
	tea "charm.land/bubbletea/v2"
)

// cursorState manages cursor position and scrolling for stateless table views.
type cursorState struct {
	cursor int
	total  int
	height int
}

func (c *cursorState) handleKey(msg tea.KeyPressMsg) {
	if c.total == 0 {
		return
	}

	switch {
	case key.Matches(msg, keys.Up):
		if c.cursor > 0 {
			c.cursor--
		}
	case key.Matches(msg, keys.Down):
		if c.cursor < c.total-1 {
			c.cursor++
		}
	case key.Matches(msg, keys.PageUp):
		c.cursor -= c.pageSize()
		if c.cursor < 0 {
			c.cursor = 0
		}
	case key.Matches(msg, keys.PageDown):
		c.cursor += c.pageSize()
		if c.cursor >= c.total {
			c.cursor = c.total - 1
		}
	case key.Matches(msg, keys.GoTop):
		c.cursor = 0
	case key.Matches(msg, keys.GoBottom):
		c.cursor = c.total - 1
	}
}

func (c *cursorState) visibleRows() int {
	v := c.height - 4
	if v < 1 {
		return 1
	}
	return v
}

func (c *cursorState) pageSize() int {
	visible := c.visibleRows()
	if visible < 1 {
		return 1
	}
	return visible / 2
}

func (c *cursorState) scrollOffset() int {
	visible := c.visibleRows()
	if c.cursor >= visible {
		return c.cursor - visible + 1
	}
	return 0
}

// underlineRow wraps the cursor row's line in the rendered table with ANSI
// underline codes so the underline spans the full table width.
func (c *cursorState) underlineRow(rendered string) string {
	lines := strings.Split(rendered, "\n")
	// +2 accounts for header text line and header border line
	idx := c.cursor - c.scrollOffset() + 2
	if idx >= 0 && idx < len(lines) {
		// Replace ANSI resets with reset+underline so underline persists
		// through per-cell color styles. termenv emits \033[m (not \033[0m).
		line := strings.ReplaceAll(lines[idx], "\033[m", "\033[4m")
		lines[idx] = "\033[4m" + line + "\033[m"
	}
	return strings.Join(lines, "\n")
}

func (c *cursorState) clamp() {
	if c.total == 0 {
		c.cursor = 0
		return
	}
	if c.cursor >= c.total {
		c.cursor = c.total - 1
	}
	if c.cursor < 0 {
		c.cursor = 0
	}
}
