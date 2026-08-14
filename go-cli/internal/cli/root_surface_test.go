package cli

import "testing"

func TestRootExposesOnlyReviewedViralViewCommands(t *testing.T) {
	root := newRootCmd(&rootFlags{})
	names := map[string]bool{}
	for _, command := range root.Commands() {
		names[command.Name()] = true
	}

	for _, name := range []string{
		"account",
		"agent-context",
		"api",
		"auth",
		"doctor",
		"library",
		"product",
		"projects",
		"task-status",
		"which",
	} {
		if !names[name] {
			t.Errorf("reviewed command %q is missing", name)
		}
	}

	for _, name := range []string{
		"export",
		"feedback",
		"import",
		"jobs",
		"load",
		"orphans",
		"profile",
		"search",
		"stale",
		"sync",
		"workflow",
	} {
		if names[name] {
			t.Errorf("unreviewed framework command %q is exposed", name)
		}
	}
}
