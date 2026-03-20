import os
import json
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

load_dotenv()

# Load each line of the KB as a LangChain Document for embedding
def load_kb(path):
    with open(path, "r") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("%")]
    docs = [Document(page_content=line) for line in lines]
    return docs

# Embed KB documents into a FAISS vector store for RAG retrieval
def build_vector_store(docs):
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(docs, embeddings)
    return vector_store

# Retrieve the k most relevant facts from the vector store for a given query
def retrieve_context(vector_store, query, k=5):
    results = vector_store.similarity_search(query, k=k)
    context = "\n".join([doc.page_content for doc in results])
    return context

# Build a LangChain that translates natural lang to a Prolog query
def build_chain():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a logic assistant. Given a Prolog knowledge base context and a natural language question, generate a Prolog query to answer it.
        
Respond in this exact JSON format:
{{
    "query": "prolog_predicate(arg1, arg2)",
    "variables": ["Var1", "Var2"]
}}

If the question is a yes/no question with no variables, use an empty list for variables.
Only use facts and predicates that exist in the provided context."""),
        ("human", "Context:\n{context}\n\nQuestion: {question}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    return chain

# Parse Prolog facts into the engine's string format (skip rules and coments)
def parse_prolog_facts(path):
    facts = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("%") or ":-" in line:
                continue
            if not line[0].islower():
                continue
            line = line.rstrip(".")
            line = line.replace(",", "").replace("(", " ").replace(")", "")
            facts.append(line)
    return facts

# Match a pattern against a fact, returning variable bindings or None
def match(pattern, fact):
    name_dict = {}
    fact_list = fact.split(" ")
    pattern_list = pattern.split(" ")

    if len(fact_list) != len(pattern_list):
        return None
    
    for i in range(len(pattern_list)):
        if "(?" in pattern_list[i]:
            name = pattern_list[i][2:-1]
            name_dict[name] = fact_list[i]
            continue
        elif fact_list[i] != pattern_list[i]:
            return None
    
    return name_dict

# Backward chain from a goal, recording each step in a trace
def backward_chain_trace(goal, rules, facts, trace=None):
    if trace is None:
        trace = []

    trace.append(f"Trying to prove: {goal}")

    for fact in facts:
        bindings = match(goal, fact)
        if bindings is not None:
            trace.append(f"Matched fact: {fact}")
            return bindings, trace

    for rule in rules:
        head, body = rule
        bindings = match(head, goal)
        if bindings is not None:
            trace.append(f"Matched rule head: {head}")
            for condition in body:
                subcondition = substitute(condition, bindings)
                result, trace = backward_chain_trace(subcondition, rules, facts, trace)
                if result is None:
                    trace.append(f"Failed to prove: {subcondition}")
                    break
                bindings.update(result)
            else:
                return bindings, trace

    trace.append(f"Could not prove: {goal}")
    return None, trace

def substitute(pattern, bindings):
    for var, val in bindings.items():
        pattern = pattern.replace(f"(?{var})", val)
    return pattern

def self_refine(chain, context, question, prolog_query, facts, rules, max_attempts=3):
    attempt = 0
    current_query = prolog_query

    while attempt < max_attempts:
        # Check if the predicate exists in facts or rules
        predicate = current_query.split("(")[0].strip()
        fact_predicates = set(f.split()[0] for f in facts)
        rule_predicates = set(r[0].split()[0] for r in rules if r[0].split()[0].islower())

        if predicate in fact_predicates or predicate in rule_predicates:
            return current_query  # query looks valid, move on

        # Predicate not found, ask LLM to fix it
        error_msg = f"The predicate '{predicate}' does not exist in the knowledge base. Available predicates are: {fact_predicates | rule_predicates}"
        print(f"\n[Self-Refiner] Attempt {attempt + 1}: {error_msg}")

        raw = chain.invoke({
            "context": context,
            "question": f"Previous query was invalid. {error_msg}. Original question: {question}"
        })
        parsed = json.loads(raw)
        current_query = parsed["query"]

        if not current_query or not parsed.get("query"):
            print("[Self-Refiner] LLM returned empty query, stopping refinement.")
            break

        current_query = parsed["query"]
        print(f"[Self-Refiner] Revised query: {current_query}")
        attempt += 1

    return prolog_query  # fall back to original if refinement failed  # return best attempt after max retries

# Convert Prolog-style variables (capitalized) to the engine format (?Var)
def convert_variables(query):
    tokens = query.split()
    converted = []
    for token in tokens:
        if re.match(r'^[A-Z][a-zA-Z0-9_]*$', token):
            converted.append(f"(?{token})")
        else:
            converted.append(token)
    return " ".join(converted)

# Split a compound Prolog query on top-level commas only
def split_goals(query):
    goals = []
    depth = 0
    current = ""
    for char in query:
        if char == "(":
            depth += 1
            current += char
        elif char == ")":
            depth -= 1
            current += char
        elif char == "," and depth == 0:
            goals.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        goals.append(current.strip())
    return goals

def main():
    docs = load_kb("ghibli.pl")
    vector_store = build_vector_store(docs)
    chain = build_chain()
    facts = parse_prolog_facts("ghibli.pl")

    # Python rules ported from ghibli.pl (operators like < and ; are unsupported)
    rules = [
        ("same_director (?X) (?Y)", ["director (?X) (?Director)", "director (?Y) (?Director)"]),
        ("same_composer (?X) (?Y)", ["composer (?X) (?Composer)", "composer (?Y) (?Composer)"]),
        ("by_director (?X) (?Director)", ["director (?X) (?Director)"]),
        ("recommend_by_genre (?X) (?Genre)", ["movie (?X) (?Genre) (?Year)"]),
    ]

    query = input("Enter your question: ")

    # Retrieve relevant KB context and generate a Prolog query via LangChain
    context = retrieve_context(vector_store, query)
    raw = chain.invoke({"context": context, "question": query})
    parsed = json.loads(raw)
    prolog_query = parsed["query"]
    
    print(f"\nGenerated Prolog query: {prolog_query}")
    prolog_query = self_refine(chain, context, query, prolog_query, facts, rules)

    # Split compound queries and change to engine format
    goals_raw = split_goals(prolog_query.rstrip("."))
    goals_clean = []
    for goal in goals_raw:
        g = goal.replace("(", " ").replace(")", "").replace(",", "").strip()
        g = convert_variables(g)
        goals_clean.append(g)

    # Prove each goal, carrying bindings forward across goals
    all_bindings = {}
    full_trace = []
    result = True

    for goal in goals_clean:
        substituted_goal = substitute(goal, all_bindings)
        bindings, trace = backward_chain_trace(substituted_goal, rules, facts)
        full_trace.extend(trace)
        if bindings is None:
            result = False
            break
        all_bindings.update(bindings)

    print("\nTrace:")
    for step in full_trace:
        print(f"  {step}")

    if result:
        print(f"\nResult: TRUE")
        print(f"Bindings: {all_bindings}")
    else:
        print(f"\nResult: FALSE")

if __name__ == "__main__":
    main()