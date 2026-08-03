**Data / Knowledge Base Evaluation** is the most neglected part of RAG evaluation.

Most teams start here:

```text
Question
    ↓
Retriever
```

They completely ignore what comes before retrieval.

That's a mistake.

Imagine building a search engine.

If the documents are corrupted, incomplete, duplicated, outdated, or poorly chunked, **no retriever, reranker, or LLM can consistently recover from that**.

In mature RAG systems, the knowledge base itself is treated as a **data product** with its own quality gates, observability, and evaluation pipeline.

---

# The RAG Evaluation Pyramid Revisited

Let's revisit the pyramid.

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
       Data / Knowledge Base Quality
```

Everything above depends on the foundation.

If your data layer is weak, every higher-level metric becomes noisy and misleading.

---

# First Principle

A knowledge base is not simply a collection of documents.

It is a pipeline.

```text
Raw Sources
      │
      ▼
Document Extraction
      │
      ▼
Cleaning
      │
      ▼
Chunking
      │
      ▼
Metadata Enrichment
      │
      ▼
Embedding
      │
      ▼
Indexing
      │
      ▼
Knowledge Base
```

Notice something.

Every arrow can introduce errors.

Therefore, we evaluate **each transformation**, not just the final index.

---

# What Are We Really Evaluating?

The goal is not

> "Is my PDF indexed?"

The real question is

> **"If the correct answer exists somewhere in my enterprise, what is the probability that my RAG system can eventually retrieve it?"**

That probability is largely determined before retrieval even starts.

---

# A Better Mental Model

Instead of thinking

```text
Knowledge Base
```

think

```text
Knowledge Supply Chain
```

Like manufacturing:

```text
Raw Material
      ↓
Processing
      ↓
Assembly
      ↓
Packaging
      ↓
Distribution
```

Quality must be inspected throughout the supply chain.

---

# The Six Dimensions of Knowledge Base Quality

I divide knowledge base evaluation into six major areas.

```text
Knowledge Base

├── Coverage
├── Freshness
├── Document Quality
├── Chunk Quality
├── Metadata Quality
└── Index Quality
```

Each has different evaluation techniques.

---

# 1. Coverage Evaluation

This is the first question.

> **Does the knowledge base actually contain the information users need?**

Notice this is different from retrieval.

Suppose your users ask

> "How do I reset Ericsson LTE Node B?"

The documentation simply doesn't exist.

No embedding model can solve this.

---

## Coverage Metrics

Coverage is essentially

```text
User Information Needs

        ∩

Knowledge Base
```

The larger the overlap,

the better.

---

### Domain Coverage

Imagine an HR assistant.

```text
HR Knowledge

├── Payroll
├── Leave
├── Benefits
├── Recruitment
├── Compliance
├── Performance Reviews
├── Promotions
├── Travel
```

You discover

Travel

↓

0 documents.

Coverage problem.

---

### Intent Coverage

Now classify user intents.

```text
Knowledge Lookup

Procedure

Comparison

Troubleshooting

Policy

Configuration

FAQ
```

Measure

```text
Coverage(intent)

=

Supported intents

/

Observed intents
```

Suppose

Production logs show

```text
20%

of questions are troubleshooting.
```

Knowledge base

contains

```text
3%

troubleshooting documents.
```

Coverage issue.

---

### Entity Coverage

Suppose your semiconductor documentation mentions

```text
Product A

Product B

Product C
```

Users ask about

```text
Product D
```

Coverage gap.

A useful metric:

```text
Covered Entities

/

Expected Entities
```

---

# How Do We Measure Coverage?

There are several approaches.

---

## Method 1 — Manual Audit

Domain experts create

```text
Knowledge Checklist

↓

Verify Documents Exist
```

Simple.

Expensive.

---

## Method 2 — Production Query Mining

Collect

100,000 user queries.

Cluster them.

```text
Queries

↓

Embeddings

↓

Semantic Clusters

↓

Compare Against Corpus
```

Clusters with no supporting documents indicate coverage gaps.

This is extremely common in enterprise AI.

---

## Method 3 — Knowledge Graph Comparison

Suppose you maintain

```text
Products

↓

Components

↓

Features
```

Automatically verify

whether every node has documentation.

---

# 2. Freshness Evaluation

Now let's assume

coverage is perfect.

The next question:

> **Is the information still correct?**

Example:

```text
Vacation Policy

2023

↓

20 days
```

Policy changes.

2026

↓

25 days.

Knowledge base

still

contains

20.

Retrieval is perfect.

Generation is faithful.

Final answer is wrong.

---

Freshness metrics.

---

### Document Age Distribution

Plot

```text
Age

0-3 months

3-6 months

6-12 months

1-2 years

>2 years
```

If

80%

of documents

are

5 years old,

that is a warning.

---

### Update Lag

Suppose

Source System

updated

today.

Knowledge base

updated

10 days later.

Metric

```text
Update Lag

=

Knowledge Base Timestamp

-

Source Timestamp
```

---

### Staleness Score

Example

```text
Document

Last Updated

