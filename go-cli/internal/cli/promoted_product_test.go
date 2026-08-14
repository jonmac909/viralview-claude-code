package cli

import (
	"bytes"
	"encoding/json"
	"testing"
)

func TestProductDryRunReportsDryRunProvenance(t *testing.T) {
	root := newRootCmd(&rootFlags{})
	output := &bytes.Buffer{}
	root.SetOut(output)
	root.SetErr(output)
	root.SetArgs([]string{
		"product",
		"--url", "https://example.com",
		"--dry-run",
		"--json",
		"--home", t.TempDir(),
	})

	if err := root.Execute(); err != nil {
		t.Fatalf("product dry run failed: %v", err)
	}

	var envelope struct {
		Meta struct {
			Source string `json:"source"`
		} `json:"meta"`
	}
	if err := json.Unmarshal(output.Bytes(), &envelope); err != nil {
		t.Fatalf("decode product dry-run output: %v\n%s", err, output.String())
	}
	if envelope.Meta.Source != "dry-run" {
		t.Fatalf("product dry-run source = %q, want dry-run", envelope.Meta.Source)
	}
}
