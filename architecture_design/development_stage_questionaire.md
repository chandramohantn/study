# Stage-by-Stage Architectural Questions — AI/ML/DL/GenAI Projects

> **Mandatory and situational questions for every stage of the AI/ML lifecycle, with acceptance criteria to gate progression between stages.**
>
> Use this as a stage-gate checklist. You may not move to the next stage until the current stage's acceptance criteria are satisfied.

---

## How to Use This Document

Each stage contains:
- **Mandatory Questions** — Must be answered before the stage is considered complete
- **Situational Questions** — Answer if applicable to your project type (marked with context)
- **Acceptance Criteria** — The conditions that must be TRUE to exit the stage

**Flow:**

```text
Stage 1: Problem Framing
    ↓ [Acceptance Criteria Met]
Stage 2: Data Exploration & Analysis
    ↓ [Acceptance Criteria Met]
Stage 3: Data Preparation & Preprocessing
    ↓ [Acceptance Criteria Met]
Stage 4: Feature Engineering / Indexing
    ↓ [Acceptance Criteria Met]
Stage 5: Model Selection & Experimentation
    ↓ [Acceptance Criteria Met]
Stage 6: Training / Fine-Tuning
    ↓ [Acceptance Criteria Met]
Stage 7: Evaluation & Validation
    ↓ [Acceptance Criteria Met]
Stage 8: Inference & Serving
    ↓ [Acceptance Criteria Met]
Stage 9: Integration & Deployment
    ↓ [Acceptance Criteria Met]
Stage 10: Monitoring & Observability
    ↓ [Acceptance Criteria Met]
Stage 11: Lifecycle Management & Continuous Improvement
```

---

## Stage 1: Problem Framing

> *Define what we're solving, for whom, and how we'll know it worked. This stage is purely analytical — no code, no data work.*

### Mandatory Questions

| # | Question | What a Good Answer Looks Like |
|---|----------|-------------------------------|
| 1 | What is the exact problem we are solving? | One sentence, specific, measurable. Not "improve customer experience" but "reduce average support response time from 15 min to < 2 min for Tier-1 queries." |
| 2 | Who is the end user and what is their current process? | Named persona, described workflow, identified pain points. |
| 3 | What is the current baseline performance? | Quantified: "Human accuracy is ~78%, takes 15 minutes." If no baseline exists, state how you'll establish one. |
| 4 | Is AI/ML the right approach? What simpler alternatives were considered? | Document: rule-based, keyword search, heuristics. If they suffice, don't use AI. |
| 5 | What type of AI task is this? | Classification, regression, generation, retrieval, RAG, agent, detection, recommendation, ranking. |
| 6 | What are the success metrics and thresholds? | 2-4 metrics with specific numbers: "Accuracy > 85%", "Latency P95 < 3s", "Faithfulness > 95%." |
| 7 | What are the hard constraints? | Budget, latency, data restrictions, compliance, technology mandates. Non-negotiable. |
| 8 | What is the input and output contract? | Input type/format → Output type/format. E.g., "Text query → Text answer with citations." |
| 9 | What are the failure modes and their cost? | False positives vs false negatives — which is more costly? What happens on failure? |
| 10 | What is the scope boundary? | Explicit in-scope and out-of-scope list. |

### Situational Questions

| # | Question | When to Ask |
|---|----------|-------------|
| S1 | Is this real-time or batch? | When latency requirements are unclear |
| S2 | Is this user-facing or internal tooling? | Affects quality bar and UX requirements |
| S3 | Are there existing models/solutions we can leverage? | Before building from scratch |
| S4 | What regulatory requirements apply? | Healthcare, finance, EU AI Act |
| S5 | Is this a POC or production build? | Determines depth of all subsequent stages |

### Acceptance Criteria

| # | Criteria | Verified By |
|---|----------|------------|
| ✓ | Problem statement is specific, measurable, and agreed by stakeholders | Stakeholder sign-off |
| ✓ | AI approach is justified over simpler alternatives | Documented rationale |
| ✓ | Success metrics and thresholds are defined | Written and agreed |
| ✓ | Input/output contract is defined | Schema or example |
| ✓ | Constraints are documented and non-negotiable items flagged | Constraint list |
| ✓ | Scope boundaries are explicit | In-scope/out-of-scope list |

---

## Stage 2: Data Exploration & Analysis

> *Understand what data exists, its quality, coverage, and suitability for the problem. This stage determines whether we CAN build what Stage 1 defined.*

### Mandatory Questions

