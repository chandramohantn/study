These are exactly the right questions to ask once you move beyond "RAG works" into "RAG works reliably."

One misconception I often see is that people think **retrieval** is the difficult part of RAG. In reality, for production systems, **ranking is where much of the quality comes from.**

Google Search, Bing, Amazon Search, LinkedIn Search, recommendation systems—all of them have invested decades in ranking. Modern RAG systems are no different.

Let's build a complete mental model.

---

# Where reranking fits in RAG

A typical RAG pipeline looks like this:

```
User Query
      │
      ▼
Query Processing
      │
      ▼
Retriever
(Dense / Sparse / Hybrid)
      │
      ▼
Top 100 documents
      │
      ▼
Reranker
      │
      ▼
Top 10 documents
      │
      ▼
Context Construction
      │
      ▼
LLM
```

Notice something important:

The retriever's goal is

> Don't miss anything relevant.

The reranker's goal is

> Put the most useful documents first.

These are different optimization problems.

---

# Why retrieval alone is not enough

Suppose the user asks

> "How do I configure dual connectivity in 5G NSA?"

Retriever returns

```
1. 5G NSA Overview
2. LTE Architecture
3. Dual Connectivity Configuration Guide
4. 5G Security
5. Ericsson Internal Release Notes
6. LTE Handover
7. EN-DC Deployment Guide
8. Beamforming
9. RRC Configuration
10. Random telecom document
```

Many are relevant.

But only two are actually what the LLM needs.

The reranker learns

```
3
7
9
1
5
2
...
```

This greatly improves answer quality.

---

# Question 1:

# What are the different reranker methods?

There are several families.

Think of them as increasingly intelligent—and increasingly expensive.

---

# Method 1: Score-based reranking

The simplest.

Retriever already gives similarity scores.

Example:

```
Embedding similarity

Doc A 0.94
Doc B 0.91
Doc C 0.83
```

Simply sort.

Pros

* extremely fast
* no extra model

Cons

* embedding similarity is not true relevance

---

# Method 2: Feature-based reranking (Learning to Rank)

Traditional search engines.

Uses handcrafted features.

Example features

```
BM25 score

Embedding score

Document length

Freshness

Popularity

Click-through rate

Number of query terms matched

Title match

Authority score
```

A machine learning model combines them.

```
Features
      │
      ▼
GBDT / XGBoost / LambdaMART
      │
      ▼
Ranking score
```

This dominated search engines before transformers.

---

# Method 3: Cross-Encoder rerankers

Today this is the most common reranker in RAG.

Instead of encoding query and document separately...

it processes them together.

Example

```
[CLS]

Query

How to configure ENDC?

[SEP]

Document

This guide explains dual connectivity...

```

Transformer reads both simultaneously.

Outputs

```
Relevance = 0.97
```

Examples

* BAAI/bge-reranker
* Cohere Rerank
* Jina AI Reranker
* MonoT5
* MS MARCO Cross Encoder

These usually outperform embedding similarity by a significant margin because they model interactions between query and document tokens directly.

---

# Method 4: Generative rerankers

Instead of predicting

```
Relevant?
```

they generate relevance.

Example prompt

```
Query

How to configure ENDC?

Document

...

Question

Is this document useful?
```

LLM answers

```
Highly relevant
```

or

```
Score: 9/10
```

This is slower but more flexible.

---

# Method 5: LLM-as-a-Judge reranking

Modern enterprise systems increasingly use this.

Example

```
Given this query

Given these 20 chunks

Rank them.
```

GPT

Claude

Gemini

Llama

perform the ranking.

Excellent quality.

Very expensive.

---

# Method 6: Late Interaction rerankers

Examples

ColBERT

Instead of one embedding,

each token has an embedding.

Similarity becomes

```
token ↔ token
```

rather than

```
vector ↔ vector
```

Huge improvement.

Popular in research and high-quality search systems.

---

# Method 7: Multi-stage reranking

Large systems rarely use one reranker.

Instead

```
Retriever

↓

Fast reranker

↓

Cross Encoder

↓

LLM Judge
```

Each stage filters further.

Google Search uses multiple ranking stages, and many production RAG systems follow the same pattern for balancing quality and latency.

---

# Summary

| Method           | Accuracy  | Speed     | Training Required |
| ---------------- | --------- | --------- | ----------------- |
| Similarity Score | Low       | Very Fast | No                |
| Learning-to-Rank | Medium    | Fast      | Yes               |
| Cross Encoder    | High      | Medium    | Usually No        |
| Late Interaction | High      | Medium    | Sometimes         |
| LLM Judge        | Very High | Slow      | No                |
| Generative       | High      | Slow      | Sometimes         |

