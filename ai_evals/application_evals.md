I actually think **application evals are more important than model evals** for someone building GenAI systems.

Here's why.

Suppose tomorrow OpenAI releases GPT-6.

Will your application automatically become better?

**Not necessarily.**

Your retrieval may still retrieve the wrong documents.
Your prompt may still be poorly engineered.
Your tools may still fail.
Your output parser may still break.

The model is only one component.

For companies building GenAI products, **application evals are often more valuable than model evals.**

---

# Part 1: The Shift in Thinking

This is the biggest mental shift you need to make.

## Model Evaluation

In model evals, the object under evaluation is

```text
            GPT-5
               │
               ▼
         Is the model good?
```

The model is the system.

---

## Application Evaluation

In application evals,

the object under evaluation is

```text
                    Application

                          │

      ┌───────────────────┼───────────────────┐

      │                   │                   │

 Retrieval             Prompt             LLM

      │                   │                   │

 Context            Tool Calling       Post-processing

      │                   │                   │

      └───────────────────┼───────────────────┘

                          │

                    User Experience
```

Notice something.

The LLM is now just **one box**.

---

# A Real Example

Imagine you build a RAG system for Ericsson documentation.

A user asks

> Why did Cell X go down?

The application performs

```text
Question

↓

Embedding Model

↓

Vector Search

↓

Top-5 Documents

↓

Prompt Construction

↓

GPT-5

↓

Answer
```

Suppose the answer is wrong.

Whose fault is it?

Could be

* Retrieval
* Embeddings
* Chunking
* Prompt
* LLM
* Missing documentation

Model evaluation cannot answer this.

Application evaluation can.

---

# Why Model Evals Don't Tell the Whole Story

Let's imagine GPT-5 scores

```text
MMLU

95%
```

Your application answers only

```text
Correct Responses

62%
```

How is that possible?

Because

```text
User Question

↓

Retriever returns wrong document

↓

LLM faithfully answers wrong context

↓

Incorrect Answer
```

The model did exactly what it should.

The application failed.

---

# First Principle of Application Evals

Application evaluation asks

> **Can this complete system solve the user's task?**

Notice we no longer care whether

* GPT is smart
* Claude reasons better
* Gemini scores higher

Instead we ask

> **Did the customer get what they needed?**

---

# A Different Measurement Problem

Let's compare.

## Model Eval

Question

↓

Model

↓

Score

---

## Application Eval

Question

↓

Application

↓

User Goal

↓

Was the goal achieved?

This is fundamentally different.

---

# The Unit of Evaluation Changes

This is subtle but incredibly important.

Model evaluation unit

```text
Prompt

↓

Response
```

Application evaluation unit

```text
Entire User Journey
```

Example

User

↓

Upload PDF

↓

OCR

↓

Chunking

↓

Embedding

↓

Retrieval

↓

LLM

↓

Citation Generation

↓

Answer

Every component contributes.

---

# An Analogy

Think about autonomous driving.

Model evaluation

asks

> Can the perception model detect pedestrians?

Application evaluation

asks

> Did the vehicle safely transport the passenger?

Those are very different questions.

---

# The Evaluation Object

Instead of evaluating

```text
f(prompt)

↓

response
```

we now evaluate

```text
Application

↓

Task Completion
```

---

# What Do We Actually Measure?

This is where application evals become much richer.

Instead of one score,

we evaluate multiple dimensions.

```text
                  Application

                        │

      ┌─────────────────┼──────────────────┐

      │                 │                  │

 Retrieval         Generation        User Success

      │                 │                  │

 Performance      Cost           Reliability

      │                 │                  │

      └─────────────────┼──────────────────┘
```

Each branch contains several metrics.

We'll spend the next few modules on each one.

---

# The Five Major Categories of Application Evals

I like to organize application evaluation into five layers.

```text
                Application

                      │

        ┌─────────────┼─────────────┐

        │             │             │

 Functional     Quality        Operational

        │             │             │

 Component      User         Business

        │             │             │

        └─────────────┼─────────────┘
```

Let's understand each.

---

# Layer 1 — Functional Evaluation

Question:

> **Does the application work?**

Example

User uploads PDF.

Does OCR succeed?

Retriever returns documents.

Tool executes.

Database queried.

No crashes.

API returns.

This resembles software testing.

---

# Layer 2 — Component Evaluation

Question

> Which component failed?

Example

```text
Retriever

↓

Returned irrelevant chunks.
```

