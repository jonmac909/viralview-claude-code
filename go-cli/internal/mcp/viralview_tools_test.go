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
		"ad_score",
		"auto_quote",
		"auto_start",
		"auto_stop",
		"caption_redo",
		"character_lock",
		"character_saved_list",
		"character_use_saved",
		"characters_generate",
		"characters_quote",
		"editor_update",
		"export_download",
		"export_start",
		"export_status",
		"frame_edit",
		"frames_generate",
		"frames_quote",
		"intent_retry",
		"intent_retry_quote",
		"library_get",
		"library_search",
		"meta_ad_library_search",
		"product_cutout",
		"product_cutout_quote",
		"product_cutout_status",
		"product_scan",
		"project_create",
		"project_status",
		"projects_get",
		"projects_list",
		"script_approve",
		"script_draft",
		"script_draft_save",
		"script_edit_line",
		"script_score",
		"source_analysis",
		"source_analysis_save",
		"source_extract",
		"source_matches",
		"source_select",
		"task_status_export_status",
		"task_status_extraction_status",
		"task_status_image_status",
		"videos_generate",
		"videos_quote",
	}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("reviewed MCP tools = %v, want %v", got, want)
	}
}
