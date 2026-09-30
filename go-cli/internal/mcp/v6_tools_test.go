package mcp

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"

	mcplib "github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"viralview-pp-cli/internal/client"
	"viralview-pp-cli/internal/config"
	"viralview-pp-cli/internal/platform"
)

func TestV6PaidToolRefusesMissingApprovalBeforeClientFactory(t *testing.T) {
	paidSpecs := []v6ToolSpec{
		{name: "characters_generate", method: "POST", path: "/api/v3/project/{id}/character-dispatch", project: true, payload: true, approval: true},
		{name: "frames_generate", method: "POST", path: "/api/v3/project/{id}/frames", project: true, payload: true, approval: true},
		{name: "videos_generate", method: "POST", path: "/api/v3/project/{id}/generate", project: true, payload: true, approval: true},
		{name: "auto_start", method: "POST", path: "/api/v3/project/{id}/auto/start", project: true, payload: true, approval: true},
		{name: "export_start", method: "POST", path: "/api/ugc/stitch-videos", project: true, payload: true, approval: true},
		{name: "intent_retry", method: "POST", path: "/api/v3/project/{id}/intent", project: true, payload: true, approval: true},
		{name: "product_cutout", method: "POST", path: "/api/v3/project/{id}/product-cutout", project: true, payload: true, approval: true},
	}
	for _, spec := range paidSpecs {
		t.Run(spec.name, func(t *testing.T) {
			factoryCalled := false
			handler := v6ToolHandler(spec, func(context.Context) (*client.Client, *platform.Session, error) {
				factoryCalled = true
				return nil, nil, nil
			})

			result, err := handler(context.Background(), mcplib.CallToolRequest{Params: mcplib.CallToolParams{
				Arguments: map[string]any{"projectId": "project_12345678", "payload": map[string]any{}},
			}})
			if err != nil {
				t.Fatalf("handler returned transport error: %v", err)
			}
			if result == nil || !result.IsError {
				t.Fatal("missing approval token was not refused")
			}
			if factoryCalled {
				t.Fatal("client factory ran before the local approval check")
			}
			if text := mcpTextContent(t, result); !strings.Contains(text, "Approval required") {
				t.Fatalf("missing-token error = %q", text)
			}
		})
	}
}

func TestV6NonPaidToolsRefusePaidActionShapesBeforeClientFactory(t *testing.T) {
	tests := []struct {
		name string
		spec v6ToolSpec
		args map[string]any
	}{
		{
			name: "frame edit cannot dispatch",
			spec: v6ToolSpec{name: "frame_edit", method: "POST", path: "/api/v3/project/{id}/frames", project: true, payload: true},
			args: map[string]any{"projectId": "project_12345678", "payload": map[string]any{"action": "dispatch", "requestId": "request-1"}},
		},
		{
			name: "source selection cannot request a paid retry",
			spec: v6ToolSpec{name: "source_select", method: "POST", path: "/api/v3/project/{id}/intent", project: true, payload: true},
			args: map[string]any{"projectId": "project_12345678", "payload": map[string]any{"type": "retry", "beat": "frames"}},
		},
		{
			name: "cutout poll cannot start work",
			spec: v6ToolSpec{name: "product_cutout_status", method: "POST", path: "/api/v3/project/{id}/product-cutout", project: true, payload: true, readOnly: true},
			args: map[string]any{"projectId": "project_12345678", "payload": map[string]any{"action": "start"}},
		},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			factoryCalled := false
			handler := v6ToolHandler(tc.spec, func(context.Context) (*client.Client, *platform.Session, error) {
				factoryCalled = true
				return nil, nil, nil
			})
			result, err := handler(context.Background(), mcplib.CallToolRequest{Params: mcplib.CallToolParams{Arguments: tc.args}})
			if err != nil {
				t.Fatalf("handler returned transport error: %v", err)
			}
			if result == nil || !result.IsError {
				t.Fatal("unsafe action shape was not refused locally")
			}
			if factoryCalled {
				t.Fatal("client factory ran before the local refusal")
			}
			if text := mcpTextContent(t, result); text == "" {
				t.Fatal("local refusal had no explanation")
			}
		})
	}
}

func TestV6AutoQuoteAndStartRequireStableRequestIdentity(t *testing.T) {
	for _, name := range []string{"auto_quote", "auto_start"} {
		spec := v6ToolSpec{name: name}
		if err := validateV6Payload(spec, map[string]any{"workspacePath": "/v6"}); err == nil {
			t.Errorf("%s accepted a payload without requestId", name)
		}
		if err := validateV6Payload(spec, map[string]any{"requestId": "auto-run-1", "workspacePath": "/v6"}); err != nil {
			t.Errorf("%s rejected a valid stable requestId: %v", name, err)
		}
		if err := validateV6Payload(spec, map[string]any{"requestId": strings.Repeat("x", 201)}); err == nil {
			t.Errorf("%s accepted a requestId over the server's 200 character limit", name)
		}
	}
}

