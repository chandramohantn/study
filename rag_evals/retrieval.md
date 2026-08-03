**Retrieval Evaluation** is the heart of RAG evaluation.

Here's a statement that may sound surprising:

> **Most RAG failures are retrieval failures disguised as LLM failures.**

People often say:

> "GPT hallucinated."

When you inspect the trace, what actually happened is:

```text
User Question
        ↓
Retriever missed the correct document
        ↓
LLM received incomplete context
        ↓
LLM made the best possible answer
```

The LLM never had a chance.

This is why, in mature RAG systems, **retrieval is treated as its own ML system**, with its own datasets, metrics, experiments, A/B tests, and regression suites.

Today, we'll study retrieval exactly as an Information Retrieval (IR) engineer would.

---

# Module 1: Understanding Retrieval Evaluation

Before we discuss metrics, let's answer a more fundamental question.

> **What is a retriever actually trying to optimize?**

Many people answer:

> "Find similar documents."

That is not quite correct.

The real objective is:

> **Retrieve the smallest set of documents that contains enough information for the downstream model to successfully complete the user's task.**

Notice how different that is.

Similarity is only a proxy.

---

# Retrieval Is Not Search

This is one of the biggest conceptual mistakes.

People think:

```text
Retriever = Search Engine
```

Not really.

A web search engine optimizes for **human reading**.

```text
Query
    ↓
Ranked Results
    ↓
Human clicks
```

A RAG retriever optimizes for **LLM reasoning**.

```text
Query
    ↓
Relevant Context
    ↓
LLM
    ↓
Correct Answer
```

The consumer is no longer a human.

It is another AI.

That changes the optimization objective.

---

# The Retrieval Pipeline

Let's zoom into the retrieval stage.

```text
                    User Query
                         │
                         ▼
                Query Processing
                         │
                         ▼
              Query Embedding
                         │
                         ▼
              Candidate Retrieval
                         │
                         ▼
                 Top-100 Chunks
                         │
                         ▼
                 Reranker (optional)
                         │
                         ▼
                  Top-10 Chunks
                         │
                         ▼
               Context Builder
```

Every box can fail.

Therefore every box can be evaluated.

---

# The Retrieval Evaluation Principle

Every evaluation ultimately asks one question:

> **If the answer exists in my knowledge base, did the retriever find it?**

Everything else is secondary.

---

# Retrieval Is a Ranking Problem

Many newcomers think retrieval is about finding documents.

Actually, retrieval is about **ranking documents**.

Suppose your corpus contains one million chunks.

The retriever assigns each one a score.

```text
Chunk A    0.98

Chunk B    0.95

Chunk C    0.92

Chunk D    0.90

...
```

The question becomes:

Did the most relevant chunks receive the highest scores?

That is why almost every retrieval metric comes from decades of Information Retrieval research.

---

# Ground Truth

Before discussing metrics, we need to solve one problem.

How do we know what should have been retrieved?

Without this,

Recall

cannot exist.

Precision

cannot exist.

MRR

cannot exist.

Everything depends on ground truth.

---

# Building Ground Truth

Suppose our corpus contains

```text
Doc1

Doc2

Doc3

Doc4

Doc5
```

User asks:

> "How do I configure OAuth?"

Experts determine

Relevant:

```text
Doc2

Doc5
```

Irrelevant:

```text
Doc1

Doc3

Doc4
```

Now retrieval can be evaluated.

---

# Binary vs Graded Relevance

This distinction is extremely important.

Most tutorials ignore it.

### Binary Relevance

```text
Relevant

Not Relevant
```

Very simple.

Useful for

Recall

Precision

Hit Rate

---

### Graded Relevance

Reality is more nuanced.

Example

```text
Chunk A

Perfect Answer

Score = 3

Chunk B

Useful Background

Score = 2

Chunk C

Somewhat Related

Score = 1

Chunk D

Irrelevant

Score = 0
```

Now ranking quality becomes measurable.

This is where metrics like **nDCG** become valuable.

---

# Retrieval Metrics

Now let's study them one by one.

Notice that every metric measures a different property.

There is no "best metric."

---

# Metric 1 — Recall@K

This is the most important retrieval metric.

Question:

> **Did we retrieve everything we needed?**

Suppose

Ground Truth

```text
Relevant Documents

D2

D5

D9
```

Retriever returns

Top-5

```text
D2

D4

D5

D8

D11
```

Relevant retrieved:

```text
D2

D5
```

Recall@5

```text
2 / 3

=

66%
```

---

## Interpretation

High recall means

You rarely miss useful evidence.

Low recall means

The answer may be impossible,

even for GPT-5.

---

## When Recall Matters

Legal

Medical

Scientific

Compliance

Enterprise Search

Missing one critical document can invalidate the answer.

---

# Metric 2 — Precision@K

Question

> **How much irrelevant information did we retrieve?**

Suppose

Top-5

```text
D2

D4

D5

D8

D11
```

Relevant

```text
D2

D5
```

Precision@5

```text
2 / 5

=

40%
```

---

High precision means

Almost everything retrieved is useful.

Low precision means

You waste context window.

---

# Precision vs Recall

Imagine

Retriever A

```text
Returns

100 Documents
```

Recall

Very High

Precision

Terrible

---

Retriever B

Returns

1 Document

Precision

Excellent

Recall

Terrible

Neither is ideal.

Production systems balance both.

---

# Metric 3 — Hit Rate

This is deceptively simple.

Question:

> **Did at least one relevant document appear?**

Suppose

Ground Truth

```text
D7
```

Top-5

```text
D1

D3

D7

D10

D20
```

