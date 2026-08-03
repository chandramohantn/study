Context evaluation is where RAG evaluation becomes more specific to **LLM systems** rather than traditional information retrieval.

Retrieval evaluation asks:

> **Did we find the right evidence?**

Context evaluation asks:

> **Given everything we found, did we construct the right evidence package for the LLM?**

Those sound similar, but they are not the same problem.

# Module: Context Evaluation

Consider this pipeline:

```text
Query
  │
  ▼
Candidate Retrieval
  │
  │ 100 chunks
  ▼
Reranking
  │
  │ 20 chunks
  ▼
Context Selection
  │
  │ 8 chunks
  ▼
Deduplication / Compression / Ordering
  │
  ▼
FINAL CONTEXT
  │
  ▼
Prompt
  │
  ▼
LLM
```

Retrieval evaluation primarily concerns the left side:

```text
Corpus → Candidates → Ranking
```

Context evaluation concerns the transformation:

```text
Retrieved Candidates
        ↓
Select
        ↓
Filter
        ↓
Deduplicate
        ↓
Compress
        ↓
Order
        ↓
Fit token budget
        ↓
Final LLM Context
```

That distinction becomes extremely important in sophisticated RAG architectures.

---

# 1. Why retrieval quality ≠ context quality

Suppose the question is:

> "What happens to employee health insurance after resignation?"

Your retriever returns:

```text
1. Health benefits policy        ← highly relevant
2. Employee termination policy   ← highly relevant
3. Insurance FAQ                 ← relevant
4. Cafeteria policy              ← irrelevant
5. Office locations              ← irrelevant
```

Retrieval isn't terrible.

But imagine your context builder has room for only two chunks and chooses:

```text
Cafeteria policy
Office locations
```

Retrieval succeeded.

Context construction failed.

The LLM never sees the relevant evidence.

---

The opposite can also happen.

Retriever:

```text
20 candidates
15 irrelevant
5 relevant
```

Reranking + context selection:

```text
5 relevant chunks
```

Retrieval precision was poor.

But final context quality is excellent.

That's why these stages should be measured independently.

---

# 2. What are we evaluating?

For a query `q`, suppose the final context is:

```text
C = {c1, c2, c3, ... ck}
```

We want to know:

> Does C contain the right information, with minimal noise, in a form the LLM can actually use?

I break that into roughly seven dimensions:

| Dimension   | Question                                                 |
| ----------- | -------------------------------------------------------- |
| Relevance   | Is the context related to the question?                  |
| Sufficiency | Is enough evidence present to answer?                    |
| Precision   | How much of the context is actually useful?              |
| Redundancy  | Are we repeating the same information?                   |
| Diversity   | Are necessary perspectives/sources represented?          |
| Consistency | Do the chunks contradict each other?                     |
| Usability   | Is the context structured so the LLM can reason over it? |

Let's examine them separately.

---

# 3. Context Relevance

The simplest question:

> Is each supplied chunk actually useful for answering this query?

Suppose:

```text
Question:
How many vacation days do new employees receive?

Context:

C1: New employees receive 20 vacation days.
C2: Employees receive health insurance.
C3: Our offices operate from 9 AM to 5 PM.
```

Only `C1` is relevant.

You could label them:

```text
C1 → Relevant
C2 → Irrelevant
C3 → Irrelevant
```

A simple context precision-like measure would therefore be:

```text
Relevant context items
──────────────────────
Total context items

1 / 3
```

But there's a complication.

Not every chunk is equally relevant.

You may want graded relevance:

```text
3 = directly answers question
2 = important supporting evidence
1 = tangentially useful
0 = irrelevant
```

For example:

```text
C1 → 3
C2 → 0
C3 → 0
```

This gives you much richer diagnostics than binary labels.

---

# 4. Context Sufficiency

This is one of the most important context metrics.

Ask:

> **Could a competent model answer the question correctly using only this context?**

This is different from relevance.

Consider:

```text
Question:
What are the steps for resetting the device?
```

Context:

```text
Step 1: Disconnect power.
Step 2: Hold reset for 10 seconds.
```

Both chunks are relevant.

Context relevance:

```text
Excellent
```

But suppose the actual procedure contains:

```text
Step 1
Step 2
Step 3
Step 4
```

Your context is incomplete.

Therefore:

```text
Relevance     = high
Sufficiency   = low
```

This distinction is critical.

---

# 5. Context Recall / Completeness

If you have ground-truth evidence, you can measure this more objectively.

Suppose the reference answer requires four facts:

```text
F1
F2
F3
F4
```

Final context supports:

```text
F1 ✓
F2 ✓
F3 ✗
F4 ✓
```

Then evidence coverage is:

```text
3 / 4 = 75%
```

This is a useful way to think about context completeness.

Notice that this is slightly different from document recall.

The relevant unit is now **information**, not necessarily documents.

That's an important conceptual improvement.

---

# 6. Document Recall vs Information Recall

Suppose one ground-truth document contains 10 relevant facts.

Your system retrieves that document but chunking/context selection only preserves two facts.

Document-level retrieval might say:

```text
Recall = 100%
```

Yet the LLM receives only:

```text
2 / 10 facts
```

Information coverage:

```text
20%
```

This is why document-level retrieval metrics can make a RAG system look healthier than it actually is.

For advanced RAG evaluation, **claim/fact-level coverage** becomes very useful.

---

# 7. Context Redundancy

Suppose you have a 10,000-token context budget.

Your system selects:

```text
Chunk 1:
Warranty is 30 days.

Chunk 2:
The warranty period lasts thirty days.

Chunk 3:
Customers receive a 30-day warranty.

Chunk 4:
Warranty duration: 30 days.
```

Retrieval precision?

Potentially 100%.

Every chunk is relevant.

But context quality?

Poor.

You've spent four chunks communicating one fact.

---

A useful conceptual metric is:

```text
Unique useful information
─────────────────────────
Total supplied information
```

High redundancy means:

* wasted tokens
* increased latency
* increased cost
* less room for other evidence

And potentially worse generation.

---

# 8. Why "More Context" Is Not Always Better

This is a major RAG misconception.

People assume:

```text
More retrieved chunks
        ↓
More information
        ↓
Better answer
```

Not necessarily.

Often:

```text
More chunks
    ↓
More irrelevant information
    ↓
More conflicting information
    ↓
More attention competition
    ↓
Harder reasoning
    ↓
Potentially worse answer
```

This creates an optimization problem:

> **Find the minimum sufficient context.**

Not:

> Maximize context.

This is one of the core design objectives of context construction.

---

# 9. Context Diversity

Now consider a comparison question:

> Compare Product A and Product B.

Your context contains:

```text
Chunk 1 → Product A
Chunk 2 → Product A
Chunk 3 → Product A
Chunk 4 → Product A
```

Every chunk is relevant.

Precision:

```text
100%
```

But can the LLM answer the comparison?

No.

There is no information about Product B.

Context diversity / coverage is poor.

---

The ideal context might be:

```text
A architecture
A performance

B architecture
B performance
```

This becomes especially important for:

* comparison questions
* multi-hop reasoning
* research assistants
* legal analysis
* scientific RAG

---

# 10. Multi-Hop Context

Consider:

> Who is the CEO of the company that acquired Company X?

You might need:

```text
Chunk A:
Company Y acquired Company X.

             ↓

Chunk B:
The CEO of Company Y is Jane Smith.
```

Neither chunk alone answers the complete question.

Together they do.

This creates an important concept:

> **Context-set sufficiency.**

Evaluating individual chunks independently isn't enough.

You must sometimes evaluate:

```text
{C1, C2, C3}
```

as a set.

This is particularly important for agentic search and research systems.

---

# 11. Context Consistency

Now suppose your context contains:

```text
Chunk A:
Refund period is 30 days.
Published: 2024

Chunk B:
Refund period is 60 days.
Published: 2026
```

Both chunks are relevant.

Both are legitimate documents.

But they contradict each other.

Your context builder should ideally recognize:

```text
2026 supersedes 2024
```

rather than blindly feeding both to the model.

Context evaluation should therefore detect:

```text
Contradictory claims
Version conflicts
Temporal conflicts
Source conflicts
```

This connects directly back to the metadata and freshness evaluations we discussed earlier.

---

# 12. Context Ordering

Suppose you select the correct 20 chunks.

Does their order matter?

Potentially, yes.

For example:

```text
Chunk 1  → irrelevant
Chunk 2  → background
...
Chunk 10 → critical evidence
...
Chunk 20 → critical evidence
```

