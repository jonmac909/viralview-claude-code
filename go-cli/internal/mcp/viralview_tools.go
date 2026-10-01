package mcp

import (
	mcplib "github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

// RegisterViralViewTools exposes only the reviewed Viral View API contract.
// It intentionally excludes generic local-store, SQL, import, workflow, and
// Cobra-mirror tools from the production MCP binary.
func RegisterViralViewTools(s *server.MCPServer) {
	installFreshTenantGate(s)

	s.AddTool(
		mcplib.NewTool("account_balance",
			mcplib.WithDescription("Read available generation-provider credits. Returns the Balance."),
			mcplib.WithReadOnlyHintAnnotation(true),
			mcplib.WithDestructiveHintAnnotation(false),
			mcplib.WithOpenWorldHintAnnotation(true),
		),
		makeAPIHandler("GET", "/api/ugc/kie-balance", true, false, nil, mcpPageConfig{}, []mcpParamBinding{}, []string{}),
	)
	s.AddTool(
		mcplib.NewTool("account_status",
			mcplib.WithDescription("Check generation-provider reachability. Returns the ProviderStatus."),
			mcplib.WithReadOnlyHintAnnotation(true),
			mcplib.WithDestructiveHintAnnotation(false),
			mcplib.WithOpenWorldHintAnnotation(true),
		),
		makeAPIHandler("GET", "/api/ugc/kie-status", true, false, nil, mcpPageConfig{}, []mcpParamBinding{}, []string{}),
	)
	s.AddTool(
		mcplib.NewTool("account_usage",
			mcplib.WithDescription("List recent generation and export usage. Optional: limit (default: 25). Returns array of UsageEvent."),
			mcplib.WithNumber("limit", mcplib.Description("Maximum usage events, capped at 100")),
			mcplib.WithReadOnlyHintAnnotation(true),
			mcplib.WithDestructiveHintAnnotation(false),
			mcplib.WithOpenWorldHintAnnotation(true),
		),
		makeAPIHandler("GET", "/api/ugc/usage", true, false, nil, mcpPageConfig{}, []mcpParamBinding{{PublicName: "limit", WireName: "limit", Location: "query", Default: "25"}}, []string{}),
	)
	s.AddTool(
		mcplib.NewTool("library_get",
			mcplib.WithDescription("Load one approved source ad. Required: id. Returns the APIResponse."),
			mcplib.WithString("id", mcplib.Required(), mcplib.Description("Approved ad-library item ID")),
			mcplib.WithReadOnlyHintAnnotation(true),
			mcplib.WithDestructiveHintAnnotation(false),
			mcplib.WithOpenWorldHintAnnotation(true),
		),
		makeAPIHandler("GET", "/api/ugc/ad-library/{id}", true, false, nil, mcpPageConfig{}, []mcpParamBinding{{PublicName: "id", WireName: "id", Location: "path"}}, []string{"id"}),
	)
	s.AddTool(
		mcplib.NewTool("library_search",
			mcplib.WithDescription("Search the approved Ad Library. Optional: query, style, limit (default: 12), and cursor. Returns array of LibraryItem."),
			mcplib.WithString("query", mcplib.Description("Words to match in the ad library")),
			mcplib.WithString("style", mcplib.Description("Optional visual style filter")),
			mcplib.WithNumber("limit", mcplib.Description("Maximum results, capped at 24")),
			mcplib.WithString("cursor", mcplib.Description("Opaque pagination cursor returned by a prior MCP response")),
			mcplib.WithReadOnlyHintAnnotation(true),
			mcplib.WithDestructiveHintAnnotation(false),
			mcplib.WithOpenWorldHintAnnotation(true),
		),
		makeAPIHandler("GET", "/api/ugc/ad-library", true, false, nil, mcpPageConfig{CursorParam: "cursor", NextCursorPath: "nextCursor"}, []mcpParamBinding{{PublicName: "query", WireName: "query", Location: "query"}, {PublicName: "style", WireName: "style", Location: "query"}, {PublicName: "limit", WireName: "limit", Location: "query", Default: "12"}}, []string{}),
	)
	s.AddTool(
		mcplib.NewTool("product_scan",
			mcplib.WithDescription("Extract editable product facts from a public product URL. Required: url. Returns the APIResponse."),
			mcplib.WithString("url", mcplib.Required(), mcplib.Description("Public product page URL")),
			mcplib.WithReadOnlyHintAnnotation(true),
			mcplib.WithDestructiveHintAnnotation(false),
			mcplib.WithOpenWorldHintAnnotation(true),
		),
		makeAPIHandler("POST", "/api/ugc/scan-product", false, false, nil, mcpPageConfig{}, []mcpParamBinding{{PublicName: "url", WireName: "productUrl", Location: "body"}}, []string{}),
	)
	s.AddTool(
		mcplib.NewTool("projects_get",
			mcplib.WithDescription("Load one owned project. Required: id. Returns the APIResponse."),
			mcplib.WithString("id", mcplib.Required(), mcplib.Description("Owned Viral View project ID")),
			mcplib.WithReadOnlyHintAnnotation(true),
			mcplib.WithDestructiveHintAnnotation(false),
			mcplib.WithOpenWorldHintAnnotation(true),
		),
		makeAPIHandler("GET", "/api/ugc/project", true, false, nil, mcpPageConfig{}, []mcpParamBinding{{PublicName: "id", WireName: "id", Location: "query"}}, []string{}),
	)
	s.AddTool(
		mcplib.NewTool("projects_list",
			mcplib.WithDescription("List owned projects. Returns array of Project."),
			mcplib.WithReadOnlyHintAnnotation(true),
			mcplib.WithDestructiveHintAnnotation(false),
			mcplib.WithOpenWorldHintAnnotation(true),
		),
		makeAPIHandler("GET", "/api/ugc/project", true, false, nil, mcpPageConfig{}, []mcpParamBinding{}, []string{}),
	)
	s.AddTool(
		mcplib.NewTool("task_status_export_status",
			mcplib.WithDescription("Poll an existing export job. Required: job-id. Returns the JobStatus."),
			mcplib.WithString("job-id", mcplib.Required(), mcplib.Description("Existing export job ID")),
			mcplib.WithReadOnlyHintAnnotation(true),
			mcplib.WithDestructiveHintAnnotation(false),
			mcplib.WithOpenWorldHintAnnotation(true),
		),
		makeAPIHandler("GET", "/api/ugc/stitch-videos", true, false, nil, mcpPageConfig{}, []mcpParamBinding{{PublicName: "job-id", WireName: "jobId", Location: "query"}}, []string{}),
	)
	s.AddTool(
		mcplib.NewTool("task_status_extraction_status",
			mcplib.WithDescription("Poll an existing source-link extraction job. Required: job-id. Returns the JobStatus."),
			mcplib.WithString("job-id", mcplib.Required(), mcplib.Description("Existing extraction job ID")),
			mcplib.WithReadOnlyHintAnnotation(true),
			mcplib.WithDestructiveHintAnnotation(false),
			mcplib.WithOpenWorldHintAnnotation(true),
		),
		makeAPIHandler("GET", "/api/ugc/extract-video", true, false, nil, mcpPageConfig{}, []mcpParamBinding{{PublicName: "job-id", WireName: "jobId", Location: "query"}}, []string{}),
	)
	s.AddTool(
		mcplib.NewTool("task_status_image_status",
			mcplib.WithDescription("Poll an existing paid image job without spending again. Required: task-id. Optional: source-image-url. Returns the JobStatus."),
			mcplib.WithString("task-id", mcplib.Required(), mcplib.Description("Existing image task ID")),
			mcplib.WithString("source-image-url", mcplib.Description("Optional source image URL used to recover task state")),
			mcplib.WithReadOnlyHintAnnotation(true),
			mcplib.WithDestructiveHintAnnotation(false),
			mcplib.WithOpenWorldHintAnnotation(true),
		),
		makeAPIHandler("GET", "/api/ugc/generate-overlay", true, false, nil, mcpPageConfig{}, []mcpParamBinding{{PublicName: "task-id", WireName: "taskId", Location: "query"}, {PublicName: "source-image-url", WireName: "sourceImageUrl", Location: "query"}}, []string{}),
	)
	RegisterV6Tools(s)
}