Hit

Yes

Score

1

---

If

```text
D7
```

never appears

Score

0

---

Why is this useful?

Because many questions only require

one good chunk.

---

# Metric 4 — Mean Reciprocal Rank (MRR)

This measures

How early did we retrieve the first useful document?

Suppose

Relevant document

appears

Rank 1

Score

1

Rank 2

Score

1/2

Rank 3

Score

1/3

Rank 10

Score

1/10

Average this over all evaluation cases to get **MRR**.

---

## Why MRR Exists

Imagine two retrievers.

Retriever A

```text
Relevant chunk

Rank 1
```

Retriever B

```text
Relevant chunk

Rank 50
```

Both technically retrieved it.

But Retriever A is much more useful because downstream stages usually only consume the top few results.

MRR rewards early retrieval.

---

# Metric 5 — nDCG

This is often the hardest metric to understand.

Let's build intuition instead of memorizing the formula.

Imagine three retrieved documents.

```text
Rank 1

Background

Score 1

Rank 2

Perfect Answer

Score 3

Rank 3

Minor Detail

Score 1
```

Now compare another ranking.

```text
Rank 1

Perfect Answer

Score 3

Rank 2

Background

Score 1

Rank 3

Minor Detail

Score 1
```

Both retrieved the same documents.

Recall

100%

Precision

100%

Yet the second ranking is clearly better.

Why?

Because the most useful document appears first.

nDCG rewards this.

It combines:

* graded relevance
* ranking quality
* emphasis on earlier positions

If you have rerankers, nDCG is one of the best metrics to track.

---

# Why @K Matters

Notice that all these metrics often have `@K`.

Why?

Because LLMs don't read one million documents.

They usually receive

Top-5

Top-10

Top-20

Therefore

Recall@5

Recall@10

Recall@20

are different metrics.

---

Example

Relevant documents

```text
D2

D9

D12
```

Top-3

retrieves

```text
D2
```

Recall@3

33%

---

Top-10

retrieves

```text
D2

D9

D12
```

Recall@10

100%

---

This helps you answer questions like:

> "Should I increase K from 5 to 10?"

Without evaluation, you're guessing.

---

# Retrieval Trace

Now let's discuss how an evaluation case should actually look.

Suppose a query arrives.

I would capture something like this:

```yaml
query: >
  How do I configure OAuth?

ground_truth:

  relevant_chunks:

    - chunk_28
    - chunk_91

retriever_output:

  rank1: chunk_91
  rank2: chunk_10
  rank3: chunk_28
  rank4: chunk_44
  rank5: chunk_77

metrics:

  recall@5: 1.0

  precision@5: 0.40

  hit_rate: 1

  reciprocal_rank: 1.0

  ndcg@5: 0.96
```

Notice something important.

This evaluation is **completely independent of the LLM**.

That's intentional.

---

# Debugging Retrieval Failures

This is where mature teams spend a lot of time.

Suppose Recall@10 drops from 95% to 78%.

The question is not:

> "Why is the answer wrong?"

Instead, investigate the retrieval pipeline.

Possible causes include:

### Embedding model regression

The new embedding model no longer places semantically similar chunks close together.

---

### Chunking regression

The answer was split across multiple chunks.

No individual chunk is sufficient.

---

### Metadata filtering

A security filter accidentally excluded relevant documents.

---

### Hybrid search weighting

Dense retrieval and keyword search were combined poorly.

The weighting favored keyword matches too strongly.

---

### Index corruption

Some vectors were never indexed.

---

### Query rewriting

The rewritten query changed the user's intent.

---

# Retrieval Evaluation Dashboard

A production retrieval dashboard might include:

| Metric                    | Purpose                                                        |
| ------------------------- | -------------------------------------------------------------- |
| Recall@5                  | Are we finding enough evidence?                                |
| Recall@10                 | Does increasing context help?                                  |
| Precision@5               | Are we wasting context?                                        |
| Hit Rate                  | Is at least one useful chunk retrieved?                        |
| MRR                       | How early is the first useful chunk?                           |
| nDCG@10                   | Are the most relevant chunks ranked highest?                   |
| Average retrieval latency | Can retrieval meet latency targets?                            |
| Candidate pool size       | Is the retriever returning enough candidates before reranking? |

Notice that none of these involve answer quality. They isolate retrieval performance.

---

# The Most Important Insight

I want to leave you with what I think is the defining principle of retrieval evaluation:

> **A retriever should not be evaluated by whether the final answer is correct. It should be evaluated by whether it supplied sufficient evidence for the downstream model to produce the correct answer.**

This distinction matters because retrieval and generation have different responsibilities.

* **Retriever's responsibility:** Find the right evidence.
* **Generator's responsibility:** Use that evidence correctly.

If you conflate these two, debugging becomes extremely difficult.

---

# Before We Move to Context Evaluation

There is one advanced topic that deserves attention before we discuss context quality.

Everything we've covered assumes there is a fixed notion of "relevant documents."

In reality, relevance itself is multi-dimensional:

* A document can be semantically similar but not answer the question.
* A document can contain the answer but lack necessary surrounding context.
* Multiple individually irrelevant chunks may become highly relevant when considered together.
* A reranker may intentionally demote a relevant chunk in favor of a more self-contained one.

Understanding **what "relevance" actually means in a RAG system** is the key to designing high-quality retrieval datasets and choosing the right metrics. That topic naturally bridges retrieval evaluation and the next layer of the pyramid: **Context Evaluation**, where we ask not just *"Did we retrieve the right chunks?"* but *"Did we construct the right context for the LLM?"*
