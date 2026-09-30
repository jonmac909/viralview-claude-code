// Copyright 2026 Jon Mac and contributors. Licensed under Apache-2.0. See LICENSE.
// Hand-written V6 endpoint tools. Kept separate from generated tools so a
// Printing Press reprint can preserve the approval and payload-binding rules.

package mcp

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"regexp"
	"strings"

	mcplib "github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"viralview-pp-cli/internal/cli"
	"viralview-pp-cli/internal/client"
	"viralview-pp-cli/internal/config"
	"viralview-pp-cli/internal/platform"
)

const viralViewApprovalHeader = "X-ViralView-Approval"

var (
	v6APIKeyTextRE = regexp.MustCompile(`(?i)vv_live_[a-z0-9._~+/-]+`)
	v6BearerTextRE = regexp.MustCompile(`(?i)Bearer\s+\S+`)
)

type v6HandlerFactory func(context.Context) (*client.Client, *platform.Session, error)

type v6ToolSpec struct {
	name          string
	description   string
	method        string
	path          string
	project       bool
	queryProject  bool
	payload       bool
	readOnly      bool
	quoteAction   string
	actionArg     bool
	approval      bool
	staticBody    map[string]any
	download      bool
}

func RegisterV6Tools(s *server.MCPServer) {
	addV6Tool(s, v6ToolSpec{name: "project_create", description: "Create or save a V6 project from product facts and a source selection. Send the app project snapshot in payload.", method: "POST", path: "/api/ugc/project", payload: true})
	addV6Tool(s, v6ToolSpec{name: "project_status", description: "Load computed V6 project context: current workflow step, available outputs, and next actions.", method: "GET", path: "/api/v3/project/{id}/context", project: true, readOnly: true})
	addV6Tool(s, v6ToolSpec{name: "source_matches", description: "Rank Ad Library candidates for the supplied product and scan context.", method: "POST", path: "/api/ugc/source-matches", payload: true, readOnly: true})
	addV6Tool(s, v6ToolSpec{name: "source_select", description: "Save a library source or an already uploaded or extracted source with a V3 project intent.", method: "POST", path: "/api/v3/project/{id}/intent", project: true, payload: true})
	addV6Tool(s, v6ToolSpec{name: "source_extract", description: "Start extracting a source video from a public video link. Poll the returned job before analysis.", method: "POST", path: "/api/ugc/extract-video", payload: true})
	addV6Tool(s, v6ToolSpec{name: "source_analysis", description: "Analyze a source video for hook, claims, proof, scenes, timestamps, and transcript.", method: "POST", path: "/api/ugc/analyze-video", payload: true})
	addV6Tool(s, v6ToolSpec{name: "source_analysis_save", description: "Save supplied-source timing, transcript, and scene cuts through the V3 project intent route.", method: "POST", path: "/api/v3/project/{id}/intent", project: true, payload: true})
	addV6Tool(s, v6ToolSpec{name: "script_draft", description: "Draft or rewrite a script from the source analysis and target product facts.", method: "POST", path: "/api/ugc/rewrite-script", payload: true})
	addV6Tool(s, v6ToolSpec{name: "script_draft_save", description: "Save an approved or edited script draft with the V3 save_script_draft intent.", method: "POST", path: "/api/v3/project/{id}/intent", project: true, payload: true})
	addV6Tool(s, v6ToolSpec{name: "script_edit_line", description: "Edit script dialogue or one scene line with the V3 edit_script intent.", method: "POST", path: "/api/v3/project/{id}/intent", project: true, payload: true})
	addV6Tool(s, v6ToolSpec{name: "script_approve", description: "Approve the saved script beat for this project.", method: "POST", path: "/api/v3/project/{id}/intent", project: true, staticBody: map[string]any{"type": "approve", "beat": "script"}})
	addV6Tool(s, v6ToolSpec{name: "script_score", description: "Score the current script using the project's V3 score endpoint.", method: "POST", path: "/api/v3/project/{id}/script-score", project: true, payload: true})
	addV6Tool(s, v6ToolSpec{name: "characters_quote", description: "Quote a character image batch. The payload must be the exact body planned for characters_generate.", method: "POST", path: "/api/v3/project/{id}/quote", project: true, payload: true, readOnly: true, quoteAction: "characters"})
	addV6Tool(s, v6ToolSpec{name: "characters_generate", description: paidDescription("characters_quote"), method: "POST", path: "/api/v3/project/{id}/character-dispatch", project: true, payload: true, approval: true})
	addV6Tool(s, v6ToolSpec{name: "character_lock", description: "Create and save a reusable character identity lock from the selected character and prompt.", method: "POST", path: "/api/ugc/lock-character", payload: true})
	addV6Tool(s, v6ToolSpec{name: "character_saved_list", description: "List the caller's saved V3 character candidates.", method: "GET", path: "/api/v3/characters", readOnly: true})
	addV6Tool(s, v6ToolSpec{name: "character_use_saved", description: "Apply a saved character with the V3 reuse_saved_character project intent.", method: "POST", path: "/api/v3/project/{id}/intent", project: true, payload: true})
	addV6Tool(s, v6ToolSpec{name: "frames_quote", description: "Quote a frames or frame_remake image batch. Include the action and pass the identical payload to frames_generate.", method: "POST", path: "/api/v3/project/{id}/quote", project: true, payload: true, readOnly: true, actionArg: true})
	addV6Tool(s, v6ToolSpec{name: "frames_generate", description: paidDescription("frames_quote"), method: "POST", path: "/api/v3/project/{id}/frames", project: true, payload: true, approval: true})
	addV6Tool(s, v6ToolSpec{name: "frame_edit", description: "Prepare or revise a single scene frame prompt through the V3 frames prepare action. This does not dispatch image generation.", method: "POST", path: "/api/v3/project/{id}/frames", project: true, payload: true})
	addV6Tool(s, v6ToolSpec{name: "videos_quote", description: "Quote scene_videos, scene_regenerate, or lip_redo. Include model, scene items, durations, and quality in payload, then reuse that identical payload for videos_generate.", method: "POST", path: "/api/v3/project/{id}/quote", project: true, payload: true, readOnly: true, actionArg: true})
	addV6Tool(s, v6ToolSpec{name: "videos_generate", description: paidDescription("videos_quote"), method: "POST", path: "/api/v3/project/{id}/generate", project: true, payload: true, approval: true})
	addV6Tool(s, v6ToolSpec{name: "auto_quote", description: "Quote the persisted V6 auto plan. Include the same stable requestId and workspacePath you will send to auto_start; the app derives paid items from the saved project.", method: "POST", path: "/api/v3/project/{id}/quote", project: true, payload: true, readOnly: true, quoteAction: "auto"})
	addV6Tool(s, v6ToolSpec{name: "auto_start", description: paidDescription("auto_quote"), method: "POST", path: "/api/v3/project/{id}/auto/start", project: true, payload: true, approval: true})
	addV6Tool(s, v6ToolSpec{name: "auto_stop", description: "Stop the active V6 automatic run for a project.", method: "POST", path: "/api/v3/project/{id}/auto/stop", project: true, staticBody: map[string]any{}})
	addV6Tool(s, v6ToolSpec{name: "intent_retry_quote", description: "Quote a persisted character, frame, video, or export retry. Use payload type retry and its beat.", method: "POST", path: "/api/v3/project/{id}/quote", project: true, payload: true, readOnly: true, quoteAction: "intent_retry"})
	addV6Tool(s, v6ToolSpec{name: "intent_retry", description: paidDescription("intent_retry_quote"), method: "POST", path: "/api/v3/project/{id}/intent", project: true, payload: true, approval: true})
	addV6Tool(s, v6ToolSpec{name: "product_cutout_quote", description: "Quote the selected product image background-removal action. Use the same payload for product_cutout.", method: "POST", path: "/api/v3/project/{id}/quote", project: true, payload: true, readOnly: true, quoteAction: "product_cutout"})
	addV6Tool(s, v6ToolSpec{name: "product_cutout", description: paidDescription("product_cutout_quote"), method: "POST", path: "/api/v3/project/{id}/product-cutout", project: true, payload: true, approval: true})
	addV6Tool(s, v6ToolSpec{name: "product_cutout_status", description: "Poll product photo background removal without starting a new job.", method: "POST", path: "/api/v3/project/{id}/product-cutout", project: true, payload: true, readOnly: true})
	addV6Tool(s, v6ToolSpec{name: "ad_score", description: "Score the current project's completed ad through its V3 score endpoint.", method: "POST", path: "/api/v3/project/{id}/ad-score", project: true, payload: true})
	addV6Tool(s, v6ToolSpec{name: "editor_update", description: "Save the latest V6 project/editor snapshot through the app's project save API. Preserve all unrelated fields; put trim, scene, and caption edits in the app fields returned by project_status.", method: "POST", path: "/api/ugc/project", payload: true})
	addV6Tool(s, v6ToolSpec{name: "export_quote", description: "Quote the final export. Include projectId, saved scenes or videoUrls, and item identifiers in the payload; reuse that exact payload for export_start.", method: "POST", path: "/api/v3/project/{id}/quote", project: true, payload: true, readOnly: true, quoteAction: "export"})
	addV6Tool(s, v6ToolSpec{name: "export_start", description: paidDescription("export_quote"), method: "POST", path: "/api/ugc/stitch-videos", project: true, payload: true, approval: true})
	addV6Tool(s, v6ToolSpec{name: "export_status", description: "Poll the saved V6 export job for a project.", method: "GET", path: "/api/v3/project/{id}/export-status", project: true, readOnly: true})
	addV6Tool(s, v6ToolSpec{name: "export_download", description: "Download an export from a same-origin /api/uploads path returned for this owned project. Returns a base64 binary envelope.", method: "GET", path: "", project: true, download: true, readOnly: true})
	addV6Tool(s, v6ToolSpec{name: "meta_ad_library_search", description: "Search the Meta Ad Library using its public Viral View search route. Pass supported search filters in payload.", method: "GET", path: "/api/ugc/meta-ad-library/search", payload: true, readOnly: true})
	addV6Tool(s, v6ToolSpec{name: "caption_redo", description: "Request the app's existing caption redo operation for a project scene.", method: "POST", path: "/api/ugc/redo-captions", payload: true})
}