| # | Question | What a Good Answer Looks Like |
|---|----------|-------------------------------|
| 1 | What data sources are available? | Complete inventory: source name, owner, format, access method, volume. |
| 2 | Can we access the data? Do we have permissions? | Access granted and tested, not "pending approval." |
| 3 | What is the data format? | Structured (CSV, DB) / Semi-structured (JSON, XML) / Unstructured (PDF, text, images). Per source. |
| 4 | What is the data volume? | Row counts, file sizes, document counts. Is it enough for the approach? |
| 5 | What is the data quality? | Completeness (% missing values), accuracy (spot-check results), consistency (format uniformity). |
| 6 | What is the data distribution? | Class balance (for classification), value ranges (for regression), topic coverage (for GenAI). |
| 7 | Does the data contain the signal needed to solve the problem? | Evidence that relevant information exists. E.g., "The docs do contain answers to 90% of top-50 user queries." |
| 8 | What is the label/ground-truth situation? | Labels exist / need creation / can be derived / not applicable (unsupervised/GenAI). |
| 9 | Are there data gaps or blind spots? | Missing categories, time periods, user segments, edge cases. |
| 10 | What is the data freshness? | Last updated when? Update frequency? Stale data impact? |
| 11 | Are there duplicates, noise, or corruption? | Duplicate rate, encoding issues, truncation, OCR errors, parsing failures. |
| 12 | What is the data coverage relative to the problem scope? | Does the data cover all scenarios in Stage 1's scope? |

### Situational Questions

| # | Question | When to Ask |
|---|----------|-------------|
| S1 | Is there class imbalance? What's the ratio? | Classification problems |
| S2 | Are there temporal patterns or seasonality? | Time-series or evolving data |
| S3 | Is the data representative of production traffic? | When POC data may differ from reality |
| S4 | Are there multiple languages? What's the distribution? | Multi-lingual systems |
| S5 | What is the document structure? Headers, tables, images? | RAG / document processing |
| S6 | Are there sensitive columns/fields? (PII, PHI) | Regulated data |
| S7 | Can we profile the data statistically? | When distributions matter (ML models) |
| S8 | What is the relationship between data entities? | When data spans multiple tables/sources |
| S9 | How was the data originally collected? Any selection bias? | When fairness/bias is a concern |
| S10 | Is there concept drift over time? | When data patterns change |

### Acceptance Criteria

| # | Criteria | Verified By |
|---|----------|------------|
| ✓ | All required data sources identified and access confirmed | Access tested, not just "requested" |
| ✓ | Data quality assessed quantitatively | Completeness %, duplicate %, corruption rate documented |
| ✓ | Data coverage is sufficient for the problem scope | Gap analysis completed |
| ✓ | Data distribution understood | Distribution plots / statistics produced |
| ✓ | Ground truth / labeling strategy defined | Either labels exist or creation plan is documented |
| ✓ | Data gaps identified with mitigation plan | Gap list with actions |
| ✓ | Decision: data is sufficient to proceed OR data blockers escalated | Explicit Go/No-Go on data |

---

## Stage 3: Data Preparation & Preprocessing

> *Transform raw data into the format the AI system needs. This stage produces clean, processed, ready-to-use data.*

### Mandatory Questions

| # | Question | What a Good Answer Looks Like |
|---|----------|-------------------------------|
| 1 | What cleaning steps are required? | Specific list: remove nulls, fix encoding, deduplicate, normalize, handle outliers. Per data source. |
| 2 | What transformation logic is needed? | Text: lowercasing, tokenization, lemmatization. Tabular: normalization, one-hot encoding. Documents: parsing, extraction. |
| 3 | How do we handle missing values? | Strategy per field: impute (mean/median/mode), drop, flag, or model-based imputation. Justified. |
| 4 | How do we handle duplicates? | Exact duplicates: remove. Near-duplicates: deduplication strategy (hash, similarity threshold). |
| 5 | What is the train/validation/test split strategy? | Ratio (70/15/15 or similar), splitting method (random, temporal, stratified), and why. |
| 6 | Is the preprocessing deterministic and reproducible? | Same input always produces same output. No random steps without fixed seeds. |
| 7 | How do we validate the preprocessing output? | Assertions: row counts preserved, no unexpected nulls introduced, distributions match expectations. |
| 8 | What is the output format and storage location? | Processed data format (Parquet, JSON, vectors) and where it's stored. |
| 9 | How long does preprocessing take? | Important for iteration speed. If it takes 8 hours, experimentation slows down. |
| 10 | Is the preprocessing pipeline documented and versioned? | Script, parameters, dependencies — another person could reproduce it. |

### Situational Questions (by AI type)

