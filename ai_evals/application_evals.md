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