func paidDescription(quoteTool string) string {
	return "PAID - spends provider credits. Ask the user to approve the quote shown by " + quoteTool + " before calling. Pass the identical payload and its approvalToken."
}

func addV6Tool(s *server.MCPServer, spec v6ToolSpec) {
	options := []mcplib.ToolOption{mcplib.WithDescription(spec.description)}
	if spec.project {
		options = append(options, mcplib.WithString("projectId", mcplib.Required(), mcplib.Description("Owned Viral View project ID")))
	}
	if spec.queryProject {
		options = append(options, mcplib.WithString("projectId", mcplib.Required(), mcplib.Description("Owned Viral View project ID")))
	}
	if spec.download {
		options = append(options, mcplib.WithString("downloadUrl", mcplib.Required(), mcplib.Description("Same-origin signed /api/uploads URL returned by this project's export status")))
	}
	if spec.payload {
		options = append(options, mcplib.WithObject("payload", mcplib.Required(), mcplib.Description("JSON request body. For paid calls, pass exactly the same object used for the matching quote.")))
	}
	if spec.actionArg {
		actionDescription := "scene_videos, scene_regenerate, or lip_redo; use the same action for the quote and paid dispatch"
		if spec.name == "frames_quote" {
			actionDescription = "frames or frame_remake; use the same action for the quote and paid dispatch"
		}
		options = append(options, mcplib.WithString("action", mcplib.Required(), mcplib.Description(actionDescription)))
	}
	if spec.approval {
		options = append(options, mcplib.WithString("approvalToken", mcplib.Required(), mcplib.Description("Short-lived token returned by the matching quote. Sent only in X-ViralView-Approval.")))
	}
	options = append(options,
		mcplib.WithReadOnlyHintAnnotation(spec.readOnly),
		mcplib.WithDestructiveHintAnnotation(spec.approval),
		mcplib.WithOpenWorldHintAnnotation(true),
	)
	s.AddTool(mcplib.NewTool(spec.name, options...), v6ToolHandler(spec, newMCPClient))
}