| # | Question | When to Ask |
|---|----------|-------------|
| S1 | What is the chunking strategy? (size, overlap, method) | RAG / document retrieval systems |
| S2 | How do we parse complex documents? (tables, images, headers) | When source data is PDFs, HTML, DOCX |
| S3 | How do we handle multi-modal data? | When combining text, images, audio |
| S4 | What text normalization is appropriate? | NLP tasks — but beware over-normalizing for LLMs |
| S5 | Do we need data augmentation? | When training data is scarce (small dataset ML) |
| S6 | How do we handle class imbalance? | Classification with skewed distributions |
| S7 | What encoding strategy for categorical variables? | Tabular ML models |
| S8 | How do we handle time-zone and timestamp normalization? | Time-series or event data |
| S9 | Do we need to anonymize or mask data? | PII present in training/processing data |
| S10 | What metadata needs to be preserved during processing? | RAG: source document, page number, section, author, date |

### Acceptance Criteria

| # | Criteria | Verified By |
|---|----------|------------|
| ✓ | Preprocessing pipeline is scripted, not manual | Runnable script exists |
| ✓ | Output data passes quality assertions | Automated checks: no nulls where unexpected, correct row counts, valid formats |
| ✓ | Train/val/test splits created with no data leakage | Split verification (no overlapping IDs across splits) |
| ✓ | Preprocessing is reproducible | Re-running produces identical output |
| ✓ | Processing time is acceptable for iteration speed | Documented: "Takes X minutes for full dataset" |
| ✓ | Output format matches downstream component expectations | Verified: next stage can read the output |
| ✓ | Metadata preserved where needed | Spot-check: source traceability intact |

---

## Stage 4: Feature Engineering / Embedding / Indexing

> *Transform processed data into the representation the model will consume. For ML: features. For GenAI/RAG: embeddings and indexes. For DL: tensor representations.*

### Mandatory Questions

| # | Question | What a Good Answer Looks Like |
|---|----------|-------------------------------|
| 1 | What representation does the model need? | Features (tabular ML), embeddings (RAG/semantic), tokens (LLM), tensors (DL). Explicit per component. |
| 2 | What embedding model are we using and why? | Model name, dimensions, domain performance, cost, multilingual support. Justified against alternatives. |
| 3 | How do we compute and store representations? | Batch vs real-time. Storage: vector DB, feature store, file-based. |
| 4 | What is the indexing strategy? | Index type (HNSW, IVF, flat), distance metric (cosine, dot, L2), parameters (ef, M). |
| 5 | How do we validate the representation quality? | Retrieval sanity checks, nearest-neighbor spot checks, embedding clustering visualization. |
| 6 | How do we handle representation updates? | Incremental (add new) vs full re-index. What triggers a re-index? |
| 7 | What is the dimensionality and storage cost? | Vectors × dimensions × bytes = storage. At scale, this becomes significant. |
| 8 | How long does the full indexing pipeline take? | Critical for understanding rebuild time and freshness latency. |

### Situational Questions

| # | Question | When to Ask |
|---|----------|-------------|
| S1 | What features have the highest predictive power? | Traditional ML — feature importance analysis |
| S2 | Are there feature interactions we should capture? | When polynomial/cross features may help |
| S3 | Do we need real-time feature computation? | Online ML serving (recommendations, fraud detection) |
| S4 | Should we use a feature store? | When features are shared across models or need point-in-time correctness |
| S5 | How do we handle high-cardinality categorical features? | Embeddings, hashing, target encoding — common in recommendation systems |
| S6 | What metadata fields should be indexable/filterable? | RAG: filter by department, date, document type at query time |
| S7 | Do we need hybrid search (dense + sparse)? | When keyword matching is important alongside semantic similarity |
| S8 | What is the embedding cache strategy? | When the same text is embedded repeatedly |
| S9 | How do we handle multi-vector representations? | ColBERT-style, late interaction, multi-modal |
| S10 | How do we version the feature/embedding schema? | When the pipeline evolves and old representations must coexist |

### Acceptance Criteria

| # | Criteria | Verified By |
|---|----------|------------|
| ✓ | Representations computed for all processed data | Count verification: processed items = indexed items |
| ✓ | Quality validated with sanity checks | Manual spot-check: "query X retrieves expected documents" |
| ✓ | Indexing pipeline is automated and reproducible | Script exists, re-run produces same index |
| ✓ | Index is queryable and returns results in acceptable time | Benchmark: query latency within target |
| ✓ | Storage and cost are within budget | Size documented, cost estimated |
| ✓ | Update strategy defined (incremental or rebuild) | Documented and tested |

---

## Stage 5: Model Selection & Experimentation

> *Choose the right model/approach based on task requirements, constraints, and empirical evidence. This stage is about exploration — try multiple approaches, measure, and decide.*

### Mandatory Questions

