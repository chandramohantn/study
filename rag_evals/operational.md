# Operational Evaluation

## Table of Contents

- [Module 1: Operational Evaluation of RAG Systems](#module-1-operational-evaluation-of-rag-systems)
- [First Principle](#first-principle)
- [The Operational Pyramid](#the-operational-pyramid)
- [Layer 1 — Performance Evaluation](#layer-1--performance-evaluation)
  - [Total Latency](#total-latency)
  - [Stage-Level Latency](#stage-level-latency)
  - [Time to First Token (TTFT)](#time-to-first-token-ttft)
  - [Tokens per Second](#tokens-per-second)
- [Layer 2 — Efficiency Evaluation](#layer-2--efficiency-evaluation)
  - [Token Efficiency](#token-efficiency)
  - [Context Utilization](#context-utilization)
  - [Cost per Request](#cost-per-request)
  - [Cost per Successful Task](#cost-per-successful-task)
- [Layer 3 — Reliability Evaluation](#layer-3--reliability-evaluation)
  - [Success Rate](#success-rate)
  - [Failure Rate](#failure-rate)
  - [Retry Rate](#retry-rate)
  - [Timeout Rate](#timeout-rate)
  - [Recovery Rate](#recovery-rate)
- [Layer 4 — Scalability Evaluation](#layer-4--scalability-evaluation)
- [Layer 5 — Resource Evaluation](#layer-5--resource-evaluation)
- [Layer 6 — Operational Quality](#layer-6--operational-quality)
  - [Cache Hit Rate](#cache-hit-rate)
  - [Duplicate Retrieval Rate](#duplicate-retrieval-rate)
  - [Judge Cost](#judge-cost)
- [Observability](#observability)
- [Service-Level Objectives (SLOs)](#service-level-objectives-slos)
- [Operational Regression Testing](#operational-regression-testing)
- [Production Monitoring](#production-monitoring)
- [Correlation Analysis](#correlation-analysis)
- [The Evaluation Matrix](#the-evaluation-matrix)
- [A Production Dashboard](#a-production-dashboard)
- [The Missing Layer: Operational Evaluation as a Control System](#the-missing-layer-operational-evaluation-as-a-control-system)
- [The Complete RAG Evaluation Stack](#the-complete-rag-evaluation-stack)
- [What I'd Study Next](#what-id-study-next)

---

**Operational Evaluation** is what separates a research prototype from a production AI system.

Many engineers spend months optimizing Recall@10, Faithfulness, Groundedness, and Context Precision. Then they deploy the system and discover:

- P95 latency is 18 seconds.
- GPU costs are exploding.
- OpenAI API rate limits are being hit.
- Vector database becomes the bottleneck.
- The reranker doubles latency.
- Cache hit rate is near zero.

From the user's perspective, **the application has failed**, even if the answers are excellent. This is exactly why operational evaluation deserves to be treated as a first-class discipline.

---

## Module 1: Operational Evaluation of RAG Systems

Let's revisit our RAG pipeline:

```text
User Query → Query Processing → Embedding Model → Vector Retrieval → Hybrid Retrieval → Reranking → Context Construction → LLM → Post Processing → Final Response
```

Everything above is a distributed system. Every stage has latency, cost, failure modes, scalability limits, and resource utilization. Operational evaluation measures these properties.

---

## First Principle

The goal is **not** simply "Can the application answer correctly?"

Instead:

> **Can the application answer correctly, reliably, quickly, and economically under production workloads?**

That is a fundamentally different optimization problem.

---

## The Operational Pyramid

I divide operational evaluation into six layers:

```text
        Business SLA
             ▲
       User Experience
             ▲
        Reliability
             ▲
        Performance
             ▲
        Efficiency
             ▲
   Infrastructure Health
```

---

## Layer 1 — Performance Evaluation

> **How fast is the application?**

### Total Latency

Most dashboards show average latency — this is almost useless. Instead measure percentiles:

| Metric | Value  |
| ------ | ------ |
| P50    | 2.1 s  |
| P90    | 4.4 s  |
| P95    | 6.8 s  |
| P99    | 14.5 s |

P99 is often what users complain about.

### Stage-Level Latency

Never measure only end-to-end latency. Break it down:

| Stage          | Latency |
| -------------- | ------- |
| Embedding      | 38 ms   |
| Retriever      | 72 ms   |
| Reranker       | 210 ms  |
| LLM            | 3100 ms |
| Postprocessing | 45 ms   |

Immediately, you know where time is spent. I recommend a waterfall chart visualization:

```text
Embedding       ████
Retriever       ██████
Reranker        ████████████
LLM             ██████████████████████████████
Post Processing ██
```

### Time to First Token (TTFT)

Increasingly important. Users perceive "response begins quickly" as faster, even if total completion time is identical.

| Model | TTFT | Completion |
|-------|------|-----------|
| Model A | 200 ms | 10 seconds |
| Model B | 3 seconds | 6 seconds |

Many users prefer Model A despite longer total time.

### Tokens per Second

Streaming systems should monitor `Generated Tokens / Generation Time`. Low throughput usually indicates GPU bottlenecks.

---

## Layer 2 — Efficiency Evaluation

Performance asks "How fast?" Efficiency asks "At what cost?"

### Token Efficiency

If a simple question like "Warranty?" generates a 12,000-token prompt, you've retrieved far too much context. Measure:

```text
Token Efficiency = Useful Tokens / Prompt Tokens
```

Rarely measured, but incredibly valuable.

### Context Utilization

Suppose you provide 10 retrieved chunks but the answer only uses 2. Eight chunks wasted tokens.

```text
Context Utilization = Evidence Used / Evidence Retrieved
```

One of my favorite enterprise metrics.

### Cost per Request

Break cost into stages:

| Stage     | Cost    |
| --------- | ------- |
| Embedding | $0.0002 |
| Retriever | $0.0001 |
| LLM       | $0.021  |
| Judge     | $0.004  |
| **Total** | **$0.0253** |

Now you know where money goes.

### Cost per Successful Task

A business metric masquerading as an operational metric. If Task Success = 80% and Cost = $0.05/request:

```text
Cost per Success = $0.05 / 0.80 = $0.0625
```

Much more meaningful than cost/request.

---

## Layer 3 — Reliability Evaluation

Suppose answers are great and latency is excellent, but 5% of requests fail. Unacceptable.

### Success Rate

```text
Success Rate = Successful Requests / Total Requests
```

Simple. Essential.

### Failure Rate

Categorize failures — don't lump everything into 500 errors:

- Embedding failure
- Retriever timeout
- LLM timeout
- Rate limit
- Prompt construction error
- JSON parsing failure
- Citation failure
- Tool failure

### Retry Rate

How often must the system retry? High retries may indicate upstream instability.

### Timeout Rate

If the LLM API times out 2% of the time, track separately.

### Recovery Rate

If failures occur, did retries succeed?

---

## Layer 4 — Scalability Evaluation

Most tutorials ignore this. Suppose your RAG works perfectly for 10 users. What about 1,000? 100,000?

Load testing becomes essential. Measure:

```text
Concurrent Users → Latency → Throughput → Failure Rate
```

Observe where the system bends or breaks.

**Key metrics:**
- Requests/second, Queries/minute, Tokens/second (track by stage)
- Queue length — long queues often indicate LLM bottlenecks

---

## Layer 5 — Resource Evaluation

What resources does the application consume?

- CPU, GPU, RAM, Disk, Network
- Vector DB memory
- Redis / Cache

**Useful metrics:** GPU utilization, memory utilization, vector DB CPU, index size, embedding cache size.

---

## Layer 6 — Operational Quality

Higher-level metrics that affect system behavior.

### Cache Hit Rate

If 1,000 users ask "Vacation Policy", should you retrieve, embed, and generate 1,000 times? No — cache.

```text
Cache Hit Rate = Cache Hits / Requests
```

### Duplicate Retrieval Rate

If same chunks are retrieved repeatedly, perhaps cache retrieval results instead.

### Judge Cost

LLM judges also cost money. Track:

```text
Evaluation Cost / Inference Cost
```

Many companies discover evaluation is 10–20% of inference cost.

---

## Observability

Every request should produce a trace:

```yaml
request_id:
query:
embedding_latency:
retrieval_latency:
reranker_latency:
llm_latency:
judge_latency:
retrieved_chunks:
prompt_tokens:
completion_tokens:
cache_hit:
tool_calls:
errors:
final_latency:
```

Without traces, debugging becomes guesswork.

---

## Service-Level Objectives (SLOs)

Operational evaluation should be tied to explicit objectives:

| Metric            | Target   |
| ----------------- | -------- |
| P95 latency       | < 4 s    |
| Availability      | > 99.9%  |
| Retrieval latency | < 100 ms |
| LLM latency       | < 3 s    |
| Task Success      | > 92%    |
| Faithfulness      | > 95%    |
| Cost per request  | < $0.03  |

These become deployment gates.

---

## Operational Regression Testing

Suppose you change the embedding model. Don't only compare Recall. Compare:

- Latency
- Cost
- Memory
- CPU / GPU
- Failure Rate

Many optimizations improve retrieval while destroying latency.

---

## Production Monitoring

Unlike offline evaluation, operational evaluation never stops:

```text
Production Requests → Telemetry → Metrics → Alerts → Investigation → Root Cause → Fix → Deploy → Repeat
```

Exactly like DevOps.

---

## Correlation Analysis

One of the most valuable enterprise practices — correlating metrics across layers:

- Retriever latency → End-to-end latency
- Prompt size → LLM latency
- Context size → Task Success

You may discover:
- Increasing Top-K from 10 to 20 improves Recall@20 by 2%.
- Prompt size doubles.
- LLM latency increases by 40%.
- Cost increases by 35%.
- Task Success doesn't improve.

This tells you the extra retrieval is not worth the operational cost.

---

## The Evaluation Matrix

Operational evaluation is best viewed as a matrix:

| Dimension      | Representative Metrics                                         |
| -------------- | -------------------------------------------------------------- |
| Performance    | P50/P95/P99 latency, TTFT, tokens/sec                          |
| Efficiency     | Prompt tokens, context utilization, cost/request, cost/success |
| Reliability    | Success rate, timeout rate, retry rate, recovery rate          |
| Scalability    | Throughput, concurrent users, queue depth                      |
| Resource Usage | CPU, GPU, memory, vector index size, cache usage               |
| Observability  | Trace completeness, logging coverage, alert quality            |

---

## A Production Dashboard

If I were designing an enterprise RAG platform, my operational dashboard would contain four sections:

### Application Health

| Metric       | Status |
| ------------ | ------ |
| Availability | 99.95% |
| Success Rate | 98.8%  |
| P95 Latency  | 3.8 s  |
| Active Users | 12,431 |

### Pipeline Breakdown

| Stage           | P95 Latency |
| --------------- | ----------- |
| Embedding       | 28 ms       |
| Retrieval       | 75 ms       |
| Reranker        | 185 ms      |
| Context Builder | 42 ms       |
| LLM             | 2.9 s       |
| Post-processing | 35 ms       |

### Cost

| Metric                | Value  |
| --------------------- | ------ |
| Avg Prompt Tokens     | 2,100  |
| Avg Completion Tokens | 420    |
| Cost/Request          | $0.022 |
| Cost/Successful Task  | $0.024 |

### Reliability

| Metric         | Value |
| -------------- | ----- |
| Timeout Rate   | 0.3%  |
| Retry Rate     | 1.1%  |
| Cache Hit Rate | 41%   |
| Tool Failures  | 0.2%  |

---

## The Missing Layer: Operational Evaluation as a Control System

Everything we've discussed so far measures **what happened**. The next level of maturity is building a system that automatically **reacts** to those measurements.

Think of your RAG application as a feedback control system:

```text
        Production Traffic
               │
               ▼
       Telemetry & Traces
               │
               ▼
      Metrics & Evaluations
               │
     ┌─────────┴─────────┐
     │                    │
     ▼                    ▼
Dashboards          Alert Engine
     │                    │
     └─────────┬──────────┘
               ▼
     Root Cause Analysis
               │
               ▼
    Configuration Changes
    (Top-K, cache, model,
     prompt, etc.)
               │
               ▼
   Continuous Improvement
```

The goal isn't just to **observe** the system — it's to **continuously optimize** it.

---

## The Complete RAG Evaluation Stack

The complete hierarchy we've built over all modules:

```text
                 BUSINESS
                     ▲
     Task Success • User Satisfaction
                     ▲
          End-to-End Evaluation
                     ▲
  Faithfulness • Correctness • Completeness
                     ▲
  Context Sufficiency • Diversity • Consistency
                     ▲
 Recall@K • Precision@K • MRR • nDCG • Hit Rate
                     ▲
Coverage • Freshness • Chunking • Metadata
                     ▲
  Operational Evaluation (cross-cutting)
```

Notice something subtle but important: **Operational evaluation is not just another layer.** It is **orthogonal** to the pipeline.

Latency, cost, reliability, scalability, and observability affect **every stage**:
- Knowledge base indexing latency
- Retrieval latency
- Context construction overhead
- LLM inference latency
- End-to-end task completion time

Instead of thinking of operational evaluation as the "last step," think of it as a **cross-cutting concern** that spans the entire RAG architecture.

---

## What I'd Study Next

We've covered the conceptual architecture of RAG evaluation from the ground up. The next topic most courses never cover:

> **How do companies like OpenAI, Anthropic, Microsoft, or enterprise AI teams actually build an evaluation platform?**

Instead of discussing individual metrics, we'd design a complete system with:

- Evaluation datasets and versioning
- Trace collection
- Judge orchestration
- Metric computation services
- Offline regression pipelines
- CI/CD integration
- Production sampling
- Experiment tracking
- Dashboards
- Alerting
- Human review workflows

In other words, we'd move from **"how to evaluate a RAG system"** to **"how to build the infrastructure that evaluates hundreds of RAG systems continuously."** That is the architecture behind modern GenAI platforms, and it ties together everything we've covered so far.