func TestV6IntentRetryAcceptsPaidExportBeat(t *testing.T) {
	for _, name := range []string{"intent_retry_quote", "intent_retry"} {
		if err := validateV6Payload(v6ToolSpec{name: name}, map[string]any{"type": "retry", "beat": "export"}); err != nil {
			t.Errorf("%s rejected the app's paid export retry beat: %v", name, err)
		}
	}
}

func TestV6QuoteThenDispatchUsesSamePayloadAndApprovalHeader(t *testing.T) {
	type requestRecord struct {
		path  string
		header string
		body  map[string]any
	}
	var mu sync.Mutex
	var requests []requestRecord
	fake := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer r.Body.Close()
		body, err := io.ReadAll(r.Body)
		if err != nil {
			t.Errorf("read request body: %v", err)
			w.WriteHeader(http.StatusBadRequest)
			return
		}
		var value map[string]any
		if err := json.Unmarshal(body, &value); err != nil {
			t.Errorf("decode request body: %v", err)
			w.WriteHeader(http.StatusBadRequest)
			return
		}
		mu.Lock()
		requests = append(requests, requestRecord{path: r.URL.Path, header: r.Header.Get(viralViewApprovalHeader), body: value})
		mu.Unlock()
		w.Header().Set("Content-Type", "application/json")
		if strings.HasSuffix(r.URL.Path, "/quote") {
			_, _ = io.WriteString(w, `{"action":"frames","model":"test-image","items":[{"id":"1","model":"test-image","creditsEach":5},{"id":"2","model":"test-image","creditsEach":5}],"creditsEach":5,"creditsTotal":10,"approvalToken":"temporary-approval-code","expiresAt":"2030-01-01T00:00:00.000Z"}`)
			return
		}
		_, _ = io.WriteString(w, `{"success":true,"status":"accepted"}`)
	}))
	defer fake.Close()

	factory := func(context.Context) (*client.Client, *platform.Session, error) {
		cfg := &config.Config{BaseURL: fake.URL, ViralviewApiKey: "vv_live_" + strings.Repeat("0", 32)}
		return client.New(cfg, 3*time.Second, 0), nil, nil
	}
	payload := map[string]any{
		"action": "dispatch", "requestId": "frame-request-7", "model": "test-image",
		"sceneNumbers": []any{1.0, 2.0}, "useProductPhoto": true,
	}
	quoteHandler := v6ToolHandler(v6ToolSpec{
		name: "frames_quote", method: "POST", path: "/api/v3/project/{id}/quote",
		project: true, payload: true, readOnly: true, quoteAction: "frames",
	}, factory)
	quote, err := quoteHandler(context.Background(), mcplib.CallToolRequest{Params: mcplib.CallToolParams{
		Arguments: map[string]any{"projectId": "project_12345678", "payload": payload},
	}})
	if err != nil {
		t.Fatalf("quote handler returned transport error: %v", err)
	}
	quoteText := mcpTextContent(t, quote)
	if !strings.Contains(quoteText, "temporary-approval-code") || !strings.Contains(quoteText, "estimatedCredits") {
		t.Fatalf("quote result omitted token or estimate summary: %s", quoteText)
	}

	dispatchHandler := v6ToolHandler(v6ToolSpec{
		name: "frames_generate", method: "POST", path: "/api/v3/project/{id}/frames",
		project: true, payload: true, approval: true,
	}, factory)
	dispatch, err := dispatchHandler(context.Background(), mcplib.CallToolRequest{Params: mcplib.CallToolParams{
		Arguments: map[string]any{"projectId": "project_12345678", "payload": payload, "approvalToken": "temporary-approval-code"},
	}})
	if err != nil {
		t.Fatalf("dispatch handler returned transport error: %v", err)
	}
	if dispatch == nil || dispatch.IsError {
		t.Fatalf("dispatch failed: %s", mcpTextContent(t, dispatch))
	}

	mu.Lock()
	defer mu.Unlock()
	if len(requests) != 2 {
		t.Fatalf("fake server got %d requests, want quote and dispatch", len(requests))
	}
	quoteBody, ok := requests[0].body["payload"].(map[string]any)
	if !ok || !equalJSONValue(quoteBody, requests[1].body) {
		t.Fatalf("dispatch body did not match quoted payload: quote=%#v dispatch=%#v", quoteBody, requests[1].body)
	}
	if requests[1].header != "temporary-approval-code" {
		t.Fatalf("dispatch approval header = %q", requests[1].header)
	}
	if requests[0].header != "" {
		t.Fatalf("quote unexpectedly carried an approval header: %q", requests[0].header)
	}
}