| # | Question | What a Good Answer Looks Like |
|---|----------|-------------------------------|
| 1 | What candidate approaches are we evaluating? | At least 2-3 options with rationale. E.g., "GPT-4o vs Claude vs fine-tuned Llama" or "XGBoost vs neural net vs logistic regression." |
| 2 | What is the evaluation protocol for comparing approaches? | Same test set, same metrics, same conditions. Apples-to-apples comparison. |
| 3 | What are the trade-offs between candidates? | Quality vs cost vs latency vs complexity. Document for each option. |
| 4 | What quick experiments can eliminate bad options? | Small-scale tests that rule out approaches in hours, not weeks. |
| 5 | What is the model's input/output contract? | Max input size, output format, handling of edge cases. |
| 6 | Is the model API-based or self-hosted? | Implications: latency, cost, data privacy, availability, control. |
| 7 | What are the licensing and usage restrictions? | Open-source license, commercial use allowed, fine-tuning permitted? |
| 8 | How complex is the integration? | SDK availability, API stability, documentation quality, community support. |
| 9 | What is the cost per prediction/generation? | At expected traffic: daily/monthly cost. |
| 10 | Is there a clear winner, or do we need more experimentation? | Decision documented with evidence, or explicit plan for more testing. |

### Situational Questions

| # | Question | When to Ask |
|---|----------|-------------|
| S1 | Do we need a baseline model first? (e.g., TF-IDF before transformers) | When a simple baseline might suffice |
| S2 | Should we use an ensemble or single model? | When different models excel on different subsets |
| S3 | Is transfer learning applicable? | When task-specific data is limited |
| S4 | Do we need model interpretability/explainability? | Regulated domains, user-facing decisions |
| S5 | What is the model's behavior on out-of-distribution inputs? | When inputs may differ from training data |
| S6 | Should we use a smaller model with a router? | Cost optimization: cheap model for easy cases, expensive for hard |
| S7 | What prompt engineering strategies should we test? | GenAI: zero-shot, few-shot, chain-of-thought, structured output |
| S8 | Is RAG sufficient or do we need fine-tuning? | When domain knowledge is needed |
| S9 | What context window size does the task require? | When inputs are long (documents, conversations) |
| S10 | How does the model handle the language(s) we need? | Multi-lingual performance varies significantly across models |

### Acceptance Criteria

| # | Criteria | Verified By |
|---|----------|------------|
| ✓ | Multiple approaches evaluated with empirical results | Comparison table with metrics |
| ✓ | A model/approach is selected with documented rationale | Decision record: what, why, trade-offs accepted |
| ✓ | Cost per prediction estimated at scale | Cost calculation documented |
| ✓ | Latency measured and within requirements | Benchmark results |
| ✓ | Edge case behavior understood | Test with adversarial/unusual inputs |
| ✓ | Licensing and data privacy implications reviewed | No blockers identified |
| ✓ | Decision is not "the first thing we tried" | Evidence of comparison |

---

## Stage 6: Training / Fine-Tuning / Prompt Engineering

> *Build the model or refine the approach using your data. For traditional ML: train models. For GenAI: engineer prompts, fine-tune, or configure RAG pipelines.*

### Mandatory Questions

| # | Question | What a Good Answer Looks Like |
|---|----------|-------------------------------|
| 1 | What is the exact training/development pipeline? | Steps, dependencies, compute requirements, expected duration. |
| 2 | What hyperparameters/configuration are we using and why? | Not defaults — justified choices. Learning rate, batch size, epochs, temperature, top-k, chunk size. |
| 3 | How do we prevent overfitting / data contamination? | Validation set monitoring, regularization, or for GenAI: test queries not in RAG corpus. |
| 4 | What is the training/development compute requirement? | GPU type, hours, cost estimate. For GenAI prompts: API call budget for iteration. |
| 5 | How do we version the model/prompts/pipeline? | Every experiment must be reproducible. What changed, what was the result? |
| 6 | What are the iteration cycles? How fast can we experiment? | Time from hypothesis to result. If it's 2 days per experiment, plan accordingly. |
| 7 | What validation do we perform during training/development? | Loss curves, validation metrics, intermediate quality checks. |
| 8 | When do we stop iterating? | Convergence criteria, time box, "good enough" threshold. |

### Situational Questions

