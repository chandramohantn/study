# Architectural Decision Questions — Production

> **Questions every AI/ML architect must answer before building a production AI system**
>
> These questions are derived from practices at Google, Meta, Netflix, Uber, Spotify, Airbnb, and Microsoft — companies that operate ML systems at scale. They cover what separates a successful POC from a reliable production system.

---

## How to Use This Document

This is organized in the order you'd typically make decisions when taking an AI system to production. Some questions reference POC findings — use your POC learnings to answer them.

For each question:
- **Answered** → document the decision and rationale
- **Unanswered** → this is a design gap that must be resolved
- **Disputed** → escalate for architectural review

---

## Category 1: Problem Validation & Business Alignment

> *Before investing in production, confirm the problem is validated and the business case is clear.*

| # | Question | Why It Matters |
|---|----------|---------------|
| 1 | Did the POC validate our hypothesis? What was the evidence? | Don't let "it kind of works" become a production investment. Reference concrete POC results. |
| 2 | What is the business case? ROI, cost savings, revenue impact? | Production systems need ongoing investment. Quantify the return to justify operational costs. |
| 3 | Who owns this system long-term? Which team maintains it? | AI systems without clear ownership degrade silently. Assign ownership before building. |
| 4 | What are the SLAs we're committing to? (availability, accuracy, latency) | Production means promises. Define what you're guaranteeing and what the consequences of failure are. |
| 5 | What is the user scale? Current and projected? | 100 users vs 100,000 users require fundamentally different architectures. |
| 6 | What regulatory/compliance requirements apply? | GDPR, AI Act, HIPAA, SOC2, internal AI governance. These shape data handling, logging, and model choices. |
| 7 | Is this a differentiator or commodity? Build vs buy decision. | If your competitive advantage isn't in the AI layer, consider managed services rather than building from scratch. |

---

## Category 2: Data Architecture

> *Production data problems are fundamentally different from POC data problems. You're now dealing with freshness, scale, quality at volume, and governance.*

| # | Question | Why It Matters |
|---|----------|---------------|
| 8 | What is the data pipeline? Source → Processing → Storage → Serving. | End-to-end data flow must be automated, monitored, and recoverable. No manual steps. |
| 9 | How will data be kept fresh? What's the update cadence? | POC used a static snapshot. Production needs continuous ingestion — daily, hourly, or real-time? |
| 10 | What happens when source data changes format or schema? | Upstream changes will break your pipeline eventually. How do you detect and handle schema evolution? |
| 11 | How do we handle data quality at scale? | Validation rules, anomaly detection, completeness checks, deduplication. What gates prevent bad data from entering the system? |
| 12 | What is the data retention policy? | How long do we store raw data, processed data, embeddings, and user interactions? Legal and cost implications. |
| 13 | How do we handle PII and sensitive data? | Masking, encryption, access controls, right-to-deletion, audit logs. This affects every component. |
| 14 | What is the data lineage and provenance strategy? | Can we trace any output back to its source data? Critical for debugging, compliance, and trust. |
| 15 | How will we version datasets? | When data changes, how do we know which version was used for training, evaluation, or indexing? |
| 16 | What's the disaster recovery plan for data? | If the vector index corrupts or the feature store goes down, how quickly can we rebuild? |
| 17 | What is the ground truth collection strategy at scale? | POC used 100 expert-labeled cases. Production needs continuous ground truth for monitoring and retraining. |

---

## Category 3: Model & AI Architecture

> *Production model decisions prioritize reliability, maintainability, and cost-effectiveness over raw performance.*

| # | Question | Why It Matters |
|---|----------|---------------|
| 18 | What is the production model choice and why? | May differ from POC. Consider: cost at scale, latency, reliability, vendor risk, data privacy. |
| 19 | Do we need model redundancy / fallback? | If primary model goes down (API outage, rate limit), what serves traffic? Fallback model? Cached responses? Graceful degradation? |
| 20 | What's the prompt/chain versioning strategy? | Prompts are code. How do we version, test, review, and roll back prompt changes? |
| 21 | Should we fine-tune, and if so, on what cadence? | Fine-tuning improves quality but adds complexity: training pipelines, data curation, evaluation, deployment. |
| 22 | What's the embedding strategy at scale? | Batch vs real-time embedding. Incremental vs full re-index. Embedding model upgrades require full re-indexing. |
| 23 | What's the retrieval architecture? | Dense only? Hybrid (dense + sparse)? With reranker? Multi-stage? The answer depends on corpus size and query patterns. |
| 24 | How do we handle context window limits at scale? | What happens when context exceeds the window? Truncation strategy, summarization, or multi-pass? |
| 25 | What guardrails are in place? | Input validation, output filtering, PII detection, toxicity checks, prompt injection defense. Non-negotiable for production. |
| 26 | What's the caching strategy? | Response cache, embedding cache, retrieval cache. Critical for cost and latency at scale. |
| 27 | Single model vs ensemble/routing? | Can a cheaper model handle 80% of traffic while expensive models handle complex cases? Router + tiered models. |

