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


Perfect. This is the point where we stop talking about *metrics* and start talking about *measurement science*.

Most blogs say:

> "Compute Faithfulness."

or

> "Compute Context Precision."

Very few explain **where these numbers actually come from.**

As an engineer, that should bother you.

If I tell you:

```
Faithfulness = 0.87
```

You should immediately ask:

> **How did you compute 0.87?**

Let's answer that question.

---

# Module 2: Designing a RAG Evaluation Dataset

I will make a strong statement.

> **A RAG evaluation system is only as good as its evaluation dataset.**

The LLM judge.

The metrics.

The dashboards.

The fancy UI.

All of them are downstream.

The evaluation dataset is the foundation.

---

# First Principle

Let's forget about RAG.

Suppose you're testing Gmail.

What do you need?

Test cases.

Example:

```
Compose email

↓

Send email

↓

Verify recipient received it
```

Software engineers have been doing this for decades.

Now replace Gmail with a RAG system.

Same idea.

We need evaluation cases.

---

# What Is an Evaluation Case?

Most beginners think an evaluation case is

```yaml
question:
answer:
```

That is far too simplistic.

A production evaluation case is much richer.

Conceptually:

```text
                   Evaluation Case

          ┌────────────────────────────┐

          │ User Query                 │

          │ User Intent                │

          │ Expected Evidence          │

          │ Reference Answer           │

          │ Evaluation Strategy        │

          │ Metadata                   │

          └────────────────────────────┘
```

Every field has a purpose.

---

# Let's Build One

Suppose your RAG system answers HR questions.

Question:

```
How many vacation days do new employees receive?
```

A mature evaluation case might look like

```yaml
id: HR-001

query:
  How many vacation days do new employees receive?

intent:
  Vacation policy

expected_documents:

- employee_handbook.pdf
- hr_policy_v4.pdf

expected_chunks:

- handbook_chunk_18
- policy_chunk_4

reference_answer:

  New employees receive 20 vacation
  days per year.

evaluation_dimensions:

- retrieval
- faithfulness
- completeness

difficulty:

  easy

language:

  english

customer_segment:

  internal_hr
```

Notice something.

The answer is only one field.

---

# Why So Much Metadata?

Imagine one evaluation fails.

Question:

```
How do contractors request VPN access?
```

The answer is wrong.

Now you ask:

Why?

Metadata helps answer that.

Maybe

```
Department = IT
```

or

```
Language = German
```

or

```
Document Version = 2026
```

Metadata allows slicing evaluation results later.

---

# What Should Be Stored?

I generally divide an evaluation case into six sections.

```
Evaluation Case

↓

Input

↓

Ground Truth

↓

Expected Retrieval

↓

Expected Behavior

↓

Metadata

↓

Scoring Strategy
```

Let's study each.

---

# Section 1 — Input

This is obvious.

```
User Query
```

But...

Should you only have one query?

No.

Suppose users ask

```
Vacation policy
```

Some users ask

```
PTO
```

Others ask

```
Leave balance
```

Others ask

```
Paid holidays
```

Same intent.

Different wording.

A robust dataset captures this linguistic variation.

---

# Section 2 — Ground Truth

This is where many people struggle.

Should we always store

```
Reference Answer?
```

Sometimes yes.

Sometimes no.

There are three possibilities.

---

## Option A

Reference Answer

Example

```
Warranty = 30 days
```

Easy.

---

## Option B

Reference Documents

Instead of

correct answer

store

```
Correct Evidence
```

This is common in RAG.

Because the answer can be generated in many ways.

---

## Option C

Expected Behavior

Sometimes

there is no correct answer.

Instead

```
Should refuse.

Should ask follow-up question.

Should say insufficient information.

Should escalate.
```

Notice

Behavior

is the ground truth.

Not text.

---

# Section 3 — Expected Retrieval

This is unique to RAG.

Imagine

Question

↓

Retriever

↓

Top K

We need to know

What SHOULD have been retrieved?

Example

```
Expected Documents

Policy_v4.pdf

Vacation.pdf

Benefits.pdf
```

Now retrieval becomes measurable.

Without this,

Recall

cannot be computed.

---

# But Wait...

How do we know

Expected Documents?

Excellent question.

This is actually one of the hardest problems in RAG evaluation.

There are several approaches.

---

# Method 1 — Human Annotation

Experts manually identify

correct documents.

```
Engineer

↓

Reads Query

↓

Reads Corpus

↓

Marks Relevant Chunks
```

Highest quality.

Most expensive.

---

# Method 2 — Existing Citations

Suppose documentation already references

```
Section 4.2
```

Automatically

ground truth exists.

---

# Method 3 — LLM Assisted

An LLM proposes

candidate chunks.

Human verifies.

This greatly reduces annotation effort.

---

# Method 4 — Production Logs

Suppose users consistently click

Document 12

after asking

```
VPN setup
```

Production interactions become weak supervision signals.

---

# Section 4 — Expected Behavior