---

# Question 2:

# How do you decide which reranker to use?

The answer depends on your constraints.

---

## Small RAG

```
100K documents
```

Use

```
Retriever

↓

Cross Encoder
```

Simple.

High quality.

---

## Large enterprise

```
100 million documents
```

Use

```
Hybrid Retrieval

↓

Feature Ranker

↓

Cross Encoder

↓

LLM Judge
```

---

## Low latency chatbot

Need

```
<200 ms
```

Avoid

LLM rerankers.

---

## Highest accuracy

Use

```
Retriever

↓

Cross Encoder

↓

LLM Judge
```

---

## Cheap deployment

Only embedding similarity.

---

# Question 3:

# Does a telecom reranker need telecom knowledge?

This is one of the most important questions.

The answer is

**Sometimes—but not always.**

Let's distinguish two situations.

---

## Scenario A

General documents.

Example

```
Configure VPN

Reset password

Install software

```

General rerankers work well.

No domain training.

---

## Scenario B

Highly specialized telecom

Example

```
ENDC

gNodeB

AMF

SMF

PDCCH

PUCCH

SRS

DRX

NR RRC

DU/CU split
```

General reranker may fail.

It doesn't know

```
ENDC

≈

Dual Connectivity
```

or

```
AMF != Authentication
```

This is where domain adaptation helps.

---

A telecom reranker should ideally understand:

* 3GPP terminology
* vendor-specific terminology
* abbreviations
* telecom procedures
* KPI names
* alarms
* network logs
* OSS/BSS language
* internal documentation style

Without that, it may incorrectly prefer documents with more common-language overlap over truly relevant technical documents.

---

# Question 4:

# How are rerankers trained?

Depends on the architecture.

---

## Cross Encoder training

Input

```
(Query, Document)
```

Output

```
Relevant

Not Relevant
```

Example

```
Q

Configure ENDC

Positive

ENDC deployment guide

Negative

LTE security document
```

Loss

Binary classification

or

Ranking loss.

---

## Pairwise ranking

Instead of labels

```
Relevant

Not Relevant
```

Model learns

```
Doc A

>

Doc B
```

Loss

```
Margin Ranking Loss
```

Example

```
Query

Configure ENDC

A

ENDC deployment

B

LTE history
```

Model learns

```
Score(A)

>

Score(B)
```

---

## Listwise training

Instead of pairs

Entire ranked list.

```
A

B

C

D
```

Ground truth

```
B

A

D

C
```

Model optimizes the whole ranking.

This often produces the best ranking quality but requires richer labels.

---

## Learning-to-Rank objectives

Classical search uses losses such as:

* Pointwise (predict a relevance score)
* Pairwise (optimize document comparisons)
* Listwise (optimize the entire ranked list)

Algorithms like RankNet, LambdaRank, and LambdaMART are designed around these objectives.

---

## Data sources

Training data comes from

* human labels
* click logs
* search logs
* support tickets
* expert annotations
* synthetic LLM-generated pairs (with validation)
* question-answer datasets mapped to source documents

---

# Question 5:

# When should you train your own reranker?

Most organizations should **not** start by training one.

Start with a strong open reranker and evaluate it.

Train only if there is evidence that the reranker is a bottleneck.

Good reasons include:

* very domain-specific terminology
* proprietary vocabulary
* many abbreviations
* poor ranking quality despite good retrieval
* internal documentation unlike public text
* significant gains demonstrated through offline evaluation

For example:

```
Open reranker

NDCG = 0.71

↓

Fine tuned telecom reranker

NDCG = 0.84
```

That improvement justifies the engineering effort.

---

# Question 6:

# Challenges in using and training rerankers

There are several practical challenges.

### 1. Labeled data

High-quality relevance labels are expensive.

You need experts to answer:

> Is this document actually better than that one for this query?

This is subjective and time-consuming.

---

### 2. Negative sampling

Easy negatives don't teach much.

Example

Positive

```
ENDC deployment
```

Negative

```
How to cook pasta
```

The model learns almost nothing.

Hard negatives are much better:

Positive

```
ENDC deployment guide
```

Negative

```
LTE dual connectivity troubleshooting
```

The distinction is subtle and informative.

---

### 3. Distribution shift

The reranker may be trained on:

```
MS MARCO
```

but deployed on:

```
Ericsson OSS manuals
```

Performance often degrades because the document style, terminology, and user queries differ.

---

### 4. Latency

Cross-encoders process every query-document pair.

If retrieval returns 100 documents:

```
100 forward passes
```