| # | Question | When to Ask |
|---|----------|-------------|
| S1 | What is the prompt template and why is it structured this way? | GenAI systems — prompt is the most critical artifact |
| S2 | What few-shot examples do we include and how were they selected? | When few-shot prompting improves quality |
| S3 | What is the fine-tuning dataset and how was it curated? | When fine-tuning a foundation model |
| S4 | What data augmentation is applied during training? | Small dataset ML — augmentation strategy |
| S5 | What is the learning rate schedule? | Deep learning training |
| S6 | How do we handle catastrophic forgetting? (fine-tuning) | When fine-tuning may degrade general capabilities |
| S7 | What is the chain/agent architecture? | Multi-step GenAI: order of operations, tool calls, fallbacks |
| S8 | What system prompt, safety instructions, and guardrails are embedded? | GenAI: preventing harmful outputs, staying on topic |
| S9 | What is the retrieval + generation integration? | RAG: how retrieved context is formatted and injected into prompt |
| S10 | How do we handle context overflow? | When retrieved content exceeds context window |
| S11 | What is the training stability? | DL: loss spikes, NaN gradients, convergence issues |
| S12 | Is curriculum learning or staged training beneficial? | Complex tasks that benefit from easy→hard progression |

### Acceptance Criteria

| # | Criteria | Verified By |
|---|----------|------------|
| ✓ | Model/pipeline produces outputs for all test inputs without errors | End-to-end run completes |
| ✓ | Validation metrics meet minimum threshold | Metrics on validation set documented |
| ✓ | No data leakage between train/val/test | Split isolation verified |
| ✓ | Pipeline is reproducible | Re-running with same config produces consistent results |
| ✓ | Configuration/prompts are versioned | Stored in version control with experiment IDs |
| ✓ | Training cost/time is documented | Budget tracking for compute/API |
| ✓ | Clear stopping criteria met | Documented why iteration stopped |
| ✓ | Known failure modes identified | List of cases where the model struggles |

---

## Stage 7: Evaluation & Validation

> *Rigorously measure the system's quality. This is the stage that determines whether we have something production-worthy or a demo that looks good but fails in reality.*

### Mandatory Questions

| # | Question | What a Good Answer Looks Like |
|---|----------|-------------------------------|
| 1 | What evaluation dataset are we using? | Size, source, composition, ground truth method. Not the same data used for development. |
| 2 | What metrics are we measuring? | Complete list with definitions. Different from training metrics — these are business-relevant. |
| 3 | What is the baseline and how do we compare? | Quantified baseline (current system, human, simple heuristic) with same metrics on same test set. |
| 4 | What is the performance on each metric? | Numbers, not vibes. "Faithfulness: 94.2%, Recall@5: 87.1%, P95 latency: 3.2s." |
| 5 | Does performance meet the thresholds defined in Stage 1? | Explicit comparison: target vs actual for each metric. |
| 6 | What is the performance breakdown by segment? | By intent type, difficulty, language, document type. Averages hide failures. |
| 7 | What are the failure cases? What patterns emerge? | Categorized failure analysis: what types of inputs fail and why? |
| 8 | How robust is the system to edge cases? | Tested with: out-of-scope queries, adversarial inputs, boundary conditions, unusual formatting. |
| 9 | Is there human evaluation? What does it show? | For GenAI: human judges assess quality on a sample. Automated metrics alone aren't sufficient. |
| 10 | Are the results statistically significant? | For comparisons: confidence intervals, not just point estimates. Is +1.2% real or noise? |

### Situational Questions

| # | Question | When to Ask |
|---|----------|-------------|
| S1 | What is the faithfulness / groundedness score? | RAG/GenAI systems |
| S2 | What is the hallucination rate? | Any generative system |
| S3 | What is the retrieval recall/precision at K? | RAG systems |
| S4 | Is there calibration analysis? (confidence vs accuracy) | When the model outputs confidence scores |
| S5 | What is the fairness/bias assessment? | When model decisions affect different groups |
| S6 | What is the latency distribution? (not just average) | All serving systems — P50, P95, P99 |
| S7 | How does performance degrade with scale? | Load testing results |
| S8 | What is the cost per evaluation and total eval budget? | LLM-as-judge evaluation costs |
| S9 | How do LLM judge scores correlate with human scores? | Validating that automated eval is trustworthy |
| S10 | What is the performance on the "Critical" regression set? | Must-not-fail cases |

### Acceptance Criteria

| # | Criteria | Verified By |
|---|----------|------------|
| ✓ | All target metrics evaluated on held-out test set | Metrics report produced |
| ✓ | Performance meets or exceeds thresholds from Stage 1 | Direct comparison documented |
| ✓ | Performance analyzed by segment — no catastrophic segment failures | Segment breakdown table |
| ✓ | Failure cases analyzed and categorized | Failure analysis report |
| ✓ | Human evaluation conducted on representative sample | Human eval scores documented |
| ✓ | Edge cases tested | Adversarial/boundary test results |
| ✓ | Results are reproducible | Re-running eval produces consistent numbers |
| ✓ | Decision: meets bar for next stage OR specific gaps identified | Explicit Go/No-Go |