func TestV6MapsApproval402CodesAndRedactsCredentials(t *testing.T) {
	for _, tc := range []struct{ code, want string }{
		{"approval_required", "Approval required"},
		{"approval_invalid", "Approval invalid"},
		{"approval_expired", "Approval expired - quote again and ask the user"},
		{"approval_replayed", "Approval already used"},
		{"over_daily_cap", "Daily credit cap reached"},
	} {
		err := &client.APIError{Method: "POST", Path: "/api/v3/project/id/frames", StatusCode: 402, Body: `{"code":"` + tc.code + `"}`}
		if got := v6ApprovalError(err, "temporary-approval-code"); !strings.Contains(got, tc.want) {
			t.Errorf("v6ApprovalError(%s) = %q, want text containing %q", tc.code, got, tc.want)
		}
	}
	key := "vv_live_" + strings.Repeat("0", 32)
	cfg := &config.Config{ViralviewApiKey: key}
	got := scrubV6Text("server echoed "+key+" and Bearer "+key+" plus temporary-approval-code", cfg, "temporary-approval-code")
	if strings.Contains(got, key) || strings.Contains(got, "temporary-approval-code") {
		t.Fatalf("credential or approval token leaked in error text: %q", got)
	}
}

func TestV6ToolAnnotationsAndPaidDescriptions(t *testing.T) {
	s := server.NewMCPServer("viralview", "test")
	RegisterViralViewTools(s)
	tools := s.ListTools()
	for _, name := range []string{
		"account_balance", "account_status", "account_usage", "library_get", "library_search",
		"projects_get", "projects_list", "task_status_export_status", "task_status_extraction_status",
		"task_status_image_status", "product_scan", "project_status", "source_matches", "characters_quote", "character_saved_list",
		"frames_quote", "videos_quote", "auto_quote", "export_quote", "export_status", "export_download",
		"meta_ad_library_search", "intent_retry_quote", "product_cutout_quote", "product_cutout_status",
	} {
		tool, ok := tools[name]
		if !ok {
			t.Fatalf("read-only tool %q missing", name)
		}
		annotations := v6ToolAnnotations(t, tool.Tool)
		if annotations["readOnlyHint"] != true {
			t.Errorf("%s readOnlyHint = %v, want true", name, annotations["readOnlyHint"])
		}
	}
	paidNames := []string{"characters_generate", "frames_generate", "videos_generate", "auto_start", "export_start", "intent_retry", "product_cutout"}
	for _, name := range paidNames {
		tool, ok := tools[name]
		if !ok {
			t.Fatalf("paid tool %q missing", name)
		}
		if !strings.HasPrefix(tool.Tool.Description, "PAID - spends provider credits. Ask the user to approve the quote shown by ") {
			t.Errorf("%s description missing required paid prefix: %q", name, tool.Tool.Description)
		}
		annotations := v6ToolAnnotations(t, tool.Tool)
		if annotations["destructiveHint"] != true || annotations["readOnlyHint"] != false || annotations["openWorldHint"] != true {
			t.Errorf("%s annotations = %#v", name, annotations)
		}
	}
	for name, tool := range tools {
		if strings.HasPrefix(tool.Tool.Description, "PAID - spends provider credits. Ask the user to approve the quote shown by ") {
			annotations := v6ToolAnnotations(t, tool.Tool)
			if annotations["destructiveHint"] != true || annotations["readOnlyHint"] != false || annotations["openWorldHint"] != true {
				t.Errorf("paid tool %s annotations = %#v", name, annotations)
			}
		}
	}
}

func v6ToolAnnotations(t *testing.T, tool any) map[string]any {
	t.Helper()
	encoded, err := json.Marshal(tool)
	if err != nil {
		t.Fatalf("marshal MCP tool: %v", err)
	}
	var value map[string]any
	if err := json.Unmarshal(encoded, &value); err != nil {
		t.Fatalf("decode MCP tool: %v", err)
	}
	annotations, _ := value["annotations"].(map[string]any)
	if annotations == nil {
		t.Fatalf("MCP tool has no annotations: %s", encoded)
	}
	return annotations
}

func equalJSONValue(a, b any) bool {
	left, leftErr := json.Marshal(a)
	right, rightErr := json.Marshal(b)
	return leftErr == nil && rightErr == nil && string(left) == string(right)
}
