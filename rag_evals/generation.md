# Generation Evaluation

## Table of Contents

- [The RAG Responsibility Chain](#the-rag-responsibility-chain)
- [The First Principle of Generation Evaluation](#the-first-principle-of-generation-evaluation)
- [The Generation Evaluation Pyramid](#the-generation-evaluation-pyramid)
- [Running Example](#running-example)
- [Metric 1: Groundedness](#metric-1-groundedness)
- [Metric 2: Faithfulness](#metric-2-faithfulness)
- [Groundedness vs Faithfulness](#groundedness-vs-faithfulness)
- [Metric 3: Correctness](#metric-3-correctness)
- [A Responsibility Matrix](#a-responsibility-matrix)
- [Metric 4: Completeness](#metric-4-completeness)
- [Metric 5: Answer Relevance](#metric-5-answer-relevance)
- [Metric 6: Conciseness](#metric-6-conciseness)
- [Metric 7: Citation Quality](#metric-7-citation-quality)
- [Metric 8: Calibration](#metric-8-calibration)
- [The Generation Evaluation Matrix](#the-generation-evaluation-matrix)
- [How Do We Actually Compute These Metrics?](#how-do-we-actually-compute-these-metrics)
  - [Method 1: Human Evaluation](#method-1-human-evaluation)
  - [Method 2: Rule-Based](#method-2-rule-based)
  - [Method 3: LLM-as-a-Judge](#method-3-llm-as-a-judge)
  - [Method 4: Claim-Based Evaluation](#method-4-claim-based-evaluation-my-preferred-mental-model)
- [The Enterprise Generation Evaluation Trace](#the-enterprise-generation-evaluation-trace)
- [The Generation Responsibility Tree](#the-generation-responsibility-tree)
- [Generation Evaluation Isn't About "Good Writing"](#generation-evaluation-isnt-about-good-writing)
- [Before We Move On](#before-we-move-on)

---

This is probably the **most misunderstood** part of RAG evaluation.

If you read ten blog posts, you'll find terms like Faithfulness, Groundedness, Correctness, Relevance, Hallucination, Factuality, and Completeness. Most of them either define these inconsistently or use them interchangeably.

**They are not the same thing.**

One of the biggest reasons RAG evaluation becomes confusing is because people fail to distinguish **the responsibility of the LLM** from **the responsibility of the retrieval system**.

Let's build a rigorous mental model.

---

## The RAG Responsibility Chain

Think of a RAG system as a contract between components:

```text
Knowledge Base → Retriever → Context Builder → LLM → User
```

Each component has exactly one responsibility:

| Component       | Responsibility                    |
| --------------- | --------------------------------- |
| Knowledge Base  | Store correct knowledge           |
| Retriever       | Find relevant knowledge           |
| Context Builder | Build a usable context            |
| LLM             | Reason correctly from the context |

Notice: the LLM **is not responsible** for retrieving documents, fixing missing context, or dealing with stale documents. The LLM's responsibility begins **after the context is constructed**.

This distinction changes how we evaluate generation.

---

## The First Principle of Generation Evaluation

Generation evaluation asks one question:

> **Given the context the LLM received, did it generate the best possible answer?**

We are **not** asking whether the retrieval was good or the context was complete — those should already have been evaluated.

---

## The Generation Evaluation Pyramid

I organize generation metrics into six layers:

```text
         User Helpfulness
                ▲
         Completeness
                ▲
          Correctness
                ▲
         Faithfulness
                ▲
        Groundedness
                ▲
  Instruction Following
```

We'll examine each carefully.

---

## Running Example

Let's establish one running example used throughout this module.

**User Question:** What is the warranty period?

**Retrieved Context:**

```text
Product Manual

Warranty: 30 days from purchase.
Applies only to manufacturing defects.
```

Now let's evaluate different responses.

---

## Metric 1: Groundedness

Groundedness asks:

> **Can every important claim in the answer be supported by the retrieved context?**

Note the wording — not "Is the answer true?" but "Is it supported?"

**Example A — High Groundedness:**

| Context | Answer | Supported? |
|---------|--------|-----------|
| Warranty = 30 days | "Warranty is 30 days." | Yes ✓ |

**Example B — Lower Groundedness:**

| Context | Answer | Supported? |
|---------|--------|-----------|
| Warranty = 30 days | "Warranty is 30 days. Customers also receive priority support." | Partially — "priority support" has no evidence |

### Important Observation

Groundedness is about `Answer → Evidence`, not `Answer → Reality`. That distinction is critical.

---

## Metric 2: Faithfulness

This is the most famous RAG metric — and the most misunderstood.

Faithfulness asks:

> **Did the model faithfully preserve the meaning of the supplied evidence?**

The difference: Groundedness = "Supported?" / Faithfulness = "Correctly interpreted?"

**Faithful example:**

- Context: "Warranty: 30 days. Only covers manufacturing defects."
- Answer: "Warranty is 30 days for manufacturing defects." ✓

**Unfaithful example:**

- Context: "Warranty: 30 days. Only covers manufacturing defects."
- Answer: "Warranty covers all damages for 30 days." ✗ (distorted the evidence)

**Another critical example:**

- Context: "Employees are NOT eligible for reimbursement."
- Answer: "Employees are eligible for reimbursement."

Everything came from context, yet meaning changed. **Faithfulness = Zero.**

---

## Groundedness vs Faithfulness

This is the distinction most engineers struggle with:

- **Groundedness:** Is there evidence for this claim?
- **Faithfulness:** Did you preserve what the evidence actually says?

**Example:**

- Context: "A causes B."
- Answer: "B causes A."
- Grounded? Somewhat. Faithful? Absolutely not.

Think of it as: Groundedness = Citation. Faithfulness = Correct interpretation.

---

## Metric 3: Correctness

Now we introduce ground truth.

| Question | Reference Answer | LLM Answer | Correct? |
|----------|-----------------|-----------|----------|
| Warranty? | 30 days | 60 days | ✗ |

Now consider an interesting case: the context says "60 days" (outdated), but the reference answer is "30 days."

The LLM says "60 days."

- Faithfulness? High.
- Groundedness? High.
- Correctness? **Wrong.**

Why? The knowledge base was outdated. This is why **Correctness and Faithfulness are different metrics.**

---

## A Responsibility Matrix

| Situation | Grounded | Faithful | Correct |
|-----------|----------|----------|---------|
| Context correct, model copies correctly | ✓ | ✓ | ✓ |
| Context wrong, model copies correctly | ✓ | ✓ | ✗ |
| Context correct, model changes meaning | Partial | ✗ | ✗ |
| Context missing, model hallucinates correctly from prior knowledge | ✗ | ✗ | Maybe ✓ |

The last row surprises many people. If the context contains nothing but GPT already knows the answer, correctness may be high — but groundedness is zero. From a RAG perspective, this is undesirable because the answer did not come from retrieval.

---

## Metric 4: Completeness

**Question:** How do I reset the router?

**Context contains:** Step 1, Step 2, Step 3, Step 4

**Answer:** Step 1, Step 2

Correct? Yes. Complete? **No.**

Completeness asks:

> **Did the answer include all necessary information?**

This is critical for procedures, troubleshooting, legal guidance, compliance, and medical workflows. Missing one step can be catastrophic.

---

## Metric 5: Answer Relevance

This sounds trivial. It isn't.

**Question:** What is OAuth?

**Answer:** "OAuth is an authentication protocol. Our company also has offices in London."

Grounded? Possibly. Relevant? Not fully.

Answer relevance asks: **Did the answer actually solve the user's question?** Not "Did it contain facts."

---

## Metric 6: Conciseness

Often ignored, but important for user experience.

**Question:** Warranty?

**Answer:** (2000 words)

Perfectly correct. Terrible user experience. Sometimes less is better. Measure verbosity relative to information density.

---

## Metric 7: Citation Quality

Enterprise RAG often requires citations. Questions include:

- Did every claim have a citation?
- Did citations point to the correct chunk?
- Did citations exist?
- Were citations hallucinated?

**Example:**

```text
Warranty = 30 days (Source: Policy.pdf, Section 4.2)
```

---

## Metric 8: Calibration

Increasingly important. Suppose the context contains no relevant information, but the LLM answers confidently anyway. That's bad.

Instead, the model should say: "The provided documents do not contain enough information."

Calibration measures whether **confidence matches evidence**. A well-calibrated RAG system knows when **not** to answer.

---

## The Generation Evaluation Matrix

Let's evaluate several responses against the same context:

**Context:** "Warranty = 30 days. Manufacturing defects only."

### Response A: "Warranty is 30 days for manufacturing defects."

| Metric | Score |
|--------|-------|
| Grounded | ✓ |
| Faithful | ✓ |
| Correct | ✓ |
| Complete | ✓ |

### Response B: "Warranty is 90 days."

| Metric | Score |
|--------|-------|
| Grounded | ✗ |
| Faithful | ✗ |
| Correct | ✗ |

### Response C: "Warranty is 30 days."

| Metric | Score |
|--------|-------|
| Grounded | ✓ |
| Faithful | Partial |
| Complete | ✗ |

The restriction (manufacturing defects only) was omitted.

### Response D: "Warranty is 30 days. Priority support included."

| Metric | Score |
|--------|-------|
| Grounded | Partial |
| Faithful | Partial |
| Correct | ✗ |

"Priority support" was hallucinated.

---

## How Do We Actually Compute These Metrics?

There are four broad approaches.

### Method 1: Human Evaluation

Give annotators the Question + Context + Answer. Ask them:
- Is every claim supported?
- Were any claims distorted?
- Did the model invent facts?
- Did it omit critical information?

Highest quality. Not scalable.

### Method 2: Rule-Based

Sometimes possible. Example: SQL generation → Execute → Compare output. Useful but limited.

### Method 3: LLM-as-a-Judge

Now the dominant approach. Prompt a judge with:

```text
Question + Retrieved Context + Generated Answer

Task: Determine whether every factual claim is supported by the retrieved context.

Output: Supported Claims, Unsupported Claims, Overall Faithfulness Score
```

A good judge should perform structured reasoning:

```json
{
  "claims": [
    {
      "claim": "Warranty is 30 days.",
      "supported": true
    },
    {
      "claim": "Priority support included.",
      "supported": false
    }
  ],
  "faithfulness": 0.5
}
```

This is much more reliable than asking "Give a score from 1–10." Modern evaluation frameworks increasingly decompose answers into claims before scoring.

### Method 4: Claim-Based Evaluation (My Preferred Mental Model)

Rather than evaluating the answer as a whole, decompose it into atomic claims.

**Answer:** "Warranty is 30 days. It covers manufacturing defects. Priority support is included."

**Claims extracted:**
- C1: Warranty = 30 days
- C2: Manufacturing defects covered
- C3: Priority support included

Then evaluate each claim independently (Supported? Faithful? Correct? Citation?) and aggregate. This gives far richer diagnostics than a single overall score.

---

## The Enterprise Generation Evaluation Trace

If I were designing an evaluation platform, I'd store:

```yaml
case_id: HR-204
query: "What is the warranty period?"
context: ...
generated_answer: ...

claims:
  - text: "Warranty is 30 days."
    grounded: true
    faithful: true
    correct: true
    citation: chunk18

  - text: "Priority support included."
    grounded: false
    faithful: false
    correct: false
    citation: none

metrics:
  groundedness: 0.50
  faithfulness: 0.50
  correctness: 0.50
  completeness: 0.92
  relevance: 0.98
  calibration: 0.85
```

Notice how much more actionable this is than a single "generation score."

---

## The Generation Responsibility Tree

One of the most useful debugging tools:

```text
Wrong Answer
    │
    ▼
Was evidence retrieved?
    │
    ├── No → Retrieval failure
    │
    ▼ Yes
Was evidence included in context?
    │
    ├── No → Context construction failure
    │
    ▼ Yes
Did the answer faithfully preserve the evidence?
    │
    ├── No → Generation failure
    │
    ▼ Yes
Was the evidence itself correct?
    │
    ├── No → Knowledge base failure
    │
    ▼ Yes
Correct answer ✓
```

This tree prevents one of the biggest mistakes in RAG debugging: blaming the LLM for failures that originated elsewhere.

---

## Generation Evaluation Isn't About "Good Writing"

Many people assume generation evaluation is mostly about fluency or style. In enterprise RAG, that's usually the least important part.

A mature evaluation stack prioritizes:

1. **Groundedness** — Did every claim come from the supplied evidence?
2. **Faithfulness** — Was the evidence interpreted correctly?
3. **Correctness** — Does the answer match reality or the reference answer?
4. **Completeness** — Are all required facts present?
5. **Relevance** — Did it answer the user's question?
6. **Calibration** — Did it appropriately express uncertainty when evidence was insufficient?
7. **Citation quality** — Can users verify important claims?
8. **Clarity and conciseness** — Is the answer usable?

Notice the ordering. It reflects the responsibilities of a RAG generator rather than a generic writing assistant.

---

## Before We Move On

At this point we've covered the three core technical layers of the RAG pipeline:

- **Retrieval Evaluation** — Did we find the right evidence?
- **Context Evaluation** — Did we construct the right evidence package?
- **Generation Evaluation** — Did the LLM reason correctly from that evidence?

The next topic is what ties everything together: **LLM-as-a-Judge**.

This is arguably the most important enabling technology in modern AI evaluation because almost every metric we've discussed—faithfulness, groundedness, completeness, relevance, even some retrieval and context metrics—is increasingly implemented using one or more LLM judges.

We'll go beyond "use GPT-4 as a judge" and study:

- How judges are actually prompted.
- How claims are extracted.
- Pairwise vs rubric-based judging.
- Why judges disagree.
- How to calibrate them against humans.
- How frameworks like **Ragas**, **DeepEval**, and **LangSmith** implement judges internally.
- How to build a production-grade judging pipeline that is reliable enough to gate releases.

Understanding that architecture is what turns these metrics from abstract concepts into implementable systems.


