# Rerankers in RAG Applications

> A comprehensive guide to reranker models — methods, architectures, training, evaluation, and production deployment patterns.

---

## Table of Contents

- [Context: Where Reranking Fits in RAG](#context-where-reranking-fits-in-rag)
- [1. Reranker Methods](#1-reranker-methods)
  - [1.1 Score-Based Reranking](#11-score-based-reranking)
  - [1.2 Feature-Based Reranking (Learning to Rank)](#12-feature-based-reranking-learning-to-rank)
  - [1.3 Cross-Encoder Rerankers](#13-cross-encoder-rerankers)
  - [1.4 Generative Rerankers](#14-generative-rerankers)
  - [1.5 LLM-as-a-Judge Reranking](#15-llm-as-a-judge-reranking)
  - [1.6 Late Interaction Rerankers](#16-late-interaction-rerankers)
  - [1.7 Multi-Stage Reranking](#17-multi-stage-reranking)
  - [1.8 Methods Summary](#18-methods-summary)
- [2. Choosing a Reranker](#2-choosing-a-reranker)
- [3. Domain Knowledge — Does a Reranker Need It?](#3-domain-knowledge--does-a-reranker-need-it)
- [4. Training Rerankers](#4-training-rerankers)
  - [4.1 Training Objectives & Loss Functions](#41-training-objectives--loss-functions)
  - [4.2 Training Data Preparation](#42-training-data-preparation)
  - [4.3 Hard Negative Mining](#43-hard-negative-mining)
  - [4.4 When to Train Your Own Reranker](#44-when-to-train-your-own-reranker)
- [5. Cross Encoder Architecture — Deep Dive](#5-cross-encoder-architecture--deep-dive)
  - [5.1 Architecture](#51-architecture)
  - [5.2 Why Cross Encoders Outperform Bi-Encoders](#52-why-cross-encoders-outperform-bi-encoders)
  - [5.3 Training Pipeline](#53-training-pipeline)
- [6. Late Interaction — Deep Dive](#6-late-interaction--deep-dive)
  - [6.1 The Problem with Single-Vector Embeddings](#61-the-problem-with-single-vector-embeddings)
  - [6.2 How Context-Aware Token Representations Are Created](#62-how-context-aware-token-representations-are-created)
  - [6.3 MaxSim Scoring](#63-maxsim-scoring)
  - [6.4 Why It Works (And Its Limitations)](#64-why-it-works-and-its-limitations)
  - [6.5 Architecture Comparison](#65-architecture-comparison)
- [7. Multi-Stage Reranking — Deep Dive](#7-multi-stage-reranking--deep-dive)
  - [7.1 The Funnel Model](#71-the-funnel-model)
  - [7.2 Stage-by-Stage Breakdown](#72-stage-by-stage-breakdown)
  - [7.3 Lightweight Reranking Methods](#73-lightweight-reranking-methods)
- [8. Metadata in Reranking](#8-metadata-in-reranking)
- [9. Evaluation Metrics](#9-evaluation-metrics)
  - [9.1 Precision@K](#91-precisionk)
  - [9.2 Recall@K](#92-recallk)
  - [9.3 Hit Rate@K](#93-hit-ratek)
  - [9.4 Mean Reciprocal Rank (MRR)](#94-mean-reciprocal-rank-mrr)
  - [9.5 Mean Average Precision (MAP)](#95-mean-average-precision-map)
  - [9.6 NDCG@K](#96-ndcgk)
  - [9.7 Metrics Summary](#97-metrics-summary)
  - [9.8 Which Metrics for Which Stage](#98-which-metrics-for-which-stage)
- [10. Challenges](#10-challenges)
- [Summary: The Production Mental Model](#summary-the-production-mental-model)

---

## Context: Where Reranking Fits in RAG

A typical RAG pipeline:

```
User Query
      │
      ▼
Query Processing
      │
      ▼
Retriever (Dense / Sparse / Hybrid)
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

**The retriever's goal:** Don't miss anything relevant (maximize recall).

**The reranker's goal:** Put the most useful documents first (maximize ranking quality).

These are different optimization problems. The retriever casts a wide net; the reranker makes the final quality-of-evidence decision.

### Why retrieval alone is not enough

Suppose the user asks: *"How do I configure dual connectivity in 5G NSA?"*

The retriever returns 10 documents — many are relevant, but only 2–3 are what the LLM actually needs. The reranker learns to push those to the top, which greatly improves answer quality.

### Three Independent Design Choices

A reranker is not one monolithic thing. It consists of three orthogonal decisions:

1. **Model architecture** — Cross Encoder, ColBERT, LambdaMART, etc.
2. **Training objective (loss function)** — Pointwise, Pairwise, Listwise
3. **Training data generation strategy** — Human labels, QA pairs, click logs, synthetic generation

These dimensions are largely independent. A Cross Encoder can be trained with pointwise, pairwise, or listwise loss.


---

## 1. Reranker Methods

There are several families of rerankers, progressively more intelligent — and more expensive.

### 1.1 Score-Based Reranking

The simplest approach. The retriever already produces similarity scores — just sort by them.

```
Embedding similarity:
  Doc A  0.94
  Doc B  0.91
  Doc C  0.83
```

**Pros:** Extremely fast, no extra model needed.
**Cons:** Embedding similarity ≠ true relevance. Semantic similarity doesn't capture whether a document actually *answers* the query.

### 1.2 Feature-Based Reranking (Learning to Rank)

Traditional search engine approach. Combines handcrafted features using a machine learning model.

**Features:**
- BM25 score
- Embedding similarity score
- Document length, freshness, popularity
- Click-through rate
- Number of query terms matched
- Title match, authority score

**Model:**
```
Features → GBDT / XGBoost / LambdaMART → Ranking score
```

This dominated search engines before transformers. Still widely used as a lightweight stage in multi-stage pipelines.

### 1.3 Cross-Encoder Rerankers

The most common reranker in modern RAG systems. Processes query and document *together* through a transformer.

```
Input:  [CLS] Query: Configure ENDC? [SEP] Document: This guide explains dual connectivity... [SEP]
Output: Relevance score = 0.97
```

The transformer's attention mechanism directly connects query tokens to document tokens, enabling deep semantic matching.

**Examples:** BAAI/bge-reranker, Cohere Rerank, Jina AI Reranker, MonoT5, MS MARCO Cross Encoder

**Why they outperform embedding similarity:** They model token-level interactions between query and document, rather than comparing two independently-compressed vectors.

### 1.4 Generative Rerankers

Instead of predicting a relevance score, they *generate* a relevance judgment.

```
Prompt:
  Query: Configure ENDC?
  Document: ...
  Question: Is this document useful for answering the query?

Output: "Highly relevant" or "Score: 9/10"
```

Slower but more flexible — can explain relevance decisions.

### 1.5 LLM-as-a-Judge Reranking

Modern enterprise systems increasingly use general-purpose LLMs for ranking.

```
Prompt:
  Given this query and these 20 chunks, rank them by relevance.
```

Models like GPT-4, Claude, Gemini, or Llama perform the ranking.

**Pros:** Excellent quality, no training needed, handles nuance.
**Cons:** Very expensive, high latency, non-deterministic.

### 1.6 Late Interaction Rerankers

Example: **ColBERT**

Instead of one embedding per document, each token retains its own embedding. Similarity is computed as token-to-token matching (MaxSim).

```
Query tokens  →  each finds best-matching document token
Final score   =  sum of best matches
```

Huge improvement over single-vector similarity while being much faster than cross-encoders.

*(See [Section 6](#6-late-interaction--deep-dive) for the full deep dive.)*

### 1.7 Multi-Stage Reranking

Large systems use multiple reranking stages:

```
Retriever → Fast reranker → Cross Encoder → LLM Judge
```

Each stage filters further, trading compute for precision.

*(See [Section 7](#7-multi-stage-reranking--deep-dive) for the full deep dive.)*

### 1.8 Methods Summary

| Method | Accuracy | Speed | Training Required |
|--------|----------|-------|-------------------|
| Similarity Score | Low | Very Fast | No |
| Learning-to-Rank | Medium | Fast | Yes |
| Cross Encoder | High | Medium | Usually No (pretrained) |
| Late Interaction | High | Medium | Sometimes |
| LLM Judge | Very High | Slow | No |
| Generative | High | Slow | Sometimes |


---

## 2. Choosing a Reranker

The right reranker depends on your constraints:

| Scenario | Recommended Approach |
|----------|---------------------|
| **Small RAG** (~100K docs) | Retriever → Cross Encoder |
| **Large enterprise** (~100M docs) | Hybrid Retrieval → Feature Ranker → Cross Encoder → LLM Judge |
| **Low latency chatbot** (< 200ms) | Avoid LLM rerankers; use lightweight neural or feature-based |
| **Highest accuracy** (latency flexible) | Retriever → Cross Encoder → LLM Judge |
| **Cheap deployment** (minimal infra) | Embedding similarity only |

**Decision factors:**
- Corpus size (determines how many stages you need)
- Latency budget (cross-encoders process each pair independently)
- Quality requirements (legal/medical demand higher quality)
- Infrastructure budget (LLM judges are expensive per-query)
- Domain specificity (specialized domains may need fine-tuned models)

---

## 3. Domain Knowledge — Does a Reranker Need It?

**Answer: Sometimes — but not always.**

### Scenario A: General documents

```
Configure VPN, Reset password, Install software
```

General rerankers (trained on MS MARCO, etc.) work well. No domain training needed.

### Scenario B: Highly specialized domain

Example (telecom):
```
ENDC, gNodeB, AMF, SMF, PDCCH, PUCCH, SRS, DRX, NR RRC, DU/CU split
```

A general reranker may fail because it doesn't know:
- `ENDC ≈ Dual Connectivity`
- `AMF ≠ Authentication`
- `gNodeB` is a 5G base station

### What domain-specific rerankers should understand

For a telecom example:
- 3GPP terminology and abbreviations
- Vendor-specific terminology
- Telecom procedures and KPI names
- Alarms and network logs
- OSS/BSS language
- Internal documentation style

### When to invest in domain adaptation

Without domain knowledge, the reranker may incorrectly prefer documents with common-language overlap over truly relevant technical documents. Fine-tune when:

- Terminology is highly specialized
- Abbreviations are pervasive
- General rerankers demonstrably underperform (measure with NDCG on domain-specific eval set)
- The relevance gap between fine-tuned and general is significant (e.g., NDCG 0.71 → 0.84)


---

## 4. Training Rerankers

### 4.1 Training Objectives & Loss Functions

There are three families of training objectives. Each optimizes a different thing.

#### Pointwise Training

Treats ranking as binary classification: "Is this document relevant to this query?"

**Loss Function — Binary Cross Entropy:**

$$L = -(y \log(\hat{y}) + (1-y) \log(1-\hat{y}))$$

Where:
- $y$ = ground truth label (1 = relevant, 0 = not)
- $\hat{y}$ = model's predicted probability

**Example:**
```
Query: "Configure ENDC"
Document: "ENDC deployment guide"
Prediction: 0.92
Target: 1
Loss: -log(0.92) ≈ 0.08 (low — good prediction)
```

| Advantages | Disadvantages |
|------------|---------------|
| Easy to implement | Doesn't directly optimize ranking order |
| Stable training | Can't distinguish "relevant" from "more relevant" |
| Needs only binary labels | Two docs both scoring 0.95 and 0.90 get no ordering signal |
| Large datasets available (MS MARCO) | Usually not state-of-the-art |

---

#### Pairwise Training

Asks: "Is document A more relevant than document B?"

**Loss Function — Margin Ranking Loss:**

$$L = \max(0, \; m - (s_p - s_n))$$

Where:
- $s_p$ = score of positive document
- $s_n$ = score of negative document
- $m$ = margin (hyperparameter)

**Example:**
```
Positive score: 5.2,  Negative score: 4.8,  Margin: 1.0
Difference: 0.4  (less than margin)
Loss: max(0, 1.0 - 0.4) = 0.6
```

**Loss Function — RankNet Loss (probabilistic):**

$$P = \sigma(s_p - s_n)$$
$$L = -\log(P) = \log(1 + e^{-(s_p - s_n)})$$

Where $\sigma$ is the sigmoid function. The target probability is 1 (positive should outrank negative).

| Advantages | Disadvantages |
|------------|---------------|
| Directly optimizes relative ordering | Pair explosion: 100 docs → 4,950 pairs |
| Aligns with ranking objective | Choosing informative pairs is crucial |
| Smooth gradients (RankNet) | Doesn't optimize the full list |
| No margin hyperparameter (RankNet) | |

---

#### Listwise Training

Optimizes the entire ranked list at once.

**Loss Function — ListNet (softmax cross-entropy on scores):**

$$p_i = \frac{e^{s_i}}{\sum_j e^{s_j}}$$

$$L = -\sum_i y_i \log(p_i)$$

Where scores are converted to a probability distribution and compared against the ground truth distribution.

**LambdaRank / LambdaMART:** Instead of defining a conventional loss, modifies gradients so that swaps improving NDCG receive larger updates. The optimization is directly aligned with the evaluation metric.

| Advantages | Disadvantages |
|------------|---------------|
| Optimizes entire ranking | Complex implementation |
| Usually best ranking quality | Requires richer labels (graded relevance) |
| Directly aligned with NDCG | More memory, larger batches |
| State-of-the-art for LTR | Harder optimization |

---

#### Summary

| Method | Loss | Learns |
|--------|------|--------|
| Pointwise | Binary Cross Entropy | Relevance (yes/no) |
| Pairwise | Margin Ranking, RankNet | Relative ordering (A > B) |
| Listwise | ListNet, ListMLE, LambdaLoss | Entire ranked list |

---

### 4.2 Training Data Preparation

Training data quality matters more than model architecture. A mediocre model with excellent data usually beats a sophisticated model with poor data.

#### Method 1 — Human Annotation

Experts create labeled triples:
```
Query: "Configure ENDC"
Positive: ENDC deployment guide
Negative: LTE alarms document
```

High quality but expensive (~2–5 min per annotation).

#### Method 2 — Search/Click Logs

```
User searched: "Configure ENDC"
Clicked: Document A
Ignored: Document B
→ Positive: A, Negative: B
```

Raw clicks are noisy (position bias — users click higher-ranked results). Must be debiased before use.

#### Method 3 — QA Datasets

```
Question: "What is ENDC?"
Answer source: Deployment Guide
→ Training pair: (Question, Deployment Guide) = Positive
```

Then retrieve top-K candidates for the question — all non-source documents become negatives.

#### Method 4 — Synthetic Generation (LLM-based)

```
Document: "ENDC deployment procedure..."
→ LLM generates: "How do I enable ENDC?"
→ Positive pair: (generated question, source document)
```

Scale: can generate millions of pairs from existing documents without human effort.

#### Method 5 — Hard Negative Mining

*(See next section)*

#### Training Data Format Example

| Query | Positive | Hard Negative | Label |
|-------|----------|---------------|-------|
| Configure ENDC | ENDC deployment guide | NSA architecture overview | 1 / 0 |
| PUCCH format | PUCCH configuration | PDCCH scheduling | 1 / 0 |
| RRC Release | RRC Release procedure | RRC Setup | 1 / 0 |

For graded relevance:

| Document | Relevance Grade |
|----------|----------------|
| Exact deployment guide | 3 |
| Troubleshooting guide | 2 |
| Overview | 1 |
| Unrelated | 0 |

---

### 4.3 Hard Negative Mining

**This is arguably the most important step in training data preparation.**

Regardless of how positives are obtained (human labels, QA pairs, clicks, synthetic), the negative examples are often the limiting factor.

#### Why easy negatives don't help

```
Positive: "ENDC deployment guide"
Easy negative: "How to cook pasta"
→ Model learns almost nothing (too obvious)
```

#### Why hard negatives are critical

```
Positive: "ENDC deployment guide"
Hard negative: "LTE dual connectivity troubleshooting"
→ Subtle distinction forces model to learn real relevance signals
```

#### Hard Negative Mining Pipeline

```
1. Generate positive examples (any method)
2. Retrieve Top-100 using current retriever/model
3. Remove known positives
4. Remaining retrieved documents = hard negatives
```

**Iterative mining:** Many modern systems repeat this every few training epochs, using the improved model to mine increasingly difficult negatives.

#### Should hard negative mining be applied to ALL data creation methods?

**Yes.** This is universal. Every dataset creation method (human annotation, QA datasets, click logs, synthetic generation) benefits from hard negatives. The quality of negatives determines how well the model learns to distinguish between "relevant" and "almost relevant."

---

### 4.4 When to Train Your Own Reranker

Most organizations should **not** start by training one. Start with a strong pretrained reranker and evaluate.

**Train only when:**
- Very domain-specific terminology
- Proprietary vocabulary and abbreviations
- Poor ranking quality despite good retrieval (measured via NDCG)
- Internal documentation unlike public text
- Significant gains demonstrated through offline evaluation

**Example justification:**
```
Open reranker NDCG = 0.71
Fine-tuned domain reranker NDCG = 0.84
→ +13% justifies the engineering effort
```


---

## 5. Cross Encoder Architecture — Deep Dive

### 5.1 Architecture

Cross encoders are **standard transformer encoder models** (BERT, RoBERTa, DeBERTa, ModernBERT, MPNet) with a linear prediction layer on top.

```
Input:
  [CLS] Query tokens [SEP] Document tokens [SEP]
        │
        ▼
  Transformer Encoder Layers (12–24 layers)
        │
        ▼
  [CLS] Representation (768-dim)
        │
        ▼
  Linear Layer (768 → 1)
        │
        ▼
  Single relevance score
```

There is no decoder. No autoregressive generation. Just an encoder producing a relevance score.

**Common base models:** BERT, RoBERTa, DeBERTa, ModernBERT, MPNet

### 5.2 Why Cross Encoders Outperform Bi-Encoders

**Bi-Encoder (embedding model):**
```
Query  → Encoder → 768-dim vector ─┐
                                     ├─ Cosine similarity
Document → Encoder → 768-dim vector ─┘
```

Query and document are encoded independently. No interaction between their tokens.

**Cross-Encoder:**
```
Query + Document → Same Transformer → Relevance score
```

The attention mechanism directly connects query tokens to document tokens:

```
"Apple stock" as query:
  - "Apple" attends to "released", "iPhone", "company" in the document
  - Can determine: is this about the company, the fruit, or finance?

Bi-encoder can't do this — each text is compressed independently.
```

This token-level interaction is why cross encoders achieve higher relevance accuracy at the cost of speed (can't pre-compute document embeddings).

### 5.3 Training Pipeline

```
Step 1: Build (query, document, label) training examples
Step 2: Feed [CLS] query [SEP] document [SEP] into transformer
Step 3: Take [CLS] representation → linear layer → score
Step 4: Compute loss (pointwise, pairwise, or listwise)
Step 5: Backpropagate and update weights
```

Repeat for millions of examples.

---

## 6. Late Interaction — Deep Dive

### 6.1 The Problem with Single-Vector Embeddings

Standard embedding models compress an entire document into one vector:

```
"Configure ENDC parameters on gNodeB for 5G NSA deployment"
→ 768 numbers
```

A 500-word document also becomes just 768 numbers. Important details get averaged away.

### 6.2 How Context-Aware Token Representations Are Created

**Common misconception:** "If I pass text to an embedding model, I get one vector."

**Reality:** The transformer *internally* computes an embedding for every token. The single vector you see is just a pooling step applied at the end.

#### What actually happens inside:

**Step 1 — Tokenization:**
```
"Configure ENDC on gNodeB"
→ [CLS] Configure END ##C on g ##Node ##B [SEP]
→ 8 tokens
```

**Step 2 — Initial embeddings:**
Each token starts with a learned embedding: a matrix of shape `(8, 768)`.

**Step 3 — Transformer layers (12 layers of self-attention):**

Each layer updates every token's representation by attending to all other tokens:

```
Layer 1: "Configure" attends to "ENDC", "gNodeB", etc. → updated representation
Layer 2: Updated "Configure" attends to updated "ENDC", etc.
...
Layer 12: Final contextualized representations
```

After 12 layers, the embedding for "ENDC" is *not* the same as "ENDC" in "ENDC troubleshooting" — because it attended to different surrounding tokens.

**Step 4 — Output:**
The transformer produces a matrix `(N_tokens, 768)` — one contextualized vector per token.

**Standard embedding models:** Pool this into one vector (mean pooling or [CLS]).
**ColBERT (late interaction):** Keep ALL token vectors. No pooling.

### 6.3 MaxSim Scoring

ColBERT scores a (query, document) pair using MaxSim:

```
Query: "Configure ENDC" → 2 token vectors (each 768-dim)
Document: 400 tokens → 400 token vectors (each 768-dim)

For each query token:
  Compute cosine similarity against ALL 400 document tokens
  Keep only the MAXIMUM similarity

Score = sum of max similarities across all query tokens
```

**Example:**
```
"Configure" → best match in document: "configuration" → sim = 0.94
"ENDC"      → best match in document: "EN-DC"         → sim = 0.98

Final score = 0.94 + 0.98 = 1.92
```

### 6.4 Why It Works (And Its Limitations)

**Why it works:** Token embeddings are *contextualized* — they encode surrounding context from self-attention. We're comparing context-aware representations, not raw word embeddings.

**What it doesn't capture:** Cross-attention between query and document during encoding. The query "Apple stock" and document "Apple released iPhone" are encoded independently — the model can't resolve ambiguity by seeing both simultaneously (unlike a cross-encoder).

**Industry usage:** Yes — ColBERT and variants are used in production for:
- Large-scale document search
- Enterprise semantic search
- Legal and academic search
- Code search

Late interaction occupies the middle ground between bi-encoders (fast, lower quality) and cross-encoders (slow, highest quality).

### 6.5 Architecture Comparison

| Architecture | Interaction | Encoding | Speed | Quality |
|-------------|-------------|----------|-------|---------|
| **Bi-Encoder** | None (cosine of pooled vectors) | Independent | Fastest (pre-compute docs) | Good |
| **Late Interaction** | After encoding (MaxSim on token vectors) | Independent | Medium | High |
| **Cross-Encoder** | During encoding (full attention) | Joint | Slowest (pair-by-pair) | Highest |

```
Quality:       Bi-Encoder  <  Late Interaction  <  Cross Encoder
Speed:         Bi-Encoder  >  Late Interaction  >  Cross Encoder
Interaction:   None           Post-encoding        During encoding
```


---

## 7. Multi-Stage Reranking — Deep Dive

### 7.1 The Funnel Model

Large systems progressively spend more computation on fewer candidates:

```
10 million docs
      ↓  Retriever
500 docs
      ↓  Fast reranker
100 docs
      ↓  Cross Encoder
20 docs
      ↓  Context optimizer
8 docs
      ↓  LLM Judge (optional)
5 docs → to LLM
```

### 7.2 Stage-by-Stage Breakdown

| Stage | Goal | Method | Input → Output | Primary Metric |
|-------|------|--------|----------------|----------------|
| **1. Candidate Generation** | Don't miss relevant docs | Dense + Sparse + Hybrid retrieval | Corpus → Top 100–1000 | Recall |
| **2. Lightweight Reranking** | Remove obvious false positives cheaply | RRF, metadata boosts, LambdaMART | 1000 → 100 | Precision gain |
| **3. Cross Encoder** | Deep semantic relevance | Neural cross-encoder | 100 → 20 | NDCG |
| **4. Context-Aware Filtering** | Optimize the *set* for LLM consumption | Dedup, diversity, token budget | 20 → 8 | Context quality |
| **5. LLM Judge** (optional) | Final relevance reasoning | GPT-4, Claude, etc. | 8 → 5 | Answer quality |

**Each stage has a different optimization:**

| Stage | Primary Objective |
|-------|-------------------|
| Retriever | Maximize recall |
| Lightweight reranker | Remove obvious false positives at low cost |
| Cross-encoder | Learn deep semantic relevance between query and document |
| Context optimizer | Build the best *set* of evidence within the token budget |
| LLM judge | Reason about which evidence is most useful for answering |

### 7.3 Lightweight Reranking Methods

#### Reciprocal Rank Fusion (RRF)

Combines rankings from multiple retrievers without training:

$$\text{RRF}(d) = \sum_i \frac{1}{k + r_i(d)}$$

Where:
- $r_i(d)$ = rank of document $d$ in retriever $i$
- $k$ = constant (typically 60)

**Example:**
```
Dense retrieval: [A, B, C, D]
BM25:            [C, A, E, F]

RRF(A) = 1/(60+1) + 1/(60+2) = 0.0164 + 0.0161 = 0.0325
RRF(C) = 1/(60+3) + 1/(60+1) = 0.0159 + 0.0164 = 0.0323
```

Documents ranking well in multiple retrievers rise to the top.

**Strengths:** No training, robust across domains, strong baseline for hybrid search.

#### Metadata Boosting

Adjust ranking scores using document metadata:

```
Current software version: × 1.5
Official manual: × 2.0
Internal wiki: × 0.8
Document age < 6 months: × 1.2
```

Especially useful when business priorities matter alongside semantic relevance.

#### Learning-to-Rank Models (LambdaMART)

Gradient-boosted decision trees trained on heterogeneous features:

**Input features:**
- BM25 score
- Dense similarity score
- Document freshness, authority, length
- Number of matched keywords
- Click-through rate
- Metadata features

**Strengths:** Extremely fast inference, handles mixed numeric features, interpretable feature importance.
**Weakness:** Cannot perform deep semantic matching on raw text alone.

#### Lightweight Neural Rerankers

Distilled/small transformer models:
- MiniLM, TinyBERT, DistilBERT, small ModernBERT variants

Provide much of the semantic quality of a full cross-encoder at significantly reduced latency. Used when hundreds of candidates still need neural scoring.

---

## 8. Metadata in Reranking

Rerankers can and do use metadata, through three integration patterns:

### Pattern 1: Pre-ranking filters and boosts

Metadata applied *before* neural reranking:
- Filter by language, product version, access rights
- Boost by document type, recency, authority

### Pattern 2: Input augmentation

Include metadata in the text passed to the cross-encoder:

```
Title: ENDC Deployment Guide
Product: Ericsson Radio 6648
Version: 24.3
Document Type: Configuration Manual

Content: This guide explains how to configure...
```

The model can learn to weight official manuals higher than wiki pages.

### Pattern 3: Feature fusion

Combine neural relevance score with metadata features in a downstream model:

```
Neural score (from cross-encoder): 0.87
Recency score: 0.95
Authority score: 0.80
Product match: 1.0
→ Final combined score: 0.91
```

### Metadata is especially valuable for:

- Product/version compatibility filtering
- Document recency weighting
- Access permissions enforcement
- Source trustworthiness signals
- Language matching
- Customer-specific document routing


---

## 9. Evaluation Metrics

Different metrics measure different aspects of ranking quality. There is no single "best" metric.

**Running example used throughout:**

| Rank | Document | Relevant? | Relevance Grade |
|------|----------|-----------|-----------------|
| 1 | D1 | Yes | 3 |
| 2 | D2 | No | 0 |
| 3 | D3 | Yes | 2 |
| 4 | D4 | Yes | 1 |
| 5 | D5 | No | 0 |

Total relevant documents in corpus: **4**

---

### 9.1 Precision@K

**Question:** "Of the top K retrieved documents, how many are relevant?"

**Formula:**

$$\text{Precision@K} = \frac{|\text{relevant} \cap \text{top-K}|}{K}$$

**Example (K=3):**
```
Top 3: [D1(relevant), D2(not), D3(relevant)]
Precision@3 = 2/3 = 0.667
```

**When to use:** RAG and search where only the top few results matter.

| Advantages | Disadvantages |
|------------|---------------|
| Very intuitive | Doesn't account for missed relevant docs |
| Focuses on user experience | Doesn't distinguish relevance grades |
| Easy to explain | Ignores everything below rank K |

---

### 9.2 Recall@K

**Question:** "Of all relevant documents, how many did we retrieve in the top K?"

**Formula:**

$$\text{Recall@K} = \frac{|\text{relevant} \cap \text{top-K}|}{|\text{total relevant}|}$$

**Example (K=5):**
```
Relevant found in top-5: {D1, D3, D4} = 3
Total relevant: 4
Recall@5 = 3/4 = 0.75
```

**When to use:** Retriever evaluation, especially first-stage retrieval where coverage is critical.

| Advantages | Disadvantages |
|------------|---------------|
| Measures coverage | Ignores ranking order |
| Critical for RAG (missing evidence = wrong answer) | Docs at rank 95 count equally to rank 1 |
| Most important retrieval metric | |

---

### 9.3 Hit Rate@K

**Question:** "Did at least ONE relevant document appear in the top K?"

**Formula:**

$$\text{Hit@K} = \begin{cases} 1 & \text{if any relevant doc in top-K} \\ 0 & \text{otherwise} \end{cases}$$

**Mean Hit Rate** = average across all queries.

**Example:**
```
Query A: relevant doc in top-5 → Hit = 1
Query B: no relevant doc in top-5 → Hit = 0
Query C: relevant doc in top-5 → Hit = 1
Mean Hit Rate@5 = (1+0+1)/3 = 0.667
```

**When to use:** QA and RAG where one good chunk is often sufficient.

| Advantages | Disadvantages |
|------------|---------------|
| Simple, intuitive | Ignores how many relevant docs found |
| Matches many RAG use cases | Doesn't care about ranking position |

---

### 9.4 Mean Reciprocal Rank (MRR)

**Question:** "How early does the FIRST relevant document appear?"

**Formula:**

$$\text{RR} = \frac{1}{\text{rank of first relevant document}}$$

$$\text{MRR} = \frac{1}{N} \sum_{i=1}^{N} \text{RR}_i$$

**Example:**

| Query | First Relevant Rank | Reciprocal Rank |
|-------|--------------------:|----------------:|
| Q1 | 1 | 1.000 |
| Q2 | 2 | 0.500 |
| Q3 | 5 | 0.200 |

$$\text{MRR} = \frac{1.0 + 0.5 + 0.2}{3} = 0.567$$

**When to use:** QA and chatbots where users expect the first result to be correct.

| Advantages | Disadvantages |
|------------|---------------|
| Strongly rewards placing first hit early | Ignores all relevant docs after the first |
| Matches user behavior (stop at first good answer) | Only measures one point in the ranking |

---

### 9.5 Mean Average Precision (MAP)

**Question:** "How well are ALL relevant documents ranked across the list?"

**Formula:**

$$\text{AP} = \frac{1}{R} \sum_{k=1}^{n} \text{Precision@k} \times \text{rel}(k)$$

Where $R$ = total relevant documents, $\text{rel}(k)$ = 1 if rank $k$ is relevant.

**Example (using our running example):**

Relevant documents at ranks 1, 3, 4:
- Precision@1 = 1/1 = 1.000
- Precision@3 = 2/3 = 0.667
- Precision@4 = 3/4 = 0.750

$$\text{AP} = \frac{1.0 + 0.667 + 0.75}{4} = 0.604$$

(Denominator = 4 because there are 4 total relevant in corpus)

**MAP** = mean AP across all queries.

**When to use:** Search engine benchmarking, retriever evaluation with multiple relevant documents.

| Advantages | Disadvantages |
|------------|---------------|
| Considers order AND multiple relevant docs | Binary relevance only |
| Well-established in IR literature | Can't distinguish "perfect" from "somewhat relevant" |
| Good overall ranking quality indicator | |

---

### 9.6 NDCG@K

**Question:** "Is the ranking optimal, considering that some documents are MORE relevant than others?"

This is the most comprehensive ranking metric and the industry standard for reranker evaluation.

#### Step 1 — Discounted Cumulative Gain (DCG@K)

$$\text{DCG@K} = \sum_{i=1}^{K} \frac{2^{rel_i} - 1}{\log_2(i+1)}$$

Two components:
- **Relevance gain:** $2^{rel} - 1$ (grade-3 is worth much more than grade-1)
- **Position discount:** $\frac{1}{\log_2(i+1)}$ (earlier positions weighted more)

**Example (using running example):**

| Rank | Grade | Gain $(2^{rel}-1)$ | Discount $(\frac{1}{\log_2(i+1)})$ | Contribution |
|------|-------|------|----------|--------------|
| 1 | 3 | 7 | 1.000 | 7.000 |
| 2 | 0 | 0 | 0.631 | 0.000 |
| 3 | 2 | 3 | 0.500 | 1.500 |
| 4 | 1 | 1 | 0.431 | 0.431 |

$$\text{DCG@4} = 7.0 + 0 + 1.5 + 0.431 = 8.931$$

#### Step 2 — Ideal DCG (IDCG@K)

Sort documents in perfect order: grades [3, 2, 1, 0]:

$$\text{IDCG@4} = \frac{7}{1.0} + \frac{3}{0.631 \cdot \log_2(3)} + \frac{1}{\log_2(4)} = 7 + 1.893 + 0.500 = 9.393$$

#### Step 3 — Normalize

$$\text{NDCG@K} = \frac{\text{DCG@K}}{\text{IDCG@K}} = \frac{8.931}{9.393} \approx 0.951$$

**Range:** 0 to 1 (1.0 = perfect ranking)

**When to use:** Reranker evaluation, any time you have graded relevance labels.

| Advantages | Disadvantages |
|------------|---------------|
| Handles graded relevance | Requires graded labels (more annotation effort) |
| Rewards placing best docs first | More complex to compute and explain |
| Industry standard for ranking | |
| Captures both "did we find it?" and "did we rank it well?" | |

---

### 9.7 Metrics Summary

| Metric | Measures | Requires | Best For | Key Limitation |
|--------|----------|----------|----------|----------------|
| **Precision@K** | Top-K purity | Binary labels | RAG context quality | Ignores missed docs |
| **Recall@K** | Coverage | Binary labels | Retriever evaluation | Ignores order |
| **Hit Rate@K** | At-least-one success | Binary labels | QA systems | Ignores quantity and position |
| **MRR** | First-hit speed | Binary labels | Chatbots, QA | Ignores all after first hit |
| **MAP** | Overall ranking with multiple relevant docs | Binary labels | Search benchmarking | Can't use graded relevance |
| **NDCG@K** | Full ranking quality with grades | Graded labels | Reranker evaluation | Needs graded annotation |

### 9.8 Which Metrics for Which Stage

| RAG Pipeline Stage | Primary Metrics |
|--------------------|----------------|
| Candidate Retrieval | Recall@K, Hit Rate@K |
| Reranking | NDCG@K, MAP, MRR |
| Context Construction | Context Precision, Context Recall |
| Answer Generation | Faithfulness, Correctness, Groundedness |

**Key insight:** Retrievers are *recall-oriented* (find everything). Rerankers are *order-oriented* (rank correctly). That's why Recall@K dominates retrieval evaluation while NDCG@K dominates reranker evaluation.


---

## 10. Challenges

Practical challenges in using and training rerankers:

### 10.1 Labeled Data Scarcity

High-quality relevance labels are expensive. You need domain experts to answer: "Is this document actually better than that one for this query?" This is subjective and time-consuming.

**Mitigation:** Synthetic generation + hard negative mining + LLM annotation with human validation.

### 10.2 Negative Sampling Quality

Easy negatives don't teach the model anything:
```
Positive: "ENDC deployment guide"
Easy negative: "How to cook pasta"       ← useless
Hard negative: "LTE dual connectivity"    ← informative
```

**Mitigation:** Always use retriever-mined hard negatives. Re-mine as the model improves.

### 10.3 Distribution Shift

A reranker trained on MS MARCO (web search queries) may degrade when deployed on Ericsson OSS manuals. Document style, terminology, and user query patterns differ significantly.

**Mitigation:** Fine-tune on domain-specific data, or at minimum evaluate on representative domain queries before deploying.

### 10.4 Latency

Cross-encoders process every (query, document) pair independently. If retrieval returns 100 documents, that's 100 forward passes.

**Mitigation:** Multi-stage pipeline (lightweight reranker first), batched inference, smaller models (MiniLM, DistilBERT), or prune candidates aggressively before cross-encoding.

### 10.5 Context Window Limitations

Rerankers may only process limited tokens. Large chunks require truncation, potentially losing critical information.

**Mitigation:** Design chunking strategy with reranker context limits in mind. Consider chunk summaries or leading-text strategies.

### 10.6 Continual Evolution

Products evolve, terminology changes, new releases arrive. Reranker performance may degrade over time.

**Mitigation:** Periodic re-evaluation with fresh queries. Track NDCG trends. Re-train or fine-tune when metrics decline.

### 10.7 Evaluation Complexity

Unlike retrieval (binary: "found it or not"), reranking requires ranking-aware metrics (NDCG, MAP, MRR) measured on representative queries segmented by type (fact lookup, troubleshooting, configuration, conceptual).

**Mitigation:** Build a graded relevance eval set early. Automate metric computation. Segment results by query type.

---

## Summary: The Production Mental Model

A reranker is one stage in a progressively more precise funnel:

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

**Each stage has a clear responsibility:**

| Stage | Responsibility |
|-------|---------------|
| Retriever | Maximize recall — don't miss relevant evidence |
| Reranker | Maximize ranking — put the best evidence first |
| Context builder | Maximize context quality — within token budget |
| Generator | Synthesize correct, grounded response |

**Key takeaways:**

1. Ranking is where much of production RAG quality comes from
2. Cross-encoders are the default choice; deploy without training first
3. Train your own only when domain-specific evaluation shows a gap
4. Hard negatives are the single most impactful training data decision
5. Use NDCG@K as the primary reranker metric
6. Multi-stage pipelines balance quality vs. latency at scale
7. Treat the reranker as an ML system with its own eval set, metrics, and regression tests