versus:

```text
Chunk 1 → critical evidence
Chunk 2 → critical evidence
Chunk 3 → supporting evidence
...
```

The second arrangement may be easier for the model to use.

Therefore, you may evaluate whether the highest-value evidence is placed appropriately within the final prompt.

This is particularly relevant for very long contexts.

---

# 13. Context Compression Evaluation

Modern RAG systems increasingly compress retrieved information.

Pipeline:

```text
20 retrieved chunks
        ↓
Context Compressor
        ↓
Extract relevant sentences
        ↓
5 compact chunks
        ↓
LLM
```

Compression is useful.

But dangerous.

Suppose original text says:

> Employees are **not** eligible for reimbursement unless approval is obtained beforehand.

Bad compressor:

> Employees are eligible for reimbursement.

One missing word completely reverses the meaning.

So compressed context needs its own evaluation:

```text
Original Evidence
       ↓
Compressed Evidence
       ↓
Meaning Preserved?
```

Metrics might include:

* factual preservation
* information recall
* contradiction rate
* compression ratio

---

# 14. How Do We Actually Evaluate Context?

Now we're getting to the important engineering question.

There are four major approaches.

## Approach A — Ground-Truth Evidence

Best when available.

Evaluation case:

```yaml
query: "What happens to benefits after resignation?"

required_evidence:
  - fact_1
  - fact_2
  - fact_3
```

Run RAG.

Final context:

```yaml
context:
  - chunk_7
  - chunk_22
  - chunk_31
```

Then determine whether those chunks contain:

```text
fact_1 ✓
fact_2 ✓
fact_3 ✗
```

Context sufficiency:

```text
2 / 3
```

This is one of the strongest evaluation approaches because you have explicit ground truth.

---

# 15. Approach B — Human Evaluation

Give an expert:

```text
Query

+

Final Context
```

Ask them to score:

```text
Relevance       4/5
Sufficiency     3/5
Redundancy      2/5
Consistency     5/5
```

High quality.

Expensive.

Therefore, this is usually used for gold datasets and judge calibration rather than millions of production queries.

---

# 16. Approach C — LLM-as-a-Judge

This is where frameworks like Ragas and DeepEval become interesting.

Give a judge:

```text
Query

+

Retrieved Context
```

Ask:

> Does the supplied context contain enough information to answer the query?

Return structured output:

```json
{
  "sufficient": false,
  "missing_information": [
    "eligibility duration"
  ],
  "score": 0.67
}
```

Or evaluate each chunk:

```text
C1 → 3
C2 → 0
C3 → 2
C4 → 1
```

Then calculate context metrics.

The LLM is essentially functioning as a **semantic relevance classifier**.

---

# 17. Approach D — Downstream Ablation

This is a particularly interesting technique.

Instead of asking a judge whether context is useful, test it experimentally.

Suppose:

```text
Context A
    ↓
LLM
    ↓
Answer Accuracy = 91%
```

Context B:

```text
Context B
    ↓
Same LLM
    ↓
Answer Accuracy = 74%
```

If everything except context is held constant, Context A is empirically better for the downstream task.

This is extremely useful when optimizing:

* Top-K
* reranking
* compression
* deduplication
* chunk ordering

It evaluates context by its **causal effect on generation quality**.

---

# 18. The Context Evaluation Record

For production evaluation, I'd capture something like:

```yaml
case_id: RAG-1042

query:
  "Compare the warranty of Product A and Product B"

retrieved_candidates:
  - chunk_17
  - chunk_81
  - chunk_42
  - chunk_93
  - chunk_11

final_context:
  - chunk_17
  - chunk_42
  - chunk_93

required_facts:
  - product_a_duration
  - product_a_conditions
  - product_b_duration
  - product_b_conditions

context_scores:

  relevance: 0.94

  sufficiency: 0.75

  fact_coverage: 0.75

  redundancy: 0.08

  consistency: 1.0

  diversity: 0.91

missing_facts:
  - product_b_conditions

token_count:
  4210

context_budget:
  8000
```

Now your evaluation tells you something actionable.

Instead of:

```text
Context score = 0.82
```

you know:

> Product B's conditions disappeared during context construction.

That is debuggable.

---

# 19. Retrieval vs Context vs Generation