func v6ToolHandler(spec v6ToolSpec, factory v6HandlerFactory) server.ToolHandlerFunc {
	return func(ctx context.Context, req mcplib.CallToolRequest) (*mcplib.CallToolResult, error) {
		args := req.GetArguments()
		var token string
		if spec.approval {
			value, ok := args["approvalToken"].(string)
			if !ok || strings.TrimSpace(value) == "" {
				return mcpToolError("Approval required - call the matching quote tool and ask the user before paid dispatch."), nil
			}
			token = strings.TrimSpace(value)
		}

		path, err := v6Path(spec, args)
		if err != nil {
			return mcpToolError(err.Error()), nil
		}
		payload, err := v6Payload(spec, args)
		if err != nil {
			return mcpToolError(err.Error()), nil
		}
		if err := validateV6Payload(spec, payload); err != nil {
			return mcpToolError(err.Error()), nil
		}

		c, platformSession, err := factory(ctx)
		if err != nil {
			return mcpToolError(scrubV6Text(err.Error(), nil, token)), nil
		}
		if platformSession != nil {
			defer platformSession.ZeroCredentials()
		}
		if err := cli.AdoptMCPOutputSemantics(platformSession, args); err != nil {
			return mcpToolError(scrubV6Text(err.Error(), c.Config, token)), nil
		}

		var data json.RawMessage
		if spec.quoteAction != "" || spec.actionArg {
			action := spec.quoteAction
			if spec.actionArg {
				action, _ = args["action"].(string)
				allowed := action == "scene_videos" || action == "scene_regenerate" || action == "lip_redo"
				if spec.name == "frames_quote" {
					allowed = action == "frames" || action == "frame_remake"
				}
				if !allowed {
					return mcpToolError("Quote action is not supported by this quote tool."), nil
				}
			}
			data, _, err = c.PostQueryWithParams(ctx, path, nil, map[string]any{"action": action, "payload": payload})
			if err == nil {
				data = summarizeV6Quote(data, payload)
			}
		} else if spec.download {
			data, err = c.GetWithHeadersNoCache(ctx, path, nil, map[string]string{client.BinaryResponseHeader: "true"})
		} else if spec.method == "GET" {
			params := map[string]string{}
			if spec.queryProject {
				params["id"] = args["projectId"].(string)
			}
			if spec.payload {
				if queryArgs, ok := payload.(map[string]any); ok {
					for key, value := range queryArgs {
						if value != nil {
							params[key] = formatMCPParamValue(value)
						}
					}
				}
			}
			data, err = c.GetWithHeadersNoCache(ctx, path, params, nil)
		} else if spec.method == "POST" && spec.approval {
			data, _, err = c.PostWithHeaders(ctx, path, payload, map[string]string{viralViewApprovalHeader: token})
		} else if spec.method == "POST" {
			if spec.readOnly {
				data, _, err = c.PostQueryWithParams(ctx, path, nil, payload)
			} else {
				data, _, err = c.Post(ctx, path, payload)
			}
		} else {
			return mcpToolError("Unsupported V6 tool method: " + spec.method), nil
		}
		if err != nil {
			message := err.Error()
			if spec.approval {
				message = v6ApprovalError(err, token)
			}
			return mcpToolError(scrubV6Text(message, c.Config, token)), nil
		}
		data = scrubV6JSON(data, c.Config, spec.quoteAction != "" || spec.actionArg)
		return mcpToolResultText(spec.method, data), nil
	}
}

