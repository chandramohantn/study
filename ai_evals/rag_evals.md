This is probably the most important topic in GenAI evaluation today. Also, it is where I think many engineers make fundamental mistakes.

One misconception I want to eliminate immediately is this:

> **"How do I evaluate my RAG system?"**

This question is actually underspecified.

A RAG system is **not one component**.

It is a distributed system.

Imagine asking:

> "How do I evaluate Kubernetes?"

You would immediately ask:

* Which component?
* API server?
* Scheduler?
* Network?
* etcd?
* Container runtime?

RAG is the same.

---

# The First Principle of RAG Evaluation

Let's start by understanding what a RAG system actually is.

A modern production RAG system typically looks like this:

```text
                         User Query
                              │
                              ▼
                    Query Understanding
                              │
                              ▼
                   Query Rewriting (Optional)
                              │
                              ▼
                 Embedding Generation
                              │
                              ▼
                  Vector / Hybrid Search
                              │
                              ▼
                  Candidate Documents
                              │
                              ▼
                     Reranking (Optional)
                              │
                              ▼
                  Top-K Context Selection
                              │
                              ▼
                 Prompt Construction
                              │
                              ▼
                          LLM
                              │
                              ▼
                 Post Processing
                              │
                              ▼
                       Final Answer
```

Now let me ask you a question.

Suppose the answer is wrong.

Which component failed?

You don't know.

This is the biggest problem in RAG evaluation.

---

# The Biggest Mistake People Make

Many teams only perform this evaluation:

```text
Question

↓

RAG

↓

Answer

↓

LLM Judge

↓

8/10
```

This is almost useless.

Why?

Because the score tells you **what happened**, not **why**.

Imagine the answer is wrong.

Was it because

* embeddings were poor?
* retrieval failed?
* reranker failed?
* prompt removed useful context?
* LLM hallucinated?
* answer formatting failed?

You have no idea.

---

# The Correct Mental Model

A RAG system should be evaluated like a distributed system.

Not

```text
Application

↓

Score
```

Instead

```text
RAG Pipeline

↓

Stage-by-stage Evaluation

↓

Root Cause Analysis

↓

Overall Evaluation
```

This is exactly how Google, OpenAI, Anthropic, and mature enterprise AI teams think about evaluation.

---

# My Evaluation Pyramid

I generally divide RAG evaluation into six layers.

```text
                User Success
                     ▲
             End-to-End Quality
                     ▲
             Generation Quality
                     ▲
           Context Quality
                     ▲
         Retrieval Quality
                     ▲
      Index / Data Quality
```

Every layer influences the one above it.

Let's examine each in detail.

---

# Layer 1 — Data / Knowledge Base Evaluation

Almost nobody starts here.

They should.

Garbage in,

garbage out.

You should ask questions like:

### Is the knowledge base complete?

Example

Suppose users ask

> What is Ericsson's LTE reset procedure?

Does the document even exist?

If not,

no retrieval algorithm can save you.

---

### Is the data current?

Imagine

Documentation

↓

2019

User asks

↓

2026 procedure

Retrieval is perfect.

Answer is wrong.

Because knowledge is stale.

---

### Chunking Quality

This is one of the biggest sources of RAG failures.

Example

Original document

```text
Procedure:

Step 1

Step 2

Step 3

Important Warning

Step 4
```

Poor chunking

```text
Chunk A

Step 1

Step 2

--------

Chunk B

Step 3

Warning

--------

Chunk C

Step 4
```

The warning becomes separated.

Retrieval quality immediately decreases.

---

Things you evaluate here:

* chunk size
* overlap
* semantic coherence
* metadata quality
* duplicate chunks
* missing chunks
* OCR quality
* parsing quality

---

# Layer 2 — Retrieval Evaluation

This is the most studied area.

Notice something.

Retrieval has nothing to do with the LLM.

The LLM hasn't even run yet.

Pipeline

```text
Question

↓

Retriever

↓

Top K Documents
```

We ask

> Did we retrieve the right documents?

---

This layer has several important metrics.

---

## Context Recall

Question:

Were all relevant documents retrieved?

Suppose the ideal documents are

```text
D3

D9

D12
```

Retriever returns

```text
D3

D9

D20
```

Recall

↓

2 of 3

↓

66%

High recall means

You rarely miss useful information.

---

## Context Precision

Question

Among retrieved documents,

how many are actually relevant?

Retriever returns

```text
D3

D9

D15

D21

D33
```

Only

```text
D3

D9
```

are useful.

Precision

↓

2 / 5

↓

40%

Low precision wastes context window.

---

## Hit Rate

Simple metric.

Did at least one useful document appear?

Yes

↓

1

No

↓

0

Surprisingly useful.

---

## MRR

Mean Reciprocal Rank

Suppose

Relevant document appears

Rank 1

↓

Score 1

Rank 2

↓

0.5

Rank 10

↓

0.1

This rewards systems that retrieve useful information early.

---

## nDCG

Measures

* ranking quality
* graded relevance

Useful when documents have

Highly relevant

Relevant

Slightly relevant

rather than binary labels.

---

# Layer 3 — Context Evaluation

This is different from retrieval.

People often confuse them.

Retrieval asks

Did we retrieve useful chunks?

Context evaluation asks

Did we give the LLM sufficient information?

Suppose retrieval finds

10 documents.

Prompt builder chooses

Top 3.

Were those three enough?

Different question.

---

Things to evaluate

Context completeness

Context redundancy

Context ordering

Context compression

Context diversity

Context conflicts

---

Example

Suppose

Top-3 chunks all say

same thing.

Great retrieval.

Terrible context.

Because diversity is poor.

---

# Layer 4 — Generation Evaluation