This can dominate end-to-end latency unless you prune candidates first or batch inference.

---

### 5. Context window limitations

The reranker may only process a limited number of tokens.

Large chunks

↓

Need truncation

↓

Important information lost

Chunking strategy therefore affects reranker performance.

---

### 6. Continual evolution

Products evolve.

Terminology changes.

New releases arrive.

The reranker may require periodic adaptation if ranking quality declines over time.

---

### 7. Evaluation complexity

Unlike retrieval, reranking must be evaluated with ranking metrics such as:

* NDCG@k (Normalized Discounted Cumulative Gain)
* MRR (Mean Reciprocal Rank)
* MAP (Mean Average Precision)
* Precision@k
* Recall@k
* Hit Rate@k

These should be measured on representative queries, ideally segmented by query type (fact lookup, troubleshooting, configuration, conceptual questions, etc.).

# A production mental model

A useful way to think about retrieval and reranking is as a progressively more precise funnel:

```
                    Entire Knowledge Base
                           │
                           ▼
                 Dense / Sparse / Hybrid Retrieval
                    (Recall-oriented)
                 1,000,000 → Top 100
                           │
                           ▼
                  Cross-Encoder Reranker
                (Fine-grained relevance)
                    Top 100 → Top 10
                           │
                           ▼
             Context Construction & Compression
                           │
                           ▼
                  LLM Answer Generation
                           │
                           ▼
                 Optional LLM Judge / Verifier
```

Each stage has a different objective:

* **Retriever:** maximize recall while remaining efficient.
* **Reranker:** maximize ranking quality among the retrieved candidates.
* **Context builder:** maximize the usefulness of the limited context window.
* **Generator:** synthesize a correct, grounded response.

---

Given your ongoing deep dive into RAG evaluation, the next topic that naturally follows is **Reranker Evaluation**. This is a substantial area in its own right because evaluating a reranker is fundamentally different from evaluating retrieval. It involves constructing pairwise and listwise relevance datasets, defining graded relevance labels, selecting appropriate metrics (NDCG, MRR, MAP, Recall@k, ERR), mining hard negatives, performing offline benchmarking, and validating improvements through online A/B testing. Understanding this layer completes the evaluation story between retrieval quality and final answer quality.


These questions get to the heart of modern retrieval systems. Once you understand them, you'll realize that **cross-encoders and late interaction models are not "special reranker architectures"—they are different ways of using transformers to solve the ranking problem.**

I'll answer them in increasing depth.

---

# 1. How are Cross Encoder models trained?

Let's first understand **what the model is actually trying to learn.**

Suppose we have the query:

> "How do I configure EN-DC in Ericsson gNodeB?"

and three documents.

```
Document A
-----------
EN-DC configuration procedure...

Document B
-----------
5G architecture overview...

Document C
-----------
LTE alarm handling...
```

We want the model to learn

```
Score(A) > Score(B) > Score(C)
```

That's all.

The challenge is how to teach it this ordering.

---

## Step 1 — Build training examples

Instead of giving the model only documents,

we always give

```
(Query, Document)
```

For example

```
Input

Query:
Configure ENDC

Document:
This document explains how to configure EN-DC...

Target

Relevant
```

Another example

```
Input

Query:
Configure ENDC

Document:
This document explains LTE paging...

Target

Not Relevant
```

The model repeatedly sees millions of these examples.

---

## Step 2 — Feed them into a transformer

Unlike embedding models,

the transformer sees BOTH texts together.

Input becomes

```
[CLS]

Configure ENDC

[SEP]

This guide explains EN-DC deployment...

[SEP]
```

This is exactly the same input format used by BERT.

Notice something important.

The attention mechanism can now connect

```
Configure
        ↓
configuration

ENDC
        ↓
EN-DC

gNodeB
        ↓
base station
```

The model is learning token-level interactions.

This is why cross encoders outperform embedding similarity.

---

## Step 3 — Final prediction layer

The transformer produces

```
CLS embedding
```

A small neural network is attached.

```
CLS

↓

Linear Layer

↓

Single Score
```

Example

```
0.97
```

or

```
3.8
```

depending on training objective.

---

## Step 4 — Compute loss

There are three major ways.

---

### Pointwise training

Treat ranking as classification.

```
Relevant

Not Relevant
```

Loss

```
Binary Cross Entropy
```

Example

```
Query

Configure ENDC

↓

Document

Deployment Guide

↓

Prediction

0.92

↓

Target

1
```

Simple.

---

### Pairwise training

This is much more common.

Instead of asking

```
Is A relevant?
```

we ask

