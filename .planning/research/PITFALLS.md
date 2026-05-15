# Research — Pitfalls

**Researched:** 2026-05-12

## 1. Stale or partial indexes

**Warning signs:** Answers cite deleted files; missing new symbols.  
**Prevention:** Webhook + CronJob reconciliation; version chunks by commit SHA in metadata.  
**Phase:** E2E / Indexer hardening.

## 2. Retrieval “looks smart” but answers wrong

**Warning signs:** High scores on irrelevant chunks; long answers without citations.  
**Prevention:** Cross-encoder rerank cap, max tool iterations, prompt requiring citations or abstain.  
**Phase:** QA agent + evaluation fixtures.

## 3. Resource blow-ups (embeddings / ES)

**Warning signs:** OOMKilled indexer; ES yellow cluster.  
**Prevention:** Batch sizes, index lifecycle, PVC sizing per DESIGN capacity sketch.  
**Phase:** Ops / prod overlay tuning.

## 4. Webhook security gaps

**Warning signs:** Unsigned triggers; SSRF on repo URLs.  
**Prevention:** Strict HMAC verification, allowlist org/repo, indexer validates input.  
**Phase:** Security hardening.

## 5. Observability blind spots

**Warning signs:** No trace correlation from HTTP → retriever → stores.  
**Prevention:** OTEL context propagation, structured logs with `trace_id`.  
**Phase:** Observability completion.
