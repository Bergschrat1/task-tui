package tui

import (
	"strings"

	"task-tui-go/internal/taskwarrior"
)

// allVirtualTags lists all virtual tags for iteration during style resolution.
var allVirtualTags = []taskwarrior.VirtualTag{
	taskwarrior.VTagActive,
	taskwarrior.VTagBlocked,
	taskwarrior.VTagBlocking,
	taskwarrior.VTagCompleted,
	taskwarrior.VTagDeleted,
	taskwarrior.VTagDue,
	taskwarrior.VTagDueToday,
	taskwarrior.VTagNoProject,
	taskwarrior.VTagNoTag,
	taskwarrior.VTagOverdue,
	taskwarrior.VTagPriority,
	taskwarrior.VTagRecurring,
	taskwarrior.VTagScheduled,
	taskwarrior.VTagTagged,
	taskwarrior.VTagUntil,
	taskwarrior.VTagWaiting,
}

// resolveTaskStyle computes the composite style for a task based on its virtual tags
// and the taskwarrior color precedence rules.
func resolveTaskStyle(task *taskwarrior.Task, cfg *taskwarrior.Config) taskwarrior.TaskStyle {
	// Build map of applicable styles from virtual tags
	candidates := make(map[string]taskwarrior.TaskStyle)
	for _, tag := range allVirtualTags {
		if task.VirtualTags[tag] {
			if style, ok := cfg.Colors[string(tag)]; ok {
				candidates[string(tag)] = style
			}
		}
	}

	// Apply styles in reverse precedence order (lowest priority first, highest last)
	precedence := strings.Split(cfg.ColorPrecedence, ",")
	// Reverse the list
	for i, j := 0, len(precedence)-1; i < j; i, j = i+1, j-1 {
		precedence[i], precedence[j] = precedence[j], precedence[i]
	}

	var result taskwarrior.TaskStyle
	for _, entry := range precedence {
		entry = strings.TrimRight(entry, ".")
		if style, ok := candidates[entry]; ok {
			result = result.Merge(style)
		}
	}

	return result
}