func v6Path(spec v6ToolSpec, args map[string]any) (string, error) {
	path := spec.path
	if spec.project || spec.queryProject {
		id, ok := args["projectId"].(string)
		if !ok || strings.TrimSpace(id) == "" {
			return "", errors.New("projectId is required")
		}
		if strings.Contains(path, "{id}") {
			path = strings.Replace(path, "{id}", mcpPathValue(strings.TrimSpace(id)), 1)
		}
	}
	if spec.download {
		raw, ok := args["downloadUrl"].(string)
		if !ok {
			return "", errors.New("downloadUrl must be a same-origin /api/uploads URL")
		}
		u, err := url.Parse(strings.TrimSpace(raw))
		if err != nil || (u.IsAbs() && (u.Scheme != "https" || !strings.EqualFold(u.Hostname(), "app.viralview.io"))) || (!u.IsAbs() && u.Host != "") || !strings.HasPrefix(u.Path, "/api/uploads/") || strings.Contains(u.Path, "..") {
			return "", errors.New("downloadUrl must be a relative /api/uploads path returned by this project's export status")
		}
		// Developer-key download access is the supported contract. Drop any
		// signed query token from the returned URL so it never enters request
		// diagnostics or logs.
		path = u.EscapedPath()
	}
	return path, nil
}

