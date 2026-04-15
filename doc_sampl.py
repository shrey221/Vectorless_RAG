import time
import json
import re
from pageindex import PageIndexClient
import cohere

from dotenv import load_dotenv

# 🔑 Keys
load_dotenv()
PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# 📌 Your saved doc_id (you already have this)
doc_id = "pi-cmnzn67hh0sw601ped58mk43m"

# 🔌 Init clients
pi_client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
co = cohere.Client(COHERE_API_KEY)

# ==============================
# ⏳ Wait until ready (safe check)
# ==============================
while not pi_client.is_retrieval_ready(doc_id):
    print("⏳ Waiting for document...")
    time.sleep(3)

print("✅ Document ready")

# ==============================
# 🌳 Get tree
# ==============================
tree = pi_client.get_tree(doc_id, node_summary=True)["result"]

# ==============================
# ❓ Ask question
# ==============================
query = "What are the key skills and experience in this resume?"

# ==============================
# 🤖 Node selection (Cohere)
# ==============================
prompt = f"""
You are given a hierarchical document tree.

Each node has:
- node_id
- title
- summary

Select the MOST relevant node_ids for answering the question.

Question: {query}

IMPORTANT:
- Always return at least 2 node_ids

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

# Extract JSON
match = re.search(r'\{.*\}', response.text, re.DOTALL)
result = json.loads(match.group())
node_ids = result.get("node_list", [])

print("✅ Selected nodes:", node_ids)

# ==============================
# 📥 Build node map
# ==============================
node_map = {}

def build_map(nodes):
    for n in nodes:
        node_map[n["node_id"]] = n
        if "children" in n:
            build_map(n["children"])

build_map(tree)

# ==============================
# ⚠️ Fallback if empty
# ==============================
if not node_ids:
    print("⚠️ No nodes selected → using fallback")
    node_ids = list(node_map.keys())[:3]

# ==============================
# 📄 Extract context
# ==============================
context = ""
for nid in node_ids:
    if nid in node_map:
        text = node_map[nid].get("text", "")
        if isinstance(text, list):
            text = "\n".join(text)
        context += text + "\n\n"

if not context:
    context = "No relevant content found."

# ==============================
# 🧾 Final answer
# ==============================
final_prompt = f"""
Answer the question using ONLY the context below.

Question: {query}

Context:
{context}
"""

final_response = co.chat(
    model="command-a-03-2025",
    message=final_prompt,
    temperature=0
)

print("\n📌 FINAL ANSWER:\n")
print(final_response.text)