# PRD vs HLD vs LLD — A Simple Guide

## The One-Line Summary

| Document | Answers | Audience |
|----------|---------|----------|
| **PRD** | **What** are we building and **why**? | Product, business, stakeholders |
| **HLD** | **How** will we build it (big picture)? | Architects, tech leads, senior engineers |
| **LLD** | **How exactly** will we build it (details)? | Developers who write the code |

---

## The Analogy: Building a House

Think of building a house:

| Document | House Equivalent | What It Contains |
|----------|-----------------|------------------|
| **PRD** | The family's wish list | "We need 3 bedrooms, a garden, modern kitchen, budget is $300K, must be done in 6 months" |
| **HLD** | The architect's blueprint | Floor plan, which floor has what, plumbing and electrical routing, materials chosen |
| **LLD** | The contractor's construction drawings | Exact wiring diagrams, pipe dimensions, bolt specifications, step-by-step build sequence |

The family (stakeholders) never reads the wiring diagram. The electrician (developer) doesn't care about why the family wanted 3 bedrooms. Each document serves a different audience at a different level.

---

## Example Scenario: AI-Powered Customer Support Chatbot

Let's say your manager asks: *"We want to build an AI chatbot that answers customer questions using our help documentation."*

Here's what each document would contain:

---

### PRD — The Product Perspective

**Core question:** What problem are we solving, for whom, and how will we know it worked?

```
PROBLEM:
Customers wait 4 hours for support replies. 60% of questions
are repetitive and already answered in our docs.

USERS:
Customers on our website (non-technical, English-speaking).

WHAT WE NEED:
- Chatbot on the website that answers product questions
- Uses our existing help documentation as source
- Shows source links so users can verify
- Says "I don't know" instead of making things up
- Responds in under 5 seconds

SUCCESS METRIC:
- Resolves 70%+ of Tier-1 tickets without human
- Customer satisfaction > 4.0/5
- Accuracy > 85% on test queries

OUT OF SCOPE:
- Multi-language support
- Voice interface
- Order management / transactions

TIMELINE: POC in 3 weeks, production in 3 months
```

**Notice:** Zero mention of LLMs, vector databases, embeddings, or architecture. The PRD doesn't care about technology — it cares about the user problem and measurable outcomes.

---

### HLD — The Architecture Perspective

**Core question:** What components do we need, how do they connect, and what technology choices are we making?

```
APPROACH:
RAG (Retrieval Augmented Generation) over help documentation.

ARCHITECTURE:
┌─────────┐     ┌──────────┐     ┌─────────┐     ┌─────────┐
│ Website │ ──► │ API Layer│ ──► │Retriever│ ──► │  LLM    │
│ Widget  │     │ (FastAPI)│     │(Qdrant) │     │(GPT-4o) │
└─────────┘     └──────────┘     └─────────┘     └─────────┘
                                       ▲
                                       │
                               ┌───────────────┐
                               │ Help Docs     │
                               │ (Embedded +   │
                               │  Indexed)     │
                               └───────────────┘

COMPONENTS:
- Document ingestion pipeline (weekly batch)
- Vector store (Qdrant, cosine similarity)
- Retrieval + Reranking
- LLM generation with grounding
- Web chat widget

DATA FLOW:
User question → Embed → Retrieve top-5 docs → Build prompt → LLM → Response

KEY DECISIONS:
- GPT-4o (best quality for POC, evaluate cost later)
- Qdrant (open-source, easy local setup)
- Chunk size: 512 tokens with 50 token overlap

EVALUATION STRATEGY:
- 100 test questions with expert answers
- Measure: correctness, faithfulness, latency
- Regression gate in CI/CD

ESTIMATED COST: ~$0.03 per query
```

**Notice:** No code, no function signatures, no exact prompts. But a developer can look at this and understand *what* they need to build without ambiguity about *which* technologies to use.

---

### LLD — The Implementation Perspective

**Core question:** How exactly do I write this code? What are the data structures, functions, prompts, and configs?