Only now does the LLM begin.

Input

↓

Question

*

Retrieved Context

↓

LLM

↓

Answer

Now we evaluate generation.

---

The most famous metrics.

---

## Faithfulness

This is arguably the most important RAG metric.

Question

Did the answer stay faithful to retrieved documents?

Context says

```text
Warranty = 30 days
```

LLM answers

```text
Warranty = 90 days
```

Hallucination.

Faithfulness

↓

Low.

Notice

Even if

90 days

is true elsewhere,

RAG evaluation says

Wrong.

Because RAG must answer using provided evidence.

---

## Groundedness

Very similar.

Every important claim should be supported by retrieved context.

Think of

Groundedness

↓

Citation coverage.

---

## Answer Relevance

Did the answer actually answer the question?

Question

"What is LTE?"

Answer

"Ericsson has offices worldwide."

Grounded?

Maybe.

Relevant?

No.

---

## Correctness

Compare

Generated Answer

↓

Reference Answer

Usually

LLM Judge

or

Human.

---

## Completeness

Suppose question

How do I reset Node B?

Correct answer requires

Step 1

Step 2

Step 3

LLM gives

Step 1

Only.

Correct.

Incomplete.

---

# Layer 5 — End-to-End Evaluation

Now we ignore internal stages.

We ask

User

↓

Question

↓

RAG

↓

Answer

↓

Task Completed?

This is closest to user experience.

Metrics include

Task success

Helpfulness

User satisfaction

Resolution rate

Citation usefulness

Latency

---

# Layer 6 — Operational Evaluation

Finally,

system metrics.

Latency

Embedding latency

Retriever latency

Reranker latency

LLM latency

Total latency

Token usage

Cost

GPU usage

Failure rate

Timeouts

Retries

Cache hit rate

---

# How Should Evaluation Actually Be Performed?

This is where I disagree with many tutorials online.

They often advocate

```text
Dataset

↓

Run RAG

↓

LLM Judge

↓

Done
```

I think this is insufficient for production systems.

Instead, every evaluation case should produce a **trace**.

Something like:

```yaml
evaluation_case:
  id: 183

query:
  "How do I reset LTE Node?"

query_embedding:
  vector_id: ...

retrieved_documents:

- doc_18
- doc_43
- doc_98

reranked_documents:

- doc_43
- doc_18

final_context:

- chunk43
- chunk18

prompt:
  ...

llm_output:
  ...

citations:
  ...

scores:

  retrieval:

      recall: 1.0
      precision: 0.67
      hit_rate: 1

  context:

      completeness: 0.92
      redundancy: 0.18

  generation:

      faithfulness: 0.97
      correctness: 0.89
      completeness: 0.84
      groundedness: 0.95

  operational:

      latency: 2.3s
      tokens: 1842

overall:

      pass
```

This is the level of detail you want.

Notice

You now know

exactly

which stage failed.

---

# The Evaluation Matrix

I like to think of RAG evaluation as a matrix.

| Stage                | Questions                                | Metrics                                                          |
| -------------------- | ---------------------------------------- | ---------------------------------------------------------------- |
| Data                 | Is the knowledge base good?              | Coverage, freshness, chunk quality                               |
| Retrieval            | Did we find the right chunks?            | Recall@K, Precision@K, Hit Rate, MRR, nDCG                       |
| Context Construction | Did we build a good context?             | Completeness, redundancy, ordering, diversity                    |
| Generation           | Did the model use the context correctly? | Faithfulness, groundedness, correctness, completeness, relevance |
| End-to-End           | Did the user achieve their goal?         | Task success, helpfulness, satisfaction                          |
| Operations           | Can the system run reliably?             | Latency, cost, throughput, failures                              |

This layered view is far more actionable than a single overall score.

---

# How Frontier Teams Actually Build RAG Evals

One of the most important observations is that mature organizations **don't rely on one evaluation**. They typically maintain **three complementary evaluation loops**:

### 1. Component-level evaluations (fast, diagnostic)

These run frequently and isolate failures.

Examples:

* Retrieval recall drops after changing the embedding model.
* Faithfulness drops after modifying the system prompt.
* Latency increases after introducing a reranker.

These are excellent for debugging because they localize the problem.

---

### 2. End-to-end regression evaluations (release gate)

Before every release:

```text
Candidate Version
        │
        ▼
Run 5,000 Evaluation Cases
        │
        ▼
Compare with Production Baseline
        │
        ▼
Did Any Metric Regress?
        │
        ▼
Ship or Block
```

This is analogous to a software regression suite.

---

### 3. Production evaluations (continuous monitoring)

After deployment, evaluation doesn't stop.

Production traffic is sampled to answer questions like:

* Are users asking new kinds of questions?
* Are retrieval patterns changing?
* Are there new hallucination modes?
* Are there documents that should be added to the knowledge base?

Failures from production become new evaluation cases, creating a continuous improvement loop.

---

## My Recommendation

If we continue this course, I would **not** jump straight into Ragas metrics or DeepEval APIs. Those are implementations.

Instead, I'd spend the next modules on the **hard problems** behind RAG evaluation:

1. **How do you build a high-quality RAG evaluation dataset?** (This is arguably the hardest part.)
2. **How do you compute metrics like faithfulness or context precision when you don't have ground truth?**
3. **How does LLM-as-a-Judge actually work for RAG, and how do you prevent judge bias?**
4. **How do frameworks like Ragas, DeepEval, and LangSmith implement these ideas internally?**
5. **How would you architect an enterprise-grade evaluation platform that continuously evaluates every RAG application?**

Those topics move from *using* RAG evaluation frameworks to *understanding how to build one*, which I think aligns well with the way you prefer to learn complex systems.