```
Is A better than B?
```

Training sample

```
Query

Configure ENDC

Positive

ENDC deployment guide

Negative

LTE overview
```

Loss encourages

```
Score(Positive)

>

Score(Negative)
```

This directly optimizes ranking.

Popular losses include **Margin Ranking Loss** and **RankNet loss**.

---

### Listwise training

Instead of two documents

the model sees many.

```
Query

↓

10 documents

↓

Predicted ordering
```

Compare against

```
Ground truth ordering
```

This is the closest to the real ranking problem but also the most complex to train.

---

# 2. How is training data prepared?

This is arguably **more important than the model architecture.**

A mediocre model with excellent data usually beats a sophisticated model with poor data.

Let's see how data is built.

---

# Method 1 — Human annotation

Experts create triples.

```
Query

Configure ENDC

Positive

Deployment guide

Negative

LTE alarms
```

Simple.

High quality.

Very expensive.

---

# Method 2 — Search logs

Suppose users searched

```
Configure ENDC
```

Clicked

```
Document A
```

Ignored

```
Document B
```

This becomes

```
Positive

A

Negative

B
```

Google has used click data extensively, but raw clicks are noisy because users tend to click higher-ranked results even when they're not the best. In practice, click logs are debiased before being used for training.

---

# Method 3 — QA datasets

Suppose

```
Question

What is ENDC?
```

Answer

```
ENDC allows...
```

Source document

```
Deployment Guide
```

Training pair

```
Question

↓

Source document

Positive
```

All other retrieved documents become negatives.

---

# Method 4 — Synthetic generation

Very popular today.

Suppose you have

```
500,000 telecom manuals
```

Use an LLM.

```
Read document

↓

Generate likely questions

↓

Create training pairs
```

Example

```
Document

ENDC deployment...

↓

Generated Question

How do I enable ENDC?
```

Now we already have

```
Positive pair
```

without human effort.

---

# Method 5 — Hard negative mining

This is probably the most important step.

Suppose retrieval returns

```
1.

ENDC deployment

2.

ENDC troubleshooting

3.

5G NSA overview

4.

LTE deployment
```

Positive

```
1
```

Instead of using random negatives

```
Cooking recipe
```

use

```
2

3

4
```

These are called

**hard negatives**.

They force the model to learn subtle semantic differences.

Many modern pipelines iteratively improve the model by repeatedly mining harder negatives with the current retriever or reranker.

---

# What should a telecom dataset look like?

For every query,

store something like

| Query          | Positive              | Hard Negative             | Label |
| -------------- | --------------------- | ------------------------- | ----- |
| Configure ENDC | ENDC deployment guide | NSA architecture overview | 1 / 0 |
| PUCCH format   | PUCCH configuration   | PDCCH scheduling          | 1 / 0 |
| RRC Release    | RRC Release procedure | RRC Setup                 | 1 / 0 |

Even better,

graded relevance

| Document               | Relevance |
| ---------------------- | --------- |
| Exact deployment guide | 3         |
| Troubleshooting guide  | 2         |
| Overview               | 1         |
| Unrelated              | 0         |

Graded labels enable listwise objectives and metrics such as NDCG.

---

# 3. Are Cross Encoder models actually transformer models?

**Yes.**

In fact,

they are usually **standard transformer encoder models**.

Common choices include

```
BERT

RoBERTa

DeBERTa

ModernBERT

MPNet
```

Nothing special.

The only difference is **how we use them**.

---

## Bi-Encoder

```
Query

↓

Encoder

↓

Embedding
```

```
Document

↓

Encoder

↓

Embedding
```

Similarity

```
Cosine
```

Documents can be encoded offline, making retrieval very fast.

---

## Cross Encoder

```
Query

+

Document

↓

Same Transformer

↓

Relevance Score
```

Notice

the transformer attends

```
Query token

↓

Document token
```

This interaction is impossible in a bi-encoder.

---

Imagine

```
Query

Apple stock
```

Document

```
Apple released iPhone
```

Bi-encoder

Produces two independent vectors and hopes their similarity captures the meaning.

Cross-encoder

Directly attends

```
stock

↓

released

↓

company
```

and can determine whether the document is about the company, finance, or something else by modeling token interactions.

---

# 4. What do Late Interaction rerankers actually do?

This is one of the biggest advances in retrieval.

Let's understand the problem first.

---

## Problem with embedding models

Suppose

```
Query

Configure ENDC
```

Embedding model compresses the entire query into

```
768 numbers
```

Document

```
500 words
```

Also compressed into

```
768 numbers
```

Then

```
Cosine similarity
```

