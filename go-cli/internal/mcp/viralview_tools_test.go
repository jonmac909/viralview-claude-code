package mcp

import (
	"reflect"
	"sort"
	"testing"

	"github.com/mark3labs/mcp-go/server"
)

func TestRegisterViralViewToolsMatchesReviewedContract(t *testing.T) {
	s := server.NewMCPServer("viralview", "test")
	RegisterViralViewTools(s)

	got := make([]string, 0, len(s.ListTools()))
	for name := range s.ListTools() {
		got = append(got, name)
	}
	sort.Strings(got)

	want := []string{
		"account_balance",
		"account_status",
		"account_usage",
		"library_get",
		"library_search",
		"product_scan",
		"projects_get",
		"projects_list",
		"task_status_export_status",
		"task_status_extraction_status",
		"task_status_image_status",
	}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("reviewed MCP tools = %v, want %v", got, want)
	}
}
