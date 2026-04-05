package taskwarrior

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

type Status string

const (
	StatusPending   Status = "pending"
	StatusCompleted Status = "completed"
	StatusDeleted   Status = "deleted"
	StatusWaiting   Status = "waiting"
	StatusRecurring Status = "recurring"
)

type VirtualTag string

const (
	VTagActive    VirtualTag = "active"
	VTagBlocked   VirtualTag = "blocked"
	VTagBlocking  VirtualTag = "blocking"
	VTagCompleted VirtualTag = "completed"
	VTagDeleted   VirtualTag = "deleted"
	VTagDue       VirtualTag = "due"
	VTagDueToday  VirtualTag = "due.today"
	VTagNoProject VirtualTag = "project.none"
	VTagNoTag     VirtualTag = "tag.none"
	VTagOverdue   VirtualTag = "overdue"
	VTagPriority  VirtualTag = "priority"
	VTagRecurring VirtualTag = "recurring"
	VTagScheduled VirtualTag = "scheduled"
	VTagTagged    VirtualTag = "tagged"
	VTagUntil     VirtualTag = "until"
	VTagWaiting   VirtualTag = "waiting"
)

// TaskTime wraps time.Time for custom JSON unmarshaling of Taskwarrior's ISO format.
type TaskTime struct {
	time.Time
}

func (t *TaskTime) UnmarshalJSON(data []byte) error {
	var s string
	if err := json.Unmarshal(data, &s); err != nil {
		return err
	}
	// Taskwarrior uses format: 20240115T120000Z
	parsed, err := time.Parse("20060102T150405Z", s)
	if err != nil {
		// Fallback to ISO 8601
		parsed, err = time.Parse(time.RFC3339, s)
		if err != nil {
			return fmt.Errorf("cannot parse time %q: %w", s, err)
		}
	}
	t.Time = parsed
	return nil
}

type Annotation struct {
	Entry       *TaskTime `json:"entry,omitempty"`
	Description string    `json:"description"`
}

type Task struct {
	ID          int          `json:"id"`
	UUID        string       `json:"uuid"`
	Description string       `json:"description"`
	Status      Status       `json:"status"`
	Entry       TaskTime     `json:"entry"`
	Modified    TaskTime     `json:"modified"`
	Urgency     float64      `json:"urgency"`
	Due         *TaskTime    `json:"due,omitempty"`
	Start       *TaskTime    `json:"start,omitempty"`
	Scheduled   *TaskTime    `json:"scheduled,omitempty"`
	Wait        *TaskTime    `json:"wait,omitempty"`
	End         *TaskTime    `json:"end,omitempty"`
	Until       *TaskTime    `json:"until,omitempty"`
	Reviewed    *TaskTime    `json:"reviewed,omitempty"`
	Project     *string      `json:"project,omitempty"`
	Priority    *string      `json:"priority,omitempty"`
	Recur       *string      `json:"recur,omitempty"`
	Tags        []string     `json:"tags,omitempty"`
	Depends     []string     `json:"depends,omitempty"`
	Annotations []Annotation `json:"annotations,omitempty"`
	VirtualTags map[VirtualTag]bool `json:"-"`
}

// HasTag checks if the task has a specific user tag.
func (t *Task) HasTag(tag string) bool {
	for _, tt := range t.Tags {
		if tt == tag {
			return true
		}
	}
	return false
}

// TagsString returns comma-separated tags.
func (t *Task) TagsString() string {
	return strings.Join(t.Tags, ",")
}

// ProjectString returns the project name or empty string.
func (t *Task) ProjectString() string {
	if t.Project != nil {
		return *t.Project
	}
	return ""
}

// PriorityString returns the priority or empty string.
func (t *Task) PriorityString() string {
	if t.Priority != nil {
		return *t.Priority
	}
	return ""
}

type ContextInfo struct {
	Name       string
	ReadFilter string
	IsActive   bool
}