or

```text
Prompt

↓

Missing system instructions.
```

or

```text
Embedding Model

↓

Poor semantic similarity.
```

Instead of evaluating the entire application,

we isolate individual modules.

---

# Layer 3 — Quality Evaluation

Question

> Was the answer good?

This includes

* correctness
* completeness
* groundedness
* faithfulness
* helpfulness
* clarity
* citation quality

These are often evaluated using human reviewers or LLM-as-a-judge.

---

# Layer 4 — Operational Evaluation

Imagine the application gives perfect answers.

But

* takes 45 seconds
* costs $2 per request
* fails 20% of the time

Would customers be happy?

Probably not.

Operational metrics include:

* latency
* throughput
* token usage
* infrastructure cost
* reliability
* uptime
* timeout rates

---

# Layer 5 — Business Evaluation

Ultimately,

companies care about outcomes.

Examples:

Customer Support

↓

Did ticket resolution improve?

Search

↓

Did users find answers faster?

Sales Assistant

↓

Did conversion increase?

Coding Assistant

↓

Did developers complete tasks more quickly?

Business metrics tie technical performance to product value.

---

# The Evaluation Pyramid

Here's how these layers build on each other.

```text
                  Business Success
                        ▲
                  User Quality
                        ▲
                 Task Completion
                        ▲
               Component Quality
                        ▲
             Infrastructure Health
```

If the bottom layer is weak,

the upper layers suffer.

---

# An Example End-to-End Evaluation

Let's evaluate a document Q&A system.

User asks

> What is the warranty period?

Pipeline

```text
Question

↓

Embedding

↓

Vector Search

↓

Retrieve Top-5

↓

Prompt

↓

LLM

↓

Answer
```

Now imagine the answer is wrong.

Application evaluation investigates:

### Functional

Did retrieval run?

---

### Component

Were the retrieved documents relevant?

---

### Generation

Did the LLM hallucinate?

---

### Operational

How long did it take?

---

### Business

Did the user abandon the chat?

Notice that **one incorrect answer can produce five different evaluation results**, each pointing to a different aspect of the system.

---

# Why Application Evals Are Harder Than Model Evals

Model evals usually evaluate one object.

```text
Model

↓

Score
```

Application evals evaluate interactions.

```text
Retriever

↓

Prompt

↓

LLM

↓

Tool

↓

Memory

↓

Output
```

Failures can emerge from the interactions between components, even if each component performs well in isolation.

---

# A Systems Engineering Perspective

Given your background as a senior ML engineer, I think you'll appreciate this analogy.

Model evaluation is like testing an individual microservice.

Application evaluation is like testing a distributed system.

In distributed systems, you don't just ask:

> "Does Service A work?"

You ask:

* Does Service A interact correctly with Service B?
* What happens when Service C times out?
* Does the retry policy create duplicate requests?
* Can the system recover from partial failures?

Application evaluation asks similar questions for GenAI pipelines.

---

# The Framework We'll Use

Over the next modules, we'll study application evaluation from the inside out.

```text
                    Application

                          │

        ┌─────────────────┼─────────────────┐

        │                 │                 │

   Retrieval         Generation        User Outcome

        │                 │                 │

        ▼                 ▼                 ▼

 Retrieval Evals   Response Evals   Business Evals

        │                 │                 │

        └─────────────────┼─────────────────┘

                    Operational Evals
```

Each of these is a substantial topic on its own.

---

# Where We Should Go Next

There are two ways to proceed:

1. **RAG-first approach**: Start with retrieval evaluation (context precision, context recall, faithfulness, groundedness, answer relevance, etc.). This is the most common type of application evaluation today and introduces many core concepts.

2. **General application evaluation architecture**: First learn how evaluation datasets, LLM judges, rubrics, regression suites, CI/CD integration, and production monitoring are designed for any GenAI application, whether it's RAG, an agent, or a coding assistant.

Given your interest in understanding systems deeply rather than just learning metrics, I recommend the **second approach**. Once you understand the architecture of an evaluation system, RAG evals, agent evals, and tool evals become special cases rather than separate subjects.


I think this is the right direction. In fact, if you understand this architecture well, you'll be able to understand almost every evaluation framework (DeepEval, Ragas, LangSmith, MLflow, Promptfoo, OpenAI Evals, etc.) because **they all implement roughly the same conceptual architecture**.