---

## Stage 8: Inference & Serving

> *Design how the model serves predictions in the target environment. This is where "it works in a notebook" becomes "it works as a service."*

### Mandatory Questions

| # | Question | What a Good Answer Looks Like |
|---|----------|-------------------------------|
| 1 | What is the serving architecture? | API service, batch job, streaming, embedded. Clear choice with rationale. |
| 2 | What is the expected latency and throughput? | P50, P95, P99 targets. Requests/second at peak. |
| 3 | What is the inference pipeline? (step by step) | Input validation → preprocessing → model call → postprocessing → response. All steps documented. |
| 4 | What hardware/compute is required? | GPU type, memory, CPU. For API-based: rate limits, concurrent connections. |
| 5 | How do we handle concurrent requests? | Async, batching, queueing, connection pooling. |
| 6 | What is the cold start time? | Time from deployment to first request served. Cache warmup needed? |
| 7 | What is the cost per inference at expected load? | Calculated: tokens × price, compute × time, including all pipeline stages. |
| 8 | What is the error handling strategy? | Timeout → retry? Model fails → fallback? Invalid input → 400 with message? |
| 9 | What caching strategy reduces cost/latency? | Exact match cache, semantic cache, embedding cache, result cache. TTL per layer. |
| 10 | How do we handle model/prompt updates without downtime? | Blue-green, rolling update, version routing. Zero-downtime deployment. |

### Situational Questions

| # | Question | When to Ask |
|---|----------|-------------|
| S1 | Do we need streaming responses? (token by token) | GenAI chat interfaces |
| S2 | What batching strategy optimizes throughput? | High-throughput batch inference |
| S3 | Do we need GPU inference or is CPU sufficient? | Depends on model size and latency requirements |
| S4 | How do we handle multi-model pipelines? (e.g., embed + retrieve + generate) | RAG and agent systems |
| S5 | What is the model serving framework? (vLLM, TGI, Triton, TorchServe) | Self-hosted model serving |
| S6 | How do we handle rate limiting from upstream APIs? | When using OpenAI/Anthropic with rate limits |
| S7 | Do we need A/B serving (multiple model versions)? | When experimenting in production |
| S8 | What is the input size limit and how do we enforce it? | Preventing context overflow, cost control |
| S9 | How do we handle graceful degradation? | When part of the pipeline is slow/down |
| S10 | What pre-computation can reduce real-time cost? | Embeddings, features, summaries computed ahead of time |

### Acceptance Criteria

| # | Criteria | Verified By |
|---|----------|------------|
| ✓ | Inference pipeline runs end-to-end with target latency | Load test results: P95 within SLA |
| ✓ | Error handling works for all known failure modes | Test each failure scenario |
| ✓ | Cost per inference calculated and within budget | Cost analysis documented |
| ✓ | Caching functional and measurably reduces cost/latency | Cache hit rate measured |
| ✓ | Concurrent load handled without degradation | Load test at expected peak |
| ✓ | Model update mechanism tested | Deploy new version with zero errors |
| ✓ | Graceful degradation works | Kill a dependency, verify fallback activates |

---

## Stage 9: Integration & Deployment

> *Connect the AI system to the real world — upstream data sources, downstream consumers, user interfaces, and CI/CD pipelines.*

### Mandatory Questions

| # | Question | What a Good Answer Looks Like |
|---|----------|-------------------------------|
| 1 | What upstream systems feed into this service? | For each: what data, what format, what happens if it's unavailable. |
| 2 | What downstream systems consume the output? | For each: what they expect, what happens if our service is slow/wrong. |
| 3 | What is the API contract? (versioning, auth, rate limits) | OpenAPI spec or equivalent. Backwards compatibility strategy. |
| 4 | What is the deployment pipeline? (CI/CD) | Code → test → build → deploy stages. Automated, not manual. |
| 5 | What are the deployment gates? | Unit tests, integration tests, evaluation regression, operational checks — all must pass. |
| 6 | What is the deployment strategy? | Canary (5% → 25% → 100%), blue-green, rolling. With automated rollback. |
| 7 | What is the rollback plan and how fast can we execute it? | Target: < 5 minutes from detection to rollback complete. |
| 8 | How do we validate the deployment is healthy? | Smoke tests, health checks, canary metrics comparison. |
| 9 | What permissions/secrets are needed in production? | API keys, DB credentials, network access. All via secrets manager, no hardcoding. |
| 10 | What is the release communication plan? | Who is notified? Documentation updated? Users informed of changes? |

### Situational Questions

