package taskwarrior

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"regexp"
	"strconv"
	"strings"
	"time"

	"charm.land/log/v2"
)

var createdTaskRe = regexp.MustCompile(`Created task (\d+)`)

type TaskCli struct {
	command    string
	configRaw  string
	config     *Config
}

func NewTaskCli() (*TaskCli, error) {
	cli := &TaskCli{command: "task"}

	// Validate taskwarrior is installed and cache config
	out, err := cli.runTask("show")
	if err != nil {
		return nil, fmt.Errorf("taskwarrior not found or failed: %w", err)
	}
	cli.configRaw = out

	cfg := ParseConfig(out)
	cli.config = &cfg

	return cli, nil
}

func (c *TaskCli) GetConfig() *Config {
	return c.config
}

func (c *TaskCli) runTask(args ...string) (string, error) {
	start := time.Now()
	cmd := exec.Command(c.command, args...)
	out, err := cmd.Output()
	duration := time.Since(start)
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			log.Error("task command failed", "args", args, "duration", duration, "stderr", string(exitErr.Stderr))
			return string(out), fmt.Errorf("task %s failed: %s", strings.Join(args, " "), string(exitErr.Stderr))
		}
		log.Error("task command error", "args", args, "err", err)
		return "", err
	}
	log.Debug("task command", "args", args, "duration", duration)
	return string(out), nil
}

func (c *TaskCli) runTaskCheck(args ...string) error {
	start := time.Now()
	cmd := exec.Command(c.command, args...)
	out, err := cmd.CombinedOutput()
	duration := time.Since(start)
	if err != nil {
		log.Error("task command failed", "args", args, "duration", duration, "output", string(out))
		return fmt.Errorf("task %s failed: %s", strings.Join(args, " "), string(out))
	}
	log.Debug("task command", "args", args, "duration", duration)
	return nil
}

func (c *TaskCli) getConfigValue(key string) string {
	out, err := c.runTask("_get", key)
	if err != nil {
		return ""
	}
	return strings.TrimSpace(out)
}

func (c *TaskCli) getContextFilter(contextName string) string {
	filter := c.getConfigValue(fmt.Sprintf("rc.context.%s.read", contextName))
	if filter == "" {
		filter = c.getConfigValue(fmt.Sprintf("rc.context.%s", contextName))
	}
	return filter
}

// ExportTasks exports tasks for a given report, applying the active context filter.
func (c *TaskCli) ExportTasks(report string) ([]Task, error) {
	args := []string{"rc.json.array=0", "rc.defaultheight=0"}

	// Apply context filter if set
	ctx := c.GetContext()
	if ctx != nil {
		filter := c.getContextFilter(ctx.Name)
		if filter != "" {
			args = append(args, strings.Fields(filter)...)
		}
	}

	args = append(args, "export")
	if report != "" {
		args = append(args, report)
	}

	out, err := c.runTask(args...)
	if err != nil {
		return nil, err
	}

	return parseTasks(out)
}

// ExportAllTasks exports all tasks (for project aggregation).
func (c *TaskCli) ExportAllTasks() ([]Task, error) {
	args := []string{"rc.json.array=0", "rc.defaultheight=0", "export"}
	out, err := c.runTask(args...)
	if err != nil {
		return nil, err
	}
	return parseTasks(out)
}

func parseTasks(output string) ([]Task, error) {
	var tasks []Task
	for _, line := range strings.Split(strings.TrimSpace(output), "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		var task Task
		if err := json.Unmarshal([]byte(line), &task); err != nil {
			continue // skip unparseable lines
		}
		task.VirtualTags = make(map[VirtualTag]bool)
		tasks = append(tasks, task)
	}
	return tasks, nil
}

// GetReportColumns returns column names and labels for a report.
func (c *TaskCli) GetReportColumns(report string) ([]string, []string, error) {
	colOut, err := c.runTask("show", "rc.defaultwidth=0", fmt.Sprintf("report.%s.columns", report))
	if err != nil {
		return nil, nil, err
	}
	lblOut, err := c.runTask("show", "rc.defaultwidth=0", fmt.Sprintf("report.%s.labels", report))
	if err != nil {
		return nil, nil, err
	}

	columns := parseShowValue(colOut, fmt.Sprintf("report.%s.columns", report))
	labels := parseShowValue(lblOut, fmt.Sprintf("report.%s.labels", report))

	colList := strings.Split(columns, ",")
	lblList := strings.Split(labels, ",")

	// Strip format suffixes from column names (e.g., "due.relative" -> "due")
	for i, col := range colList {
		if idx := strings.Index(col, "."); idx != -1 {
			colList[i] = col[:idx]
		}
	}

	return colList, lblList, nil
}