Everything about a long document is represented by one vector.

Important details can be averaged away.

---

## Late Interaction idea

Instead of

```
One vector
```

store

```
One vector

for every token.
```

Example

Document

```
Configure

ENDC

gNodeB

parameter

setup
```

Embeddings become

```
Configure

↓

768

ENDC

↓

768

gNodeB

↓

768

...
```

The document is now represented as a matrix rather than a single vector.

---

Now query

```
Configure ENDC
```

also becomes

```
Configure

↓

768

ENDC

↓

768
```

---

Instead of

```
Document vector

vs

Query vector
```

compute

```
Configure

↓

all document tokens

ENDC

↓

all document tokens
```

Each query token finds its best matching document token.

One popular scoring function, used by ColBERT, is **MaxSim**:

For each query token:

1. Compute similarity to every document token.
2. Keep only the highest similarity.
3. Sum those maxima across all query tokens.

Conceptually:

```
Query token 1 ──► best matching document token
Query token 2 ──► best matching document token
...
Final score = sum(best matches)
```

If a document contains a very strong match for every important query token, it scores highly.

This preserves fine-grained evidence that a single embedding would lose.

---

## Why is it called "Late Interaction"?

Because

the query and document are encoded **independently**, like a bi-encoder.

The interaction happens only **after encoding**, during scoring.

Hence

```
Late Interaction
```

instead of

```
Early Interaction
```

which is what a cross-encoder does.

---

Comparison:

| Model            | Interaction Timing            |
| ---------------- | ----------------------------- |
| Bi-Encoder       | Never                         |
| Late Interaction | During similarity computation |
| Cross Encoder    | During transformer attention  |

---

# 5. How is multi-stage reranking actually performed?

Large systems rarely compare every document with the most expensive model.

Instead, they progressively spend more computation on fewer candidates.

Think of it as a funnel.

```
10 million docs

↓

Retriever

↓

500 docs

↓

Fast reranker

↓

100 docs

↓

Cross Encoder

↓

20 docs

↓

LLM Judge

↓

5 docs
```

Every stage has a different objective.

---

## Stage 1 — Candidate Generation

Goal:

**Don't miss relevant documents.**

Use

* Dense retrieval
* BM25
* Hybrid retrieval

Return

```
Top 100–1000
```

High recall matters more than perfect ordering.

---

## Stage 2 — Lightweight reranking

Goal:

Remove obvious mistakes cheaply.

Possible methods:

* Reciprocal Rank Fusion (for hybrid retrieval)
* Metadata boosts (document type, recency, authority)
* Learning-to-Rank models such as LambdaMART
* Lightweight neural rerankers

Reduce

```
1000

↓

100
```

---

## Stage 3 — Cross Encoder

Goal

Deep semantic relevance.

Now

```
100

↓

20
```

Because

```
100 transformer passes
```

is manageable.

---

## Stage 4 — Context-aware filtering

The top 20 documents may still be unsuitable as LLM context.

Example:

```
Document 1

Chapter 1

Introduction
```

```
Document 2

Chapter 2

Introduction
```

Nearly duplicates.

We now optimize the **set** of documents, not just each document individually.

Typical operations include:

* Deduplication (remove repeated chunks)
* Diversity optimization (avoid near-identical passages)
* Metadata constraints (language, product version, access rights)
* Chunk merging or splitting
* Token-budget optimization

Reduce

```
20

↓

8
```

---

## Stage 5 — LLM Judge (optional)

In high-value applications such as legal, medical, or enterprise support, an LLM may inspect the final candidates.

For example:

```
User question

+

Top 8 chunks

↓

Rank the chunks by usefulness.
Explain why.
```

This stage can also identify missing evidence or contradictions before the answer generation step.

---

# One important insight

Many people think:

> "The retriever finds the documents and the reranker sorts them."

That's an oversimplification.

In mature systems, **each stage solves a different optimization problem**:

| Stage                | Primary Objective                                        |
| -------------------- | -------------------------------------------------------- |
| Retriever            | Maximize recall                                          |
| Lightweight reranker | Remove obvious false positives at low cost               |
| Cross-encoder        | Learn deep semantic relevance between query and document |
| Context optimizer    | Build the best *set* of evidence within the token budget |
| LLM judge            | Reason about which evidence is most useful for answering |

This distinction becomes especially important in enterprise RAG, where the final answer quality often depends as much on **context construction** as on the retriever or reranker themselves.

In fact, modern production systems increasingly view retrieval as a **multi-stage candidate selection pipeline**, where every stage trades off quality, latency, memory usage, and cost rather than relying on a single "best" reranker.

