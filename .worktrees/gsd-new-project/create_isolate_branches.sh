#!/usr/bin/env bash
# Create isolate/<folder> branches: each branch contains only that folder at root.
# Run from repo root. Requires: backup/full-repo branch exists with all 22 folders.

set -e
FOLDERS=(
  agentic-first-response
  ai-best-practices-example
  airtable-observability-application
  buildbuddy-application
  career-suite
  design-kube
  devops-portfolio
  devtools
  event-streaming-tutorial
  fraud-detection-demo
  go-pihole
  job-application-pipeline
  langfuse-demo
  llm-workflow-orchestrator
  localgpt
  multitenant-saas-observability
  my-blog-app
  otel-demo-platform
  pearl-health-application
  pelotech
  portfolio-projects
  showcase-projects
)

for keep in "${FOLDERS[@]}"; do
  echo "=== isolate/$keep ==="
  git clean -fd
  git checkout backup/full-repo
  git checkout -B "isolate/$keep"

  # Remove all other top-level folders
  for name in "${FOLDERS[@]}"; do
    [ "$name" = "$keep" ] && continue
    if [ -e "$name" ]; then
      git rm -rf "$name" 2>/dev/null || rm -rf "$name"
    fi
  done
  # Remove root script
  if [ -f consolidate_repos.py ]; then
    git rm -f consolidate_repos.py 2>/dev/null || rm -f consolidate_repos.py
  fi

  # Root README for this branch
  echo "This branch contains only the **$keep** project." > README.md
  git add README.md

  git add -A
  if git diff --cached --quiet && git diff --quiet; then
    git commit --allow-empty -m "chore: isolate $keep — remove other projects"
  else
    git commit -m "chore: isolate $keep — remove other projects"
  fi
done

echo "Done. Switching back to main."
git checkout main