This distinction is worth making explicit.

| Layer      | Core Question                               | Example Failure                                        |
| ---------- | ------------------------------------------- | ------------------------------------------------------ |
| Retrieval  | Did we find the evidence?                   | Correct chunk never retrieved                          |
| Context    | Did we give sufficient evidence to the LLM? | Correct chunk retrieved but removed by context builder |
| Generation | Did the LLM correctly use the evidence?     | Correct context provided but model hallucinated        |

This gives us a very powerful debugging tree.

---

# 20. Diagnosing a Wrong Answer

Suppose answer correctness is low.

First ask:

### Was the necessary evidence retrieved?

No →

```text
Retrieval failure
```

Yes →

### Was the evidence included in final context?

No →

```text
Context construction failure
```

Yes →

### Was the context sufficient and unambiguous?

No →

```text
Context quality failure
```

Yes →

### Did the model correctly use it?

No →

```text
Generation failure
```

That is much more useful than saying:

> "Our RAG accuracy is 74%."

---

# 21. How I Would Build the Context Eval Suite

I would not use one metric.

I'd create a scorecard:

| Metric                    | What it detects                     |
| ------------------------- | ----------------------------------- |
| Context relevance         | Irrelevant evidence                 |
| Context sufficiency       | Missing information                 |
| Fact/evidence coverage    | Missing required claims             |
| Redundancy                | Duplicate information               |
| Diversity                 | Missing sources/aspects             |
| Consistency               | Contradictory evidence              |
| Compression fidelity      | Information lost during compression |
| Context token utilization | Inefficient use of context window   |

And I'd segment these metrics by:

```text
Query type
Difficulty
Domain
Document type
Single-hop vs multi-hop
Language
```

Because averages hide failures.

---

# 22. A More Mature RAG Evaluation Architecture

We can now refine the pyramid we've been building.

```text
                    User Query
                         │
                         ▼
              ┌────────────────────┐
              │    RETRIEVAL       │
              └────────────────────┘
                         │
                   candidates
                         │
                         ▼
              Retrieval Evaluation
              ────────────────────
              Recall@K
              Precision@K
              MRR
              nDCG
              Hit Rate
                         │
                         ▼
              ┌────────────────────┐
              │ CONTEXT BUILDER    │
              └────────────────────┘
                         │
                  final context
                         │
                         ▼
               Context Evaluation
               ──────────────────
               Relevance
               Sufficiency
               Fact Coverage
               Redundancy
               Diversity
               Consistency
               Compression Fidelity
                         │
                         ▼
              ┌────────────────────┐
              │        LLM         │
              └────────────────────┘
                         │
                         ▼
                   Final Answer
```

Now we can isolate exactly where information was lost.

---

# One Subtle Point: Don't Over-Evaluate Every Stage in Production

There is an important engineering trade-off.

I would **not** run expensive LLM judges for every metric on every production request.

Instead, use different evaluation depths.

For offline regression:

```text
Gold Dataset
    ↓
Full retrieval metrics
    +
Full context metrics
    +
Full generation metrics
```

For CI/CD:

```text
Critical Dataset
    ↓
Fast high-confidence metrics
```

For production:

```text
100% traffic
    ↓
Cheap telemetry

+

Sampled traffic
    ↓
Expensive semantic judges
```

For example, perhaps 1–5% of production traces receive full LLM-based context evaluation, while cheap deterministic signals run on every request.

This distinction between **evaluation coverage and evaluation cost** becomes important once RAG systems operate at scale.

---

# The Main Principle

If retrieval evaluation asks:

> **"Did we find the right evidence?"**

context evaluation asks:

> **"Did we transform that evidence into the smallest, sufficient, coherent, non-conflicting information package that gives the LLM everything it needs to answer correctly?"**

That is the real job of the context layer.

And it explains why **retrieval precision alone isn't enough**. You can retrieve 50 relevant chunks and still construct a terrible context.

---

The next layer is **Generation Evaluation**, where the responsibility finally transfers to the LLM. Once we've established that the model received sufficient evidence, we can meaningfully ask whether its answer was **faithful, grounded, correct, complete, relevant, well-cited, and appropriately calibrated when the evidence was insufficient**. This is also where we'll carefully separate concepts that are frequently conflated—particularly **faithfulness vs groundedness vs factual correctness**.
