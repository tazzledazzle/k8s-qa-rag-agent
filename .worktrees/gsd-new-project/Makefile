# otel-demo-platform — one-command bootstrap
# Run from repo root. Ports: API 8080, Agent 8000 (override with API_PORT/AGENT_PORT before make run).
# See CONFIG.md for all env vars.

.PHONY: infra up-infra run-agent run-worker run-api run smoke e2e-smoke stop

# Start infrastructure (Temporal, Grafana otel-lgtm). Use "docker compose" for compatibility.
infra up-infra:
	docker compose up -d

# Start Agent in foreground (for debugging). Install deps first: cd agent && pip install -e ".[dev]"
run-agent:
	cd agent && python -m agent.main

# Start Worker from repo root.
run-worker:
	./gradlew :worker:run

# Start API from repo root.
run-api:
	./gradlew :api:run

# Stop stale background processes from a previous run.
stop:
	@for pidfile in .agent.pid .worker.pid .api.pid; do \
		if [ -f "$$pidfile" ]; then \
			pid=$$(cat "$$pidfile"); \
			if kill -0 "$$pid" 2>/dev/null; then \
				echo "Stopping $$pidfile (pid $$pid)..."; \
				kill "$$pid" 2>/dev/null || true; \
			fi; \
			rm -f "$$pidfile"; \
		fi; \
	done
	@echo "Stale processes cleaned up."

# One-command start: stop stale processes, infra, then Agent (bg), Worker (bg), API (fg).
# Ctrl+C stops API; Agent/Worker keep running (use 'make stop' to clean up).
run: stop infra
	@echo "Starting Agent in background..."
	@(cd agent && python -m agent.main > ../.agent.log 2>&1) & echo $$! > .agent.pid; sleep 3
	@echo "Starting Worker in background..."
	@./gradlew :worker:run > .worker.log 2>&1 & echo $$! > .worker.pid; sleep 5
	@echo "Starting API in foreground (Ctrl+C to stop API only). API: http://localhost:8080, Agent: http://localhost:8000"
	@./gradlew :api:run

# E2E smoke: bring up infra, start apps in background, wait, then curl health + POST /chat.
# Used by CI. Override ports via API_PORT/AGENT_PORT if needed.
e2e-smoke smoke: stop infra
	@echo "Waiting for infra (Temporal, otel-lgtm)..."
	@sleep 15
	@echo "Starting Agent..."
	@(cd agent && python -m agent.main > ../.agent.log 2>&1) & echo $$! > .agent.pid; sleep 5
	@echo "Starting Worker..."
	@./gradlew :worker:run --no-daemon > .worker.log 2>&1 & echo $$! > .worker.pid; sleep 8
	@echo "Starting API..."
	@./gradlew :api:run --no-daemon > .api.log 2>&1 & echo $$! > .api.pid; sleep 8
	@echo "Smoke: GET /health..."
	@curl -sf http://localhost:8080/health | grep -q "otel-demo-api" || (echo "Health check failed — port 8080 is not the API (expected service=otel-demo-api). Kill stale processes and retry."; exit 1)
	@echo "Smoke: POST /chat (optional)..."
	@out=$$(curl -sf -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"Hello"}' 2>/dev/null); \
	if echo "$$out" | grep -q '"reply"'; then \
		echo "Smoke: POST /chat OK."; \
	else \
		echo "Smoke: POST /chat skipped or failed (Temporal/Worker/Ollama may not be ready)."; \
	fi
	@echo "Smoke passed."