func v6Payload(spec v6ToolSpec, args map[string]any) (any, error) {
	if spec.staticBody != nil {
		return spec.staticBody, nil
	}
	if !spec.payload {
		return map[string]any{}, nil
	}
	payload, ok := args["payload"].(map[string]any)
	if !ok || payload == nil {
		return nil, errors.New("payload must be a JSON object")
	}
	return payload, nil
}

func validateV6Payload(spec v6ToolSpec, payload any) error {
	row, _ := payload.(map[string]any)
	if row == nil {
		return nil
	}
	if spec.name == "auto_quote" || spec.name == "auto_start" {
		requestID, _ := row["requestId"].(string)
		if requestID = strings.TrimSpace(requestID); requestID == "" || len(requestID) > 200 {
			return errors.New("Auto quote and start require the same stable requestId (1 to 200 characters).")
		}
	}
	intentType, _ := row["type"].(string)
	allowedIntents := map[string][]string{
		"source_select":        []string{"select_source", "set_supplied_source"},
		"source_analysis_save": []string{"save_supplied_source_enrichment"},
		"script_draft_save":    []string{"save_script_draft"},
		"script_edit_line":     []string{"edit_script"},
		"character_use_saved":  []string{"reuse_saved_character"},
		"intent_retry":         []string{"retry"},
		"intent_retry_quote":   []string{"retry"},
	}
	if allowed, ok := allowedIntents[spec.name]; ok {
		for _, expected := range allowed {
			if intentType == expected {
				if expected == "retry" {
					beat, _ := row["beat"].(string)
					if beat != "character" && beat != "frames" && beat != "generate" && beat != "export" {
						return errors.New("Retry beat must be character, frames, generate, or export.")
					}
				}
				return nil
			}
		}
		return errors.New("Intent type is not supported by this tool.")
	}
	if spec.name == "frame_edit" {
		if row["action"] != "prepare" {
			return errors.New("frame_edit only accepts action prepare; use frames_quote and frames_generate for dispatch.")
		}
	}
	if spec.name == "product_cutout_quote" || spec.name == "product_cutout" {
		if row["action"] != "start" && row["action"] != "start-fallback" {
			return errors.New("Product cutout quote and dispatch require action start or start-fallback.")
		}
	}
	if spec.name == "product_cutout_status" && row["action"] != "poll" {
		return errors.New("product_cutout_status only accepts action poll.")
	}
	return nil
}

func summarizeV6Quote(raw json.RawMessage, payload any) json.RawMessage {
	var quote map[string]any
	if json.Unmarshal(raw, &quote) != nil {
		return raw
	}
	itemCount, seconds := 0, 0.0
	if items, ok := quote["items"].([]any); ok {
		itemCount = len(items)
		for _, rawItem := range items {
			if item, ok := rawItem.(map[string]any); ok {
				if duration, ok := item["durationSeconds"].(float64); ok {
					seconds += duration
				}
			}
		}
	}
	if row, ok := payload.(map[string]any); ok {
		if itemCount == 0 {
			if items, ok := row["items"].([]any); ok {
				itemCount = len(items)
			} else if scenes, ok := row["sceneNumbers"].([]any); ok {
				itemCount = len(scenes)
			} else if row["requestId"] != nil || row["itemId"] != nil {
				itemCount = 1
			}
		}
		if itemCount > 0 && seconds == 0 {
			if items, ok := row["items"].([]any); ok {
				for _, rawItem := range items {
					if item, ok := rawItem.(map[string]any); ok {
						if duration, ok := item["durationSeconds"].(float64); ok {
							seconds += duration
						}
					}
				}
			}
		}
		if itemCount > 0 && seconds == 0 {
			if duration, ok := row["durationSeconds"].(float64); ok {
				seconds = duration * float64(itemCount)
			}
		}
	}
	quote["itemCount"] = itemCount
	quote["seconds"] = seconds
	if total, ok := quote["creditsTotal"]; ok {
		quote["estimatedCredits"] = total
	}
	encoded, err := json.Marshal(quote)
	if err != nil {
		return raw
	}
	return encoded
}