| # | Question | When to Ask |
|---|----------|-------------|
| S1 | Does the UI/frontend need changes? | User-facing features |
| S2 | Are there database migrations required? | Schema changes in production |
| S3 | What feature flags control the rollout? | Gradual rollout, quick kill-switch |
| S4 | How do we handle multi-region deployment? | Global services |
| S5 | What is the infrastructure-as-code strategy? | Terraform, CDK, Pulumi for reproducibility |
| S6 | How do we test the integration before production? | Staging environment with realistic data |
| S7 | What is the data migration strategy? | When moving from old system to new |
| S8 | How do we handle backwards compatibility? | When the API contract changes |

### Acceptance Criteria

| # | Criteria | Verified By |
|---|----------|------------|
| ✓ | CI/CD pipeline runs end-to-end: code → test → deploy | Pipeline execution log |
| ✓ | All deployment gates pass (tests, eval, operational checks) | Gate status report |
| ✓ | Canary deployment successful with no regressions | Canary metrics comparison |
| ✓ | Rollback tested and completes within target time | Rollback drill executed |
| ✓ | Health checks and smoke tests pass post-deployment | Automated verification |
| ✓ | Upstream/downstream integrations tested | Integration test results |
| ✓ | Secrets managed properly (no hardcoded credentials) | Security scan passes |
| ✓ | Documentation updated | API docs, runbook, architecture diagram current |

---

## Stage 10: Monitoring & Observability

> *Once deployed, the system must be observable. You need to know when it's healthy, when it's degrading, and why — before users report problems.*

### Mandatory Questions

| # | Question | What a Good Answer Looks Like |
|---|----------|-------------------------------|
| 1 | What SLOs are defined for this system? | Availability (99.9%), latency (P95 < 4s), quality (faithfulness > 95%), cost (< $0.03/request). |
| 2 | What metrics are we tracking? | Operational: latency, error rate, throughput. Quality: evaluation scores, drift signals. Cost: per request, daily total. |
| 3 | What does the request trace look like? | Full trace: query → retrieval → context → generation → response, with timings per stage. |
| 4 | How do we detect quality degradation? | Continuous evaluation on sampled traffic + drift detection on distributions. |
| 5 | What alerts exist and who gets notified? | Tiered: Critical (page on-call), Warning (Slack + ticket), Info (dashboard annotation). |
| 6 | What dashboards exist? | Application health, pipeline breakdown, cost tracking, quality trending. |
| 7 | What is the on-call rotation and escalation path? | Named team, rotation schedule, escalation from L1 → L2 → engineering lead. |
| 8 | What runbooks exist for common incidents? | At minimum: high latency, elevated errors, quality drop, cost spike, upstream dependency failure. |
| 9 | How do we track cost in real-time? | Per-request cost attribution, daily aggregation, budget alerts at 80%. |
| 10 | How do we detect data/model drift? | Query distribution monitoring, embedding space drift, model output distribution shifts. |

### Situational Questions

| # | Question | When to Ask |
|---|----------|-------------|
| S1 | Are we sampling production traffic for evaluation? At what rate? | GenAI systems — can't evaluate everything |
| S2 | Do we have canary metrics that compare against baseline continuously? | Post-deployment health |
| S3 | How do we detect prompt injection attempts? | User-facing GenAI systems |
| S4 | What user feedback signals do we capture? | Thumbs up/down, explicit feedback, implicit signals |
| S5 | How do we monitor GPU/compute utilization? | Self-hosted models |
| S6 | What is the log retention policy? | Compliance + debugging needs vs cost |
| S7 | How do we detect silent failures? (system returns answers but quality dropped) | The hardest monitoring challenge in AI |
| S8 | Do we have error budget tracking? | SLO-driven development |
| S9 | How do we attribute quality drops to specific changes? | Correlating deployments with metric shifts |
| S10 | Is there anomaly detection on incoming traffic? | Detecting adversarial attacks, bot traffic |

### Acceptance Criteria

| # | Criteria | Verified By |
|---|----------|------------|
| ✓ | SLOs defined, measured, and visible on dashboard | Dashboard screenshot |
| ✓ | Alerting rules active and tested (alert fires when condition met) | Alert testing drill |
| ✓ | Full request traces captured and queryable | Sample trace retrieved and inspected |
| ✓ | Runbooks exist for top-5 failure scenarios | Runbook review |
| ✓ | On-call rotation assigned and notified | Team acknowledged |
| ✓ | Cost tracking active with budget alerts | Alert threshold configured |
| ✓ | Quality sampling running on production traffic | Sample evaluation results visible |
| ✓ | Drift detection active | Baseline distributions captured, drift checks scheduled |

---

## Stage 11: Lifecycle Management & Continuous Improvement

> *AI systems are never "done." This stage defines how the system evolves, improves, and stays healthy over time. This is what separates mature AI teams from those who ship and forget.*

