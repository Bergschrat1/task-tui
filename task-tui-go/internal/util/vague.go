package util

import (
	"fmt"
	"math"
	"time"
)

// FormatVagueDuration formats a duration as a vague human-readable string.
func FormatVagueDuration(d time.Duration) string {
	sign := ""
	seconds := d.Seconds()
	if seconds < 0 {
		sign = "-"
		seconds = math.Abs(seconds)
	}

	days := seconds / 86400

	var value string
	switch {
	case seconds >= 86400*365:
		value = fmt.Sprintf("%.1fy", days/365)
	case seconds >= 86400*90:
		value = fmt.Sprintf("%dmo", int(days/30))
	case seconds >= 86400*14:
		value = fmt.Sprintf("%dw", int(days/7))
	case seconds >= 86400:
		value = fmt.Sprintf("%dd", int(days))
	case seconds >= 3600:
		value = fmt.Sprintf("%dh", int(seconds/3600))
	case seconds >= 60:
		value = fmt.Sprintf("%dmin", int(seconds/60))
	case seconds >= 1:
		value = fmt.Sprintf("%ds", int(seconds))
	default:
		return ""
	}

	return sign + value
}

// FormatVagueDatetime formats a time relative to now as a vague duration.
func FormatVagueDatetime(target *time.Time) string {
	if target == nil {
		return ""
	}
	delta := time.Until(*target)
	return FormatVagueDuration(delta)
}
