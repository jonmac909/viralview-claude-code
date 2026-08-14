.PHONY: build test lint install clean

BIN_EXT := $(if $(filter windows,$(shell go env GOOS)),.exe,)
VERSION ?= 0.1.0
CLI_LDFLAGS := -X viralview-pp-cli/internal/cli.version=$(VERSION)
MCP_LDFLAGS := -X main.version=$(VERSION)

build:
	mkdir -p bin
	go build -ldflags "$(CLI_LDFLAGS)" -o bin/viralview-pp-cli$(BIN_EXT) ./cmd/viralview-pp-cli

test:
	go test ./...

lint:
	golangci-lint run

install:
	go install -ldflags "$(CLI_LDFLAGS)" ./cmd/viralview-pp-cli

clean:
	rm -rf bin/

build-mcp:
	mkdir -p bin
	go build -ldflags "$(MCP_LDFLAGS)" -o bin/viralview-pp-mcp$(BIN_EXT) ./cmd/viralview-pp-mcp

install-mcp:
	go install -ldflags "$(MCP_LDFLAGS)" ./cmd/viralview-pp-mcp

build-all: build build-mcp