Suppose the query is

```
How do I change payroll information?
```

Maybe

Correct behavior is

```
Answer directly.
```

Another query

```
My password doesn't work.
```

Expected behavior

```
Route to IT.
```

Another query

```
How do I hack payroll?
```

Expected behavior

```
Refuse.
```

Behavior

is sometimes more important than answer correctness.

---

# Section 5 — Metadata

This becomes surprisingly useful.

Possible metadata.

```
Difficulty

Department

Language

User Type

Topic

Intent

Date

Document Version

Retriever Version

Prompt Version

Embedding Model
```

Later

you discover

```
German questions

↓

20% worse.
```

Without metadata

you never find this.

---

# Section 6 — Evaluation Strategy

This is rarely discussed.

Different cases require different evaluators.

Example

Case A

```
Exact Match
```

Case B

```
LLM Judge
```

Case C

```
SQL Execution
```

Case D

```
Faithfulness Only
```

The dataset itself specifies

how it should be evaluated.

---

# Dataset Taxonomy

One thing that distinguishes mature evaluation teams is that they don't treat all queries equally.

Instead, they classify them.

For a technical documentation assistant, you might have:

```text
Knowledge Lookup
        │
Procedure Questions
        │
Configuration Questions
        │
Troubleshooting
        │
Comparison Questions
        │
Summarization
        │
Multi-document Reasoning
        │
Out-of-scope Questions
        │
Adversarial Questions
```

Each category stresses a different part of the pipeline.

---

# Difficulty Levels

A mature dataset also contains different difficulty levels.

```
Easy

↓

Single document.

↓

Direct answer.

---------------------

Medium

↓

Multiple chunks.

↓

Some reasoning.

---------------------

Hard

↓

Multiple documents.

↓

Conflict resolution.

↓

Long reasoning.
```

If all your evaluation cases are easy, your system may look excellent while failing on realistic enterprise queries.

---

# Building the Dataset

Most teams don't start with 10,000 examples.

They grow organically.

```
Initial Seed Set
        │
        ▼
Human-written Cases
        │
        ▼
Deploy
        │
        ▼
Production Failures
        │
        ▼
Convert Failures into Eval Cases
        │
        ▼
Regression Suite Grows
```

This is exactly the same philosophy used in software testing.

Every production bug becomes a future regression test.

---

# Gold, Silver, and Bronze Datasets

Frontier teams often think in terms of data quality tiers.

### Gold

* Human curated.
* Human verified.
* High confidence.
* Used for release decisions.

Typically only hundreds of cases.

---

### Silver

* LLM generated.
* Human reviewed.
* Mostly correct.

Often thousands of cases.

---

### Bronze

* Automatically mined from production.
* Weak labels.
* Large scale.

Used for monitoring rather than release gating.

---

# The Dataset Is a Living Artifact

A common mistake is to think:

> "We built an evaluation dataset."

Finished.

No.

A mature evaluation dataset behaves like source code.

```
Version 1
      │
Production failures
      │
Version 2
      │
New product features
      │
Version 3
      │
New document corpus
      │
Version 4
```

It has versioning, reviews, ownership, and change history.

---

# An Enterprise RAG Evaluation Repository

If I were building an evaluation platform, I would not store just CSV files.

I'd organize it more like this:

```text
rag-evals/
│
├── datasets/
│   ├── gold/
│   ├── silver/
│   ├── bronze/
│   └── archived/
│
├── cases/
│   ├── hr/
│   ├── finance/
│   ├── engineering/
│   ├── legal/
│   └── support/
│
├── rubrics/
│   ├── faithfulness.yaml
│   ├── completeness.yaml
│   └── correctness.yaml
│
├── judges/
│   ├── llm_judge.py
│   ├── retrieval_judge.py
│   └── execution_judge.py
│
└── reports/
```

Notice that the **dataset** is treated as a first-class software artifact, not just a file.

---

# The Biggest Insight of This Module

I want to leave you with one important realization.

When most engineers think about RAG evaluation, they think:

```
Question

↓

Answer

↓

Score
```

But an evaluation engineer thinks:

```
Question

↓

Expected Retrieval

↓

Expected Context

↓

Expected Behavior

↓

Expected Answer

↓

Evaluation Strategy

↓

Metadata

↓

Score
```

The evaluation case becomes a **specification** of how the system should behave, not merely a question with an answer.

---

## Where We Should Go Next

We have now built the foundation: the evaluation dataset.

The next logical question is the one every engineer eventually asks:

> **"I understand what faithfulness means conceptually, but how do frameworks like Ragas or DeepEval actually compute it?"**

That is where we'll dive into **LLM-as-a-Judge**, rubrics, prompt design for judges, pairwise evaluation, structured scoring, calibration, agreement with human raters, and how metrics like **Faithfulness**, **Answer Relevance**, **Context Precision**, and **Context Recall** are implemented internally. Understanding that machinery will demystify almost every modern RAG evaluation framework.