### Mandatory Questions

| # | Question | What a Good Answer Looks Like |
|---|----------|-------------------------------|
| 1 | What is the model/prompt update cadence? | Defined schedule: weekly prompt review, monthly model evaluation, quarterly architecture review. |
| 2 | How does the evaluation dataset grow over time? | Failure mining from production → human review → promote to regression suite. Target: 20-50 new cases/week. |
| 3 | How do we handle knowledge base / data freshness? | Automated ingestion pipeline, staleness alerts, update lag tracking. |
| 4 | What is the experiment framework? | How we propose, test, measure, and ship improvements. Formal experiment tracking. |
| 5 | How do we compare system versions? | A/B testing, shadow evaluation, canary with metrics comparison. |
| 6 | What is the regression testing strategy? | Critical cases on every commit, gold set before release, extended set nightly. |
| 7 | How do we handle model provider changes? (new model versions, deprecations) | Evaluate new versions against regression set before adopting. Fallback plan. |
| 8 | How do we incorporate user feedback? | Feedback → categorization → prioritization → improvement backlog → implementation → measurement. |
| 9 | What is the technical debt management strategy? | Documented shortcuts, scheduled cleanup sprints, debt doesn't accumulate forever. |
| 10 | What is the system's sunset/deprecation plan? | How do we shut it down if a better approach emerges? Migration path for users. |

### Situational Questions

| # | Question | When to Ask |
|---|----------|-------------|
| S1 | Do we need periodic retraining? On what cadence? | Traditional ML with data drift |
| S2 | How do we handle embedding model upgrades? (requires full re-index) | RAG systems with evolving embedding models |
| S3 | How do we manage prompt versioning across environments? | GenAI with multiple environments (dev/staging/prod) |
| S4 | What is the model governance process? (approval for changes) | Regulated industries |
| S5 | How do we handle A/B tests that run indefinitely? | When no variant clearly wins |
| S6 | What is the data re-labeling strategy? | When ground truth labels become stale or incorrect |
| S7 | How do we handle feature store evolution? | When features are added/removed/changed |
| S8 | What is the compliance audit cadence? | Regulated systems need periodic review |
| S9 | How do we benchmark against competing approaches? | Staying aware of better alternatives |
| S10 | What are the KPIs for the continuous improvement program itself? | Measuring whether the improvement process is working |

### Acceptance Criteria

| # | Criteria | Verified By |
|---|----------|------------|
| ✓ | Update cadence defined and scheduled | Calendar entries, team agreement |
| ✓ | Evaluation dataset growth pipeline active | Cases added in last 30 days |
| ✓ | Experiment tracking system operational | Past experiments logged with results |
| ✓ | Regression suite running in CI/CD | Pipeline logs show regression runs |
| ✓ | User feedback collection mechanism active | Feedback received and categorized |
| ✓ | Data freshness pipeline monitored | No staleness alerts in last period |
| ✓ | Technical debt backlog maintained | Debt items listed, prioritized, scheduled |
| ✓ | System owner identified and accountable | Named individual/team |

---

## Summary: Stage-Gate Progression Matrix

| Stage | Key Question It Answers | Blocks If Not Done |
|-------|------------------------|-------------------|
| 1. Problem Framing | "What are we solving and is AI the right approach?" | Everything |
| 2. Data Exploration | "Do we have the data to solve this?" | Stages 3-11 |
| 3. Data Preparation | "Is the data in usable form?" | Stages 4-11 |
| 4. Feature/Embedding/Indexing | "Is the data in model-consumable form?" | Stages 5-11 |
| 5. Model Selection | "What approach works best?" | Stages 6-11 |
| 6. Training/Prompt Engineering | "Does the model perform on our data?" | Stages 7-11 |
| 7. Evaluation | "Does it meet our quality bar?" | Stages 8-11 |
| 8. Inference & Serving | "Can it run at target speed and cost?" | Stages 9-11 |
| 9. Integration & Deployment | "Is it connected and deployed safely?" | Stages 10-11 |
| 10. Monitoring | "Can we see when it breaks?" | Stage 11 |
| 11. Lifecycle Management | "Will it stay healthy over time?" | Long-term success |

---

## The 5 Questions That Gate Every Stage Transition

Before moving from any stage to the next, answer:

1. **Is the work from this stage documented and reproducible?**
2. **Do the acceptance criteria have evidence (not just belief)?**
3. **Are the known risks and limitations written down?**
4. **Does the next stage have everything it needs from this stage?**
5. **Has someone other than the builder reviewed the output?**

If any answer is "no" — don't advance. Resolve first. The cost of going back is always higher than the cost of completing a stage properly.