Expected Update Frequency
```

If

Safety Manual

should update

monthly

but

last updated

2 years ago

↓

High staleness.

---

# 3. Document Quality

Now we evaluate

individual documents.

Questions include

Is OCR correct?

Missing pages?

Broken formatting?

Unreadable tables?

Corrupted images?

Duplicate pages?

---

Example

Original

```text
Maximum voltage = 220V
```

OCR

```text
Maximum voltage = 22OV
```

(letter O instead of zero)

Retrieval succeeds.

Generation fails.

Root cause:

OCR.

---

Useful metrics.

OCR confidence

Extraction success rate

Broken document rate

Parsing failures

Missing figures

Unreadable tables

---

# 4. Chunk Quality

This deserves an entire module by itself.

I consider chunking

one of the most important parts of RAG.

Why?

Because retrievers retrieve chunks,

not documents.

---

Imagine

Original document

```text
Reset Procedure

Step 1

Step 2

Step 3

Important Warning

Step 4
```

Chunked badly

```text
Chunk 1

Step 1

Step 2

---------

Chunk 2

Step 3

Warning

---------

Chunk 3

Step 4
```

Now

Warning

may never appear

with

Step 4.

The semantic unit has been broken.

---

# Chunk Quality Dimensions

I evaluate chunking using several dimensions.

---

## Semantic Coherence

Question:

Does the chunk represent

one coherent concept?

Good

```text
Entire Procedure
```

Bad

```text
Half Procedure

+

Random Table

+

Footer
```

---

## Boundary Integrity

Did chunking split

* paragraphs
* code blocks
* tables
* equations
* procedures

across chunk boundaries?

---

## Information Completeness

Does a chunk

contain enough information

to answer questions

without neighboring chunks?

---

## Redundancy

Overlap

is necessary.

Too much overlap

creates duplicates.

Measure

Duplicate content %

Average overlap %

Embedding similarity

---

## Chunk Size Distribution

Plot histogram.

```text
Tiny Chunks

Medium

Large

Very Large
```

Large variance

usually indicates parsing problems.

---

# How Would I Evaluate Chunk Quality?

I would randomly sample

1000 chunks.

For each chunk,

compute

```text
Semantic Density

Boundary Quality

Readability

Token Count

Overlap

Parent Document

Section Completeness
```

Then

human review

a statistically representative sample.

---

# 5. Metadata Quality

Metadata is the hidden backbone of enterprise RAG.

Imagine

```text
Document

↓

No department

No owner

No version

No language
```

Filtering becomes impossible.

---

Metadata completeness metrics.

Required fields present

Language detected

Security label

Access control

Document owner

Version

Publication date

Source system

---

Metadata consistency.

Suppose

same document

has

```text
Language

English
```

and

```text
Locale

German
```

Consistency issue.

---

# 6. Index Quality

Finally,

after chunking

comes indexing.

Questions include

Were all chunks embedded?

Were embeddings generated successfully?

Any duplicate vectors?

Any orphan vectors?

Any indexing failures?

---

Useful metrics.

Embedding success rate

Index completeness

Duplicate vectors

Embedding dimensionality consistency

Index corruption rate

---

# Knowledge Base Evaluation Pipeline

Putting everything together,

my pipeline would look like this:

```text
Source Systems
      │
      ▼
Coverage Evaluation
      │
      ▼
Freshness Evaluation
      │
      ▼
Document Extraction Evaluation
      │
      ▼
Chunk Quality Evaluation
      │
      ▼
Metadata Evaluation
      │
      ▼
Embedding Evaluation
      │
      ▼
Index Evaluation
      │
      ▼
Knowledge Base Health Report
```

Notice that **retrieval hasn't started yet**.

---

# A Knowledge Base Health Dashboard

If I were building an enterprise platform, I'd want a dashboard something like this:

| Category           | Example Metrics                                                              |
| ------------------ | ---------------------------------------------------------------------------- |
| Coverage           | Domain coverage %, entity coverage %, intent coverage %                      |
| Freshness          | Average age, update lag, stale document %                                    |
| Documents          | OCR success %, parsing failures, corrupt documents                           |
| Chunking           | Average chunk size, overlap %, semantic coherence score, boundary violations |
| Metadata           | Metadata completeness %, missing required fields, inconsistent labels        |
| Embeddings & Index | Embedding success %, duplicate vectors, orphan chunks, index completeness    |

This dashboard should be monitored continuously, just like infrastructure dashboards.

---

# The Biggest Insight

I want to leave you with one principle that many RAG practitioners overlook.

A knowledge base should not be viewed as **static data**.

It should be treated like **source code**.

That means:

* It has versions.
* It has quality gates.
* It has automated validation.
* It has regression tests.
* It has observability.
* It has ownership.

When organizations reach that level of maturity, RAG quality improves dramatically—not because they changed the LLM, but because they improved the foundation on which the entire system is built.

---

## Where I Think We Should Go Next

The next layer in the pyramid is **Retrieval Evaluation**, and this is where many commonly cited metrics—Recall@K, Precision@K, MRR, nDCG, Hit Rate, Context Precision, and Context Recall—come into play.

However, rather than simply defining these metrics, I suggest we study retrieval like we studied PyTorch: by treating it as a **retrieval system architecture**. We'll answer questions such as:

* What exactly is the retriever optimizing?
* Why do traditional IR metrics still matter in vector search?
* How do you create ground truth for retrieval?
* How do you evaluate hybrid retrieval and rerankers?
* How do enterprise teams debug retrieval failures?

Once those foundations are clear, metrics like Recall@K and nDCG become obvious consequences rather than formulas to memorize.