---

## Category 4: System Architecture & Infrastructure

> *Production AI systems are distributed systems. All distributed systems concerns apply.*

| # | Question | Why It Matters |
|---|----------|---------------|
| 28 | What is the end-to-end system architecture? | Services, databases, queues, caches, external dependencies. Draw the complete picture. |
| 29 | How does the system scale horizontally? | Auto-scaling rules, stateless design, connection pooling. What happens at 10x traffic? |
| 30 | What's the deployment architecture? | Kubernetes? Serverless? Managed services? Region selection? Multi-region? |
| 31 | What are the service boundaries? | Monolith vs microservices. What's a separate service vs internal module? |
| 32 | What are the integration points and failure modes? | Upstream and downstream systems. For each: what happens if it's slow, down, or returns garbage? |
| 33 | What's the API contract? | Versioning, backwards compatibility, rate limiting, authentication, pagination. |
| 34 | How do we handle async vs sync processing? | User-facing queries need sync (fast). Background tasks (indexing, evaluation) can be async. |
| 35 | What's the infrastructure cost model? | Compute, API calls, storage, bandwidth. Monthly estimate at expected traffic. |
| 36 | What's the cold start behavior? | After deployment, cache is empty, index may be warming. How does the system behave initially? |
| 37 | What is the network architecture? | VPC, private endpoints, what crosses network boundaries? Data that hits external APIs. |

---

## Category 5: Evaluation & Quality

> *In production, evaluation is not a one-time event — it's a continuous system.*

| # | Question | Why It Matters |
|---|----------|---------------|
| 38 | What is the offline evaluation strategy? | Regression datasets, metrics, baselines, evaluation pipeline. How do we know quality before deploying? |
| 39 | What is the online evaluation strategy? | Production sampling, LLM judges, human review. How do we know quality after deploying? |
| 40 | What regression dataset exists and how does it grow? | Every production failure should become a permanent test case. Define the growth pipeline. |
| 41 | What are the deployment gates? | What quality/performance thresholds must pass before code reaches production? |
| 42 | How do we detect model/data drift? | Query distribution changes, embedding drift, provider model updates. All silently degrade quality. |
| 43 | How do we compare two system versions? | A/B testing, shadow evaluation, canary deployment. You need a method to compare before committing. |
| 44 | What's the human evaluation cadence? | Judges drift. Models drift. Periodic human review calibrates automated metrics. Weekly? Monthly? |
| 45 | How do we measure business impact, not just technical metrics? | Ticket deflection, time saved, user satisfaction. Connect technical quality to business outcomes. |

---

## Category 6: Reliability & Operations

> *Google: "Hope is not a strategy." Production AI needs the same operational discipline as any critical system.*

| # | Question | Why It Matters |
|---|----------|---------------|
| 46 | What SLOs are we committing to? | Availability (99.9%), latency (P95 < 4s), quality (faithfulness > 95%). Define, measure, alert. |
| 47 | What's the monitoring strategy? | Metrics (latency, errors, cost), traces (per-request flow), logs (debugging). Three pillars of observability. |
| 48 | What alerting rules exist? | What conditions page someone? What's a warning vs critical? Who gets alerted? |
| 49 | What's the on-call story? | Who responds at 2 AM? What runbooks exist? What's the escalation path? |
| 50 | What's the deployment strategy? | Canary → gradual rollout → full. With automated rollback on quality regression. |
| 51 | What's the rollback plan? | If a deployment degrades quality, how quickly can we revert? Minutes, not hours. |
| 52 | How do we handle vendor outages? (LLM provider down) | Circuit breakers, fallback models, cached responses, graceful degradation. |
| 53 | What's the capacity planning approach? | How do we know when to scale up? Load testing cadence, growth projections, bottleneck identification. |
| 54 | What happens during traffic spikes? | Rate limiting, queue-based processing, auto-scaling. Define behavior under pressure. |
| 55 | How do we handle cost control? | Budget alerts, cost per request tracking, automatic throttling if budget exceeded. |

---

## Category 7: Security, Safety & Compliance

> *Production AI systems are attack surfaces. They generate content. They access data. They make decisions.*

| # | Question | Why It Matters |
|---|----------|---------------|
| 56 | How do we prevent prompt injection? | Input sanitization, system prompt protection, output filtering. Active area of attack. |
| 57 | How do we prevent data leakage through the model? | System prompt exposure, training data extraction, PII in responses. |
| 58 | What content safety filters are in place? | Toxicity, harmful advice, inappropriate content. Both input and output filtering. |
| 59 | What access control model applies? | Who can query the system? Who can modify prompts? Who can access traces/logs? RBAC at every layer. |
| 60 | How are API keys and secrets managed? | Rotation, vault storage, least-privilege access. No hardcoded credentials anywhere. |
| 61 | Is there an AI ethics review required? | Bias assessment, fairness testing, transparency requirements. Check organizational policy. |
| 62 | What audit trail exists? | For compliance: who queried what, when, what was the response? Retention requirements. |
| 63 | How do we handle adversarial users? | Users trying to jailbreak, extract data, or abuse the system. Rate limiting, detection, blocking. |

