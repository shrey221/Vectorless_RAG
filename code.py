import time
import json
import re
from dotenv import load_dotenv
import os
from pageindex import PageIndexClient
import cohere
load_dotenv()
PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
print("Hi i m shrey")
PDF_PATH = "Christ.pdf"

pi_client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
co = cohere.Client(COHERE_API_KEY)
print("Shrey")
print("My name is shrey ")

resp = pi_client.submit_document(PDF_PATH)
doc_id = resp["doc_id"]

print("📄 Uploaded doc_id:", doc_id)

while not pi_client.is_retrieval_ready(doc_id):
    print("⏳ Processing...")
    time.sleep(5)

print("✅ Tree ready")

tree = pi_client.get_tree(doc_id, node_summary=True)["result"]

query = "Where am i working and what teachers helped in this project?"

prompt = f"""
You are given a document tree.

Each node contains:
- id
- title
- summary

Task:
Find the most relevant nodes for answering the question.

Question: {query}

Tree:
{json.dumps(tree)[:4000]}

Return ONLY JSON:
{{
  "node_list": ["node_id_1", "node_id_2"]
}}
"""

response = co.chat(
    model="command-a-03-2025",
    message=prompt,
    temperature=0
)

print("\n🔍 Raw response:\n", response.text)

# Extract JSON safely
match = re.search(r'\{.*\}', response.text, re.DOTALL)
if not match:
    raise Exception("❌ JSON parsing failed")

result = json.loads(match.group())
node_ids = result.get("node_list", [])

print("✅ Selected nodes:", node_ids)

node_map = {}

def build_map(nodes):
    for n in nodes:
        node_map[n["node_id"]] = n
        if "children" in n:
            build_map(n["children"])

build_map(tree)

context = ""
for nid in node_ids:
    if nid in node_map:
        text = node_map[nid].get("text", "")
        if isinstance(text, list):
            text = "\n".join(text)
        context += text + "\n\n"

if not context:
    context = "No relevant content found."

final_prompt = f"""
Answer the question using ONLY the context below.

Question: {query}

Context:
{context}

Give a clear and concise answer.
"""

final_response = co.chat(
    model="command-a-03-2025",
    message=final_prompt,
    temperature=0
)

print("\n📌 FINAL ANSWER:\n")
print(final_response.text)