// parseShowValue extracts the value for a key from `task show` output.
func parseShowValue(output, key string) string {
	for _, line := range strings.Split(output, "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, key) {
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				return parts[len(parts)-1]
			}
		}
	}
	return ""
}

// AddTask creates a new task and returns the task ID.
func (c *TaskCli) AddTask(description string) (int, error) {
	args := append([]string{"add"}, strings.Fields(description)...)
	out, err := c.runTask(args...)
	if err != nil {
		return 0, fmt.Errorf("failed to add task: %w", err)
	}

	matches := createdTaskRe.FindStringSubmatch(out)
	if len(matches) < 2 {
		return 0, fmt.Errorf("could not parse task ID from output: %s", out)
	}

	id, _ := strconv.Atoi(matches[1])
	return id, nil
}

// SetTaskDone marks a task as completed.
func (c *TaskCli) SetTaskDone(task *Task) error {
	return c.runTaskCheck(task.UUID, "done")
}

// StartTask starts a task.
func (c *TaskCli) StartTask(task *Task) error {
	return c.runTaskCheck(task.UUID, "start")
}

// StopTask stops a task.
func (c *TaskCli) StopTask(task *Task) error {
	return c.runTaskCheck(task.UUID, "stop")
}

// DeleteTask deletes a task with no confirmation.
func (c *TaskCli) DeleteTask(task *Task) error {
	return c.runTaskCheck("rc.confirmation=off", "rc.recurrence.confirmation=no", strconv.Itoa(task.ID), "delete")
}

// ModifyTask modifies a task with the given modification string.
func (c *TaskCli) ModifyTask(task *Task, modification string) error {
	args := []string{task.UUID, "modify"}
	args = append(args, strings.Fields(modification)...)
	return c.runTaskCheck(args...)
}

// AnnotateTask adds an annotation to a task.
func (c *TaskCli) AnnotateTask(task *Task, annotation string) error {
	return c.runTaskCheck(task.UUID, "annotate", annotation)
}

// LogTask logs a completed task.
func (c *TaskCli) LogTask(description string) error {
	args := append([]string{"log"}, strings.Fields(description)...)
	return c.runTaskCheck(args...)
}

// EditTask opens a task in $EDITOR. Returns the command to exec.
func (c *TaskCli) EditTaskCmd(task *Task) *exec.Cmd {
	return exec.Command(c.command, task.UUID, "edit")
}

// GetContext returns the currently active context, or nil.
func (c *TaskCli) GetContext() *ContextInfo {
	name := c.getConfigValue("rc.context")
	if name == "" || name == "none" {
		return nil
	}
	filter := c.getContextFilter(name)
	return &ContextInfo{
		Name:       name,
		ReadFilter: filter,
		IsActive:   true,
	}
}

// ListContexts returns all available contexts.
func (c *TaskCli) ListContexts() []ContextInfo {
	out, err := c.runTask("_context")
	if err != nil {
		return nil
	}

	activeCtx := c.GetContext()
	activeName := ""
	if activeCtx != nil {
		activeName = activeCtx.Name
	}

	var contexts []ContextInfo
	// Always include "none" option
	contexts = append(contexts, ContextInfo{
		Name:       "none",
		ReadFilter: "",
		IsActive:   activeName == "",
	})

	for _, line := range strings.Split(strings.TrimSpace(out), "\n") {
		name := strings.TrimSpace(line)
		if name == "" {
			continue
		}
		filter := c.getContextFilter(name)
		contexts = append(contexts, ContextInfo{
			Name:       name,
			ReadFilter: filter,
			IsActive:   name == activeName,
		})
	}

	return contexts
}

// SetContext switches the active context.
func (c *TaskCli) SetContext(name string) error {
	if name == "" || name == "none" {
		return c.runTaskCheck("context", "none")
	}
	return c.runTaskCheck("context", name)
}

// EditTask opens the task in $EDITOR by running the command with stdin/stdout attached.
func (c *TaskCli) EditTask(task *Task) error {
	cmd := exec.Command(c.command, task.UUID, "edit")
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}