This is also where AI evaluation starts looking remarkably similar to **software testing**, except the outputs are probabilistic instead of deterministic.

---

# Module 1: The Architecture of an AI Evaluation System

Let's forget about RAG, agents, and copilots for a moment.

Suppose you're building an evaluation platform inside OpenAI.

Your manager asks:

> **Build an evaluation system that can test any AI application.**

Where do you start?

Most people answer:

> "We need some test questions."

That's actually the wrong starting point.

The first question is much deeper.

---

# What is an Evaluation?

Think about unit testing.

A unit test looks like this:

```python
def test_add():
    assert add(2,3) == 5
```

There are four things happening here.

```
Input

↓

System Under Test

↓

Expected Behavior

↓

Comparison
```

Every software test follows this pattern.

---

Now let's translate this into AI.

Suppose your chatbot answers questions.

```
Question

↓

AI Application

↓

Generated Answer

↓

Evaluation
```

Notice something.

Unlike software,

there is often **no single correct answer**.

That changes everything.

---

# The First Big Difference

Software testing:

```
2 + 3

↓

5

↓

Exact Match
```

Easy.

---

GenAI:

```
Summarize this document.
```

Possible outputs:

```
Version A

Version B

Version C

Version D
```

All four may be perfectly acceptable.

Therefore,

AI evaluation **cannot rely on exact matching** in most cases.

---

# The Core Architecture

Every mature AI evaluation platform eventually converges to something like this.

```text
                    Evaluation Platform

                           │

    ┌──────────────────────┼──────────────────────┐

    │                      │                      │

Evaluation Dataset    Application Runner     Evaluators

    │                      │                      │

Ground Truth         Candidate Output      Scoring Logic

    │                      │                      │

    └──────────────────────┼──────────────────────┘

                     Results Database

                           │

                   Dashboards & Reports

                           │

                  Regression Detection
```

This architecture is surprisingly universal.

Let's examine each piece.

---

# Component 1 — Evaluation Dataset

Everything begins with a dataset.

Notice I did **not** say

> Test questions.

Because datasets can contain much more.

An evaluation example might look like:

```yaml
id: 182

input:
   What is the refund policy?

metadata:
   language: English
   customer_type: Premium

expected_behavior:
   Mention 30-day refund.
   Mention receipt requirement.

reference_answer:
   ...

evaluation_type:
   llm_judge
```

This is much richer than

```
Question

↓

Answer
```

---

## Think of Evaluation Cases

Instead of questions,

think in terms of

**evaluation cases**.

An evaluation case defines

* input
* context
* expectations
* scoring strategy

Not every case even has a reference answer.

---

# Component 2 — The Application Runner

This is surprisingly simple.

Its only job is

```
Evaluation Case

↓

Run Application

↓

Capture Output
```

The application runner should behave exactly like production.

That means

* same prompts
* same tools
* same retrieval
* same model
* same middleware

Otherwise,

you're not evaluating what users actually experience.

---

# Component 3 — Evaluators

This is where AI evaluation becomes interesting.

Unlike software,

we need different evaluation strategies.

Imagine three questions.

---

Question 1

```
2+2
```

Evaluation:

```
Exact Match
```

---

Question 2

```
Write an apology email.
```

Evaluation:

```
LLM Judge
```

---

Question 3

```
Generate SQL.
```

Evaluation:

```
Execute SQL
```

Different tasks require different evaluators.

---

# The Evaluator Pattern

A useful abstraction is:

```
Input

+

Output

+

Metadata

↓

Evaluator

↓

Score
```

Notice something.

The evaluator doesn't care

whether the application is

* RAG
* Agent
* Chatbot
* Copilot

It only receives

```
Input

↓

Output

↓

Score
```

This abstraction makes evaluation systems reusable.

---

# Component 4 — Score Aggregation

One response rarely has one score.

Imagine evaluating

```
Summarize document.
```

Possible dimensions:

```
Correctness

Completeness

Groundedness

Conciseness

Tone

Formatting
```

Each becomes an independent evaluator.

```
             Response

                  │

     ┌────────────┼────────────┐

     ▼            ▼            ▼

Correctness   Groundedness   Style

     ▼            ▼            ▼

   0.91         0.97         0.83
```

Now we have a **score vector**, not a single score.

This is analogous to a medical check-up where blood pressure, cholesterol, heart rate, and glucose are all measured separately rather than collapsed into one number.

---

# Component 5 — Storage

Every evaluation result is stored.

