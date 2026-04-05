package taskwarrior

import (
	"strconv"
	"strings"
)

type Config struct {
	Due             int
	ColorPrecedence string
}

// ParseConfig extracts configuration values from `task show` output.
func ParseConfig(output string) Config {
	cfg := Config{
		Due:             7,
		ColorPrecedence: "deleted,completed,active,keyword.,tag.,project.,overdue,scheduled,due.today,due,blocked,blocking,recurring,tagged,uda.",
	}

	for _, line := range strings.Split(output, "\n") {
		line = strings.TrimSpace(line)

		if strings.HasPrefix(line, "due") {
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				if v, err := strconv.Atoi(parts[len(parts)-1]); err == nil {
					cfg.Due = v
				}
			}
		}

		if strings.HasPrefix(line, "rule.precedence.color") {
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				cfg.ColorPrecedence = parts[len(parts)-1]
			}
		}
	}

	return cfg
}
