# Task 08 - LangChain + RAG + Logical Inference

This task reimplements the Logic-LM pipeline from Task 5 using LangChain, adds RAG for context retrieval, and wires the output into the backward chaining inference engine from Task 7.

## What This Does

The pipeline takes a natural language question and returns a true/false answer with a full deduction trace. It does this in three stages that map directly to the Logic-LM paper:

**Problem Formulator** — A LangChain chain takes the question and relevant KB context retrieved via RAG and translates it into a Prolog query. The chain uses `ChatPromptTemplate` to structure the prompt and pipes it through `gpt-4o-mini` and a `StrOutputParser`.

**Symbolic Reasoner** — The generated Prolog query gets normalized into the engine's string format and passed to the backward chaining engine. Each goal is proved individually with bindings carried forward across compound queries.

**Result Interpreter** — The engine outputs TRUE or FALSE along with a step-by-step deduction trace showing exactly how the answer was reached.

## RAG

The Ghibli knowledge base is embedded into a FAISS vector store using `OpenAIEmbeddings`. When a question comes in, the top 5 most semantically similar facts are retrieved and injected into the LangChain prompt as context. This grounds the LLM in what predicates and entities actually exist in the KB before it generates a query.

## Self-Refiner

After the LLM generates a query, the self-refiner checks whether the predicate exists in the KB. If it doesn't, it sends the error back to the LLM with a list of valid predicates and asks for a revised query. This repeats up to 3 times. If refinement fails, the original query is used as a fallback and the inference engine handles it — returning FALSE if the predicate truly doesn't exist.

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install langchain langchain-openai langchain-community faiss-cpu pyswip python-dotenv
```

Create a `.env` file with your OpenAI key:
```
OPENAI_API_KEY=your-key-here
```

## Running It
```bash
python3 task08.py
```

Example queries to try:

- `Did miyazaki direct spirited away?` — simple fact lookup
- `Who directed ponyo?` — variable binding
- `Does spirited away and ponyo have the same composer?` — compound query
- `Is same_director true for spirited away and ponyo?` — rule-based inference

## Limitations

Rules using operators like `<`, `>=`, `;` (OR), and `\=` (not equal) from `ghibli.pl` were not ported to the Python inference engine since the string-based matcher doesn't support them. Only rules with simple conjunctive bodies were included.