```
PROJECT STRUCTURE:
chatbot/
├── src/
│   ├── ingestion/
│   │   ├── loader.py        # Reads help docs from CMS API
│   │   ├── chunker.py       # Splits into 512-token chunks
│   │   └── indexer.py       # Embeds + stores in Qdrant
│   ├── pipeline/
│   │   ├── retriever.py     # Queries Qdrant, top-5
│   │   ├── reranker.py      # Cohere rerank
│   │   └── generator.py     # Prompt assembly + LLM call
│   └── api/
│       └── routes.py        # FastAPI endpoints
├── prompts/
│   └── answer_v1.txt        # Exact prompt template
└── configs/
    └── config.yaml          # All parameters

EXACT PROMPT:
"""
You are a helpful customer support assistant for [Company].
Answer the user's question using ONLY the provided context.
If the context doesn't contain the answer, say "I don't have
information about that. Please contact support@company.com."

Context:
{context}

Question: {query}

Instructions:
- Be concise (2-3 sentences unless procedure)
- Cite sources as [Source: document_name]
- Never invent information
"""

SCHEMAS:
class QueryRequest:
    query: str
    session_id: str

class QueryResponse:
    answer: str
    sources: List[Source]
    confidence: float
    latency_ms: int

class Source:
    title: str
    url: str
    chunk_id: str
    relevance_score: float

QDRANT COLLECTION CONFIG:
    name: "help_docs"
    vector_size: 1536
    distance: "Cosine"
    payload_fields: [title, url, section, last_updated]

KEY FUNCTION:
def run_query(query: str) -> QueryResponse:
    embedding = openai.embed(query, model="text-embedding-3-small")
    chunks = qdrant.search(embedding, limit=5, score_threshold=0.75)
    
    if not chunks:
        return QueryResponse(answer="I don't have information...")
    
    context = format_chunks(chunks)
    prompt = render_template("answer_v1.txt", context=context, query=query)
    response = openai.chat(model="gpt-4o", messages=[...], temperature=0.1)
    sources = extract_sources(chunks)
    
    return QueryResponse(answer=response, sources=sources, ...)
```

**Notice:** A developer can literally start coding from this. Exact prompts, exact schemas, exact parameters, exact function logic. No ambiguity.

---

## Side-by-Side Comparison

| Aspect | PRD | HLD | LLD |
|--------|-----|-----|-----|
| **Audience** | PM, stakeholders, business | Architects, tech leads | Developers |
| **Language** | Business language, user stories | Technical but high-level | Code-adjacent, schemas, configs |
| **Diagrams** | User journeys, flows | Architecture boxes, data flows | Sequence diagrams, class diagrams |
| **Technology mentions** | None or minimal | Major choices (GPT-4o, Qdrant) | Exact versions, configs, params |
| **Level of detail** | What + Why | How (structural) | How (procedural) |
| **Length** | 3-8 pages | 8-15 pages | 10-30 pages |
| **Changes when...** | Requirements change | Architecture changes | Implementation changes |
| **Answers** | "Should we build this?" | "Can we build this?" | "How do I build this?" |

---

## The Flow: How They Connect

```text
PRD                          HLD                          LLD
───                          ───                          ───
"We need a chatbot           "We'll use RAG with          "The prompt is: '...'
 that resolves 70%    ──►     Qdrant + GPT-4o,     ──►    The function signature
 of tickets with              5 components,                is run_query(str) →
 >85% accuracy"              evaluated on 100              Response, Qdrant
                              test cases"                   collection config
                                                           is {...}"
```

**The rule of thumb:**
- If a **business person** wouldn't understand it → it doesn't belong in the PRD
- If a **developer** needs more detail to start coding → it's HLD, not LLD
- If you're specifying **exact code logic** → that's LLD

---

## Common Mistakes

| Mistake | Why It's Bad | Fix |
|---------|-------------|-----|
| PRD includes technology choices | Constrains solutions too early | State requirements, not implementation |
| HLD has no technology decisions | Developers can't start without knowing the stack | Make clear choices, justify them |
| LLD is just code | Loses the "why" behind decisions | Include rationale for non-obvious choices |
| Writing LLD without HLD | Coding without an agreed architecture | Always align on HLD first |
| PRD has vague success criteria | No way to know if you succeeded | Use numbers: "> 85%", "< 3 seconds" |
| All three written by one person | No cross-functional input | PM owns PRD, architect owns HLD, dev owns LLD |

---

## When Someone Asks You to Write One

### "Write a PRD"

They want:
- Clear problem statement with impact
- Who the user is and what they need
- Measurable success criteria
- Scope boundaries (in/out)
- Timeline and constraints

They do NOT want: Architecture diagrams, code, model choices.

### "Write an HLD"

They want:
- Component architecture with diagram
- Technology selections with justification
- Data flow end-to-end
- Key design decisions and trade-offs
- Evaluation and operational strategy

They do NOT want: Function signatures, exact prompts, config files.

### "Write an LLD"

They want:
- Project structure and file layout
- Exact schemas, interfaces, and data models
- Algorithm pseudocode and decision logic
- Configuration values and environment setup
- Step-by-step implementation plan anyone can follow

They do NOT want: Business justification, user stories, high-level architecture (reference the HLD).

---

## Quick Template Selection Guide

| Situation | Start With |
|-----------|-----------|
| "I have an idea for an AI feature" | PRD |
| "PRD is approved, how do we architect this?" | HLD |
| "Architecture is agreed, how do I implement?" | LLD |
| "Let's do a quick POC" | Lightweight PRD → POC HLD → POC LLD |
| "Explain this to executives" | PRD only |
| "New developer joining mid-project" | HLD + LLD |