Imagine

```
Prompt Version 14

↓

Run 12,000 evaluations

↓

Store Results
```

Later

```
Prompt Version 15

↓

Run Same Dataset

↓

Compare
```

Without historical storage,

regression testing becomes impossible.

---

# Component 6 — Reporting

Now we ask questions like

```
Overall Accuracy?

↓

Which capability regressed?

↓

Which prompt caused it?

↓

Which customer segment failed?

↓

Which evaluator changed?
```

Dashboards emerge naturally.

```
Correctness

█████████

92%

Groundedness

██████████

97%

Latency

██████

3.1 seconds
```

---

# The Evaluation Lifecycle

Putting everything together:

```text
Evaluation Dataset

↓

Application Runner

↓

Generated Outputs

↓

Evaluators

↓

Scores

↓

Database

↓

Dashboards

↓

Regression Detection

↓

Engineers Improve Application

↓

Run Again
```

This loop mirrors continuous integration in software engineering.

---

# The Most Important Design Principle

Here's the biggest conceptual takeaway.

**Separate execution from evaluation.**

Many newcomers design systems like this:

```text
Question

↓

Application

↓

Score Immediately
```

This tightly couples generation and evaluation.

Instead, mature systems do this:

```text
Question

↓

Application

↓

Raw Output

↓

Persist Everything

↓

Evaluate Later

↓

Store Scores
```

Why?

Because evaluation methods evolve.

Today you may score only correctness.

Tomorrow you may add

* hallucination detection
* toxicity
* citation quality

If you've stored the raw outputs, you can re-evaluate historical runs without rerunning the application.

This is exactly the same reason observability systems store logs instead of only aggregate metrics.

---

# Evaluation Is a Pipeline

One of the biggest misconceptions is that evaluation is a single function.

It is better thought of as a pipeline.

```text
Evaluation Dataset
        │
        ▼
Application Execution
        │
        ▼
Trace Collection
        │
        ▼
Evaluation
        │
        ▼
Aggregation
        │
        ▼
Regression Analysis
        │
        ▼
Reporting
```

This architecture is remarkably similar to an ML training pipeline:

```text
Training Data
        │
        ▼
Training
        │
        ▼
Validation
        │
        ▼
Metrics
        │
        ▼
Model Registry
```

The difference is that the "model" being evaluated is now an **entire application**.

---

# Why Every Framework Looks Similar

Let's connect this to real frameworks.

| Component          | DeepEval | Ragas   | LangSmith | MLflow | Promptfoo |
| ------------------ | -------- | ------- | --------- | ------ | --------- |
| Evaluation dataset | ✓        | ✓       | ✓         | ✓      | ✓         |
| Run application    | ✓        | ✓       | ✓         | ✓      | ✓         |
| LLM judge          | ✓        | ✓       | ✓         | ✓      | ✓         |
| Custom evaluators  | ✓        | ✓       | ✓         | ✓      | ✓         |
| Regression testing | ✓        | Partial | ✓         | ✓      | ✓         |
| Dashboards         | Partial  | Partial | ✓         | ✓      | Partial   |

Although their APIs differ, they all implement essentially the same architectural pattern we've just discussed.

---

# Before We Continue

Everything above describes the **skeleton** of an evaluation platform.

Now we need to understand the **organs** inside that skeleton.

There are six major building blocks that every serious evaluation system needs:

```
                    Evaluation Platform

                          │

      ┌───────────────────┼───────────────────┐

      │                   │                   │

 Evaluation Dataset   Evaluators         Regression Suite

      │                   │                   │

  LLM Judges          Rubrics          CI/CD Integration

      │                   │                   │

      └───────────────────┼───────────────────┘

                  Production Monitoring
```

We'll study each in depth.

## The order I recommend

1. **Evaluation datasets** (how to create high-quality evaluation cases)
2. **Rubrics** (what exactly are we measuring?)
3. **LLM-as-a-Judge** (how modern systems score subjective outputs)
4. **Regression suites** (preventing prompt/model regressions)
5. **CI/CD integration** (how evaluations become deployment gates)
6. **Production monitoring** (closing the feedback loop with real users)

This sequence mirrors how many organizations mature their GenAI evaluation practice—from building a static benchmark to operating a continuously improving evaluation platform. I consider the next topic, **evaluation dataset design**, to be the foundation for everything else. A weak dataset cannot be rescued by a sophisticated judge or a polished dashboard.