---

## Category 8: Cost & Sustainability

> *The #1 killer of production AI systems is cost, not quality.*

| # | Question | Why It Matters |
|---|----------|---------------|
| 64 | What is the cost per request at expected traffic? | LLM tokens + embedding + retrieval + compute + storage. Know this number. |
| 65 | What is the monthly operational cost? | Infrastructure + API costs + monitoring + evaluation + human review. Full picture. |
| 66 | How does cost scale with traffic? | Linear? Sub-linear (caching helps)? Super-linear (rate limits force expensive fallbacks)? |
| 67 | What cost optimization levers exist? | Smaller models for simple queries, caching, batching, shorter prompts, fewer retrieval rounds. |
| 68 | Is the cost justified by the business value? | If cost/successful task > value/successful task, the system is a net negative. |
| 69 | What's the cost monitoring and alerting strategy? | Daily cost tracking, budget alerts, automatic throttling. No surprise bills. |

---

## Category 9: Team & Process

> *Production AI systems are not projects — they're products that need ongoing investment.*

| # | Question | Why It Matters |
|---|----------|---------------|
| 70 | Who maintains this system after launch? | Clear ownership: team, rotation, knowledge transfer. Orphaned AI systems decay fastest. |
| 71 | What's the change management process? | How are prompt changes, model upgrades, and data updates reviewed, tested, and deployed? |
| 72 | How do we handle knowledge transfer? | Documentation, runbooks, architecture decision records. New team members must onboard quickly. |
| 73 | What's the incident response process? | Incident detection → triage → mitigation → root cause → prevention. Standard SRE practices apply. |
| 74 | What's the experiment/iteration cadence? | How often do we try new models, prompts, retrievers? Continuous improvement, not set-and-forget. |
| 75 | How do we collect and incorporate user feedback? | Thumbs up/down, explicit feedback, implicit signals. This feeds the continuous improvement loop. |

---

## Category 10: Future-Proofing & Evolution

> *AI technology changes fast. Design for change, not for permanence.*

| # | Question | Why It Matters |
|---|----------|---------------|
| 76 | How do we swap the LLM without rewriting the system? | Abstract the model layer. If GPT-5 drops tomorrow, what's the migration effort? |
| 77 | How do we handle embedding model upgrades? | Changing embedding models requires re-indexing everything. Plan for this operationally. |
| 78 | What's the strategy for incorporating new AI capabilities? | Multi-modal, longer context, function calling, reasoning models. Design extensibility. |
| 79 | How do we sunset or deprecate this system? | If a better approach emerges, what's the migration path? How do we redirect users? |
| 80 | What technical debt are we knowingly accepting? | Every production system has tech debt. Document it so it can be addressed deliberately. |

---

## Quick Reference: The 15 Questions That Kill Production AI Systems

The most common reasons production AI systems fail, framed as questions you must answer:

1. **Who owns this system and maintains it after launch?** (Orphan problem)
2. **How does data stay fresh and correct?** (Staleness problem)
3. **How do we know when quality degrades?** (Silent failure problem)
4. **What happens when the LLM provider goes down?** (Vendor dependency problem)
5. **What's the cost at 10x current traffic?** (Cost explosion problem)
6. **How do we prevent hallucination at scale?** (Safety problem)
7. **How do we roll back a bad deployment in minutes?** (Rollback problem)
8. **How does the evaluation dataset grow over time?** (Regression coverage problem)
9. **How do we detect drift without users reporting it?** (Drift problem)
10. **What's the cold start experience?** (Day-1 problem)
11. **How do we handle adversarial inputs?** (Security problem)
12. **What guardrails prevent harmful outputs?** (Safety problem)
13. **How do we A/B test changes before full rollout?** (Experimentation problem)
14. **What's the incident response plan?** (Operational readiness problem)
15. **Is the business value still justified at production cost?** (Sustainability problem)

---

## The POC → Production Gap

| Dimension | POC Reality | Production Requirement |
|-----------|-------------|----------------------|
| Data | Static snapshot, manual | Automated pipeline, fresh, validated |
| Scale | Single user, 10 QPS | Thousands of users, auto-scaling |
| Reliability | "It mostly works" | 99.9% availability, SLOs, alerting |
| Quality | Manual spot-checking | Continuous evaluation, regression gates |
| Security | None | Auth, guardrails, audit, compliance |
| Cost | "Budget for testing" | Sustainable unit economics |
| Operations | Developer runs it | On-call, runbooks, incident response |
| Evolution | "We'll figure it out" | Model upgrades, data drift, versioning |

Every row is an architectural decision you must make for production that you could skip for POC.