func v6ApprovalError(err error, approvalToken string) string {
	var apiErr *client.APIError
	if errors.As(err, &apiErr) && apiErr.StatusCode == 402 {
		var body struct {
			Code string `json:"code"`
		}
		_ = json.Unmarshal([]byte(apiErr.Body), &body)
		switch body.Code {
		case "approval_required":
			return "Approval required - quote this exact payload and ask the user before calling again."
		case "approval_invalid":
			return "Approval invalid - get a fresh quote and ask the user before calling again."
		case "approval_expired":
			return "Approval expired - quote again and ask the user."
		case "approval_replayed":
			return "Approval already used - quote again and ask the user before retrying."
		case "over_daily_cap":
			return "Daily credit cap reached - no paid request was accepted."
		default:
			return "Paid approval was refused (HTTP 402) - quote again and ask the user."
		}
	}
	message := err.Error()
	if approvalToken != "" {
		message = strings.ReplaceAll(message, approvalToken, "[REDACTED_APPROVAL_TOKEN]")
	}
	return fmt.Sprintf("Paid request failed: %s", message)
}

func scrubV6JSON(raw json.RawMessage, cfg *config.Config, keepApprovalToken bool) json.RawMessage {
	var value any
	if json.Unmarshal(raw, &value) != nil {
		return json.RawMessage(scrubV6Text(string(raw), cfg, ""))
	}
	value = scrubV6Value(value, cfg, keepApprovalToken)
	encoded, err := json.Marshal(value)
	if err != nil {
		return raw
	}
	return encoded
}

func scrubV6Value(value any, cfg *config.Config, keepApprovalToken bool) any {
	switch typed := value.(type) {
	case map[string]any:
		clean := make(map[string]any, len(typed))
		for key, item := range typed {
			if key == "approvalToken" && keepApprovalToken {
				clean[key] = item
				continue
			}
			if isV6SensitiveField(key) {
				clean[key] = "[REDACTED]"
				continue
			}
			clean[key] = scrubV6Value(item, cfg, keepApprovalToken)
		}
		return clean
	case []any:
		clean := make([]any, len(typed))
		for index, item := range typed {
			clean[index] = scrubV6Value(item, cfg, keepApprovalToken)
		}
		return clean
	case string:
		return scrubV6Text(typed, cfg, "")
	default:
		return value
	}
}

func isV6SensitiveField(key string) bool {
	name := strings.ToLower(strings.ReplaceAll(strings.ReplaceAll(key, "-", ""), "_", ""))
	return strings.Contains(name, "authorization") || strings.Contains(name, "apikey") ||
		strings.Contains(name, "secret") || strings.Contains(name, "password") ||
		strings.Contains(name, "cookie") || name == "token" || strings.HasSuffix(name, "token")
}

func scrubV6Text(value string, cfg *config.Config, approvalToken string) string {
	if approvalToken != "" {
		value = strings.ReplaceAll(value, approvalToken, "[REDACTED_APPROVAL_TOKEN]")
	}
	if cfg != nil {
		for _, secret := range []string{cfg.ViralviewApiKey, cfg.AccessToken, cfg.RefreshToken, cfg.ClientSecret, cfg.AuthHeaderVal, cfg.AuthHeader()} {
			if secret != "" {
				value = strings.ReplaceAll(value, secret, "[REDACTED]")
			}
		}
	}
	value = v6APIKeyTextRE.ReplaceAllString(value, "[REDACTED_API_KEY]")
	return v6BearerTextRE.ReplaceAllString(value, "Bearer [REDACTED]")
}
