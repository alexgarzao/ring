---
name: ring:gandalf-webhook
description: Send tasks to Gandalf (AI team member) via webhook and get responses back. Publish to Alfarrábio, ask for business context, trigger Slack messages, and more.
user_invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
---

# Gandalf Webhook

Send tasks to Gandalf and get responses back. Gandalf is Lerian's AI team member running on a dedicated Mac mini with access to Slack, Google Workspace, GitHub, Jira, Alfarrábio (report server), and more.

## When to Use

- **Publish to Alfarrábio** — send analysis, reports, or HTML to be published on the report server
- **Business context** — ask Gandalf about clients, deals, product decisions, team context
- **Slack messages** — ask Gandalf to post something on a Slack channel
- **Cross-tool tasks** — anything that needs tools you don't have (Google Docs, CRM, calendar, etc.)

## Endpoint

```
POST http://gandalf.heron-justitia.ts.net:18792/task
```

Accessible only via Tailscale. No auth token needed — identity is resolved automatically from your Tailscale node.

## Sending a Task

```bash
curl -s -X POST http://gandalf.heron-justitia.ts.net:18792/task \
  -H "Content-Type: application/json" \
  -d '{
    "message": "your task description here",
    "context": "optional context about what you are working on"
  }'
```

**Fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `message` | Yes | What you want Gandalf to do. Be specific. |
| `context` | No | What you're working on (repo, PR, feature). Helps Gandalf prioritize and contextualize. |
| `content` | No | Inline content (HTML, markdown, text) for Gandalf to process. Max 5MB. Use this instead of file uploads. |

**Response (202):**
```json
{
  "ok": true,
  "task_id": "a1b2c3d4",
  "from": "Your Name",
  "node": "your-machine",
  "status": "processing",
  "poll": "/task/a1b2c3d4"
}
```

## Polling for Response

```bash
curl -s http://gandalf.heron-justitia.ts.net:18792/task/{task_id}
```

**While processing:**
```json
{
  "task_id": "a1b2c3d4",
  "status": "processing"
}
```

**When done:**
```json
{
  "task_id": "a1b2c3d4",
  "status": "done",
  "response": "Published at https://alfarrabio.lerian.net/your-report.html",
  "completed_at": "2026-03-13T16:18:51-03:00"
}
```

## Full Pattern (send + poll)

```bash
# Send task
TASK_ID=$(curl -s -X POST http://gandalf.heron-justitia.ts.net:18792/task \
  -H "Content-Type: application/json" \
  -d '{"message": "publish this analysis as an Alfarrábio report", "context": "PR #1900 lib-commons v4"}' \
  | jq -r .task_id)

# Poll until done (max ~2 min)
for i in $(seq 1 24); do
  RESULT=$(curl -s http://gandalf.heron-justitia.ts.net:18792/task/$TASK_ID)
  STATUS=$(echo $RESULT | jq -r .status)
  if [ "$STATUS" != "processing" ]; then
    echo $RESULT | jq .
    break
  fi
  sleep 5
done
```

## Examples

### Publish a report to Alfarrábio
```bash
# Build your HTML/markdown content, then send inline via `content` field
CONTENT=$(cat my-report.html)
curl -s -X POST http://gandalf.heron-justitia.ts.net:18792/task \
  -H "Content-Type: application/json" \
  --data-binary @- << EOF
{
  "message": "Publish this as an Alfarrábio report titled 'API Coverage Analysis'. Return the URL.",
  "context": "midaz API audit",
  "content": $(echo "$CONTENT" | jq -Rs .)
}
EOF
```

### Publish markdown (Gandalf converts to HTML)
```bash
curl -s -X POST http://gandalf.heron-justitia.ts.net:18792/task \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Convert this markdown to a styled Alfarrábio report and publish it. Return the URL.",
    "context": "PR #1900 analysis",
    "content": "# Analysis\n\n## Findings\n\n- Point 1\n- Point 2\n\n## Conclusion\n\nAll good."
  }'
```

### Ask for business context
```bash
curl -s -X POST http://gandalf.heron-justitia.ts.net:18792/task \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the current status of the Voluti integration? Any known issues?",
    "context": "investigating INC-72"
  }'
```

### Post to Slack
```bash
curl -s -X POST http://gandalf.heron-justitia.ts.net:18792/task \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Post on #pull-requests: PR #1900 lib-commons v4 is ready for review. Migration guide included.",
    "context": "lib-commons v4 task force"
  }'
```

## Constraints

- **Rate limit:** 10 requests/min per Tailscale node
- **Timeout:** 120s per task
- **Content limit:** 5MB inline (use `content` field, not file uploads)
- **One-way initiation:** you send, Gandalf processes. No streaming.
- **Tailscale only:** not accessible from the public internet
- **Identity:** your Tailscale node identity is attached automatically. No spoofing.
- **No file uploads:** send content inline as JSON string. Safer, simpler.

## Health Check

```bash
curl -s http://gandalf.heron-justitia.ts.net:18792/health
```
