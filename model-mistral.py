
# ==========================================
# INSTALL
# ==========================================
!pip install flask pyngrok llama-cpp-python huggingface_hub

# ==========================================
# 🔐 CONFIGURATION
# ==========================================
NGROK_TOKEN = "YOUR NGROK TOKEN"
HF_TOKEN = "YOUR HUGGING FACE TOKEN"   # <-- Optional but recommended

MODEL_REPO = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
MODEL_FILE = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"

# ==========================================
# HUGGINGFACE LOGIN (IF TOKEN PROVIDED)
# ==========================================
from huggingface_hub import login

if HF_TOKEN and HF_TOKEN != "":
    login(token=HF_TOKEN)
    print("✅ HuggingFace Authenticated")
else:
    print("⚠️ No HF Token Provided (Public models only)")

# ==========================================
# DOWNLOAD MODEL
# ==========================================
from huggingface_hub import hf_hub_download

model_path = hf_hub_download(
    repo_id=MODEL_REPO,
    filename=MODEL_FILE,
    token=HF_TOKEN if HF_TOKEN else None
)

# ==========================================
# LOAD MODEL (CPU OPTIMIZED)
# ==========================================
from llama_cpp import Llama

llm = Llama(
    model_path=model_path,
    n_ctx=2048,
    n_threads=4,
    n_batch=256,
    verbose=False
)

print("✅ Model Loaded")

# ==========================================
# WEB SERVER
# ==========================================
from flask import Flask, request, jsonify, render_template_string
from pyngrok import ngrok

ngrok.set_auth_token(NGROK_TOKEN)

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Code Generator AI</title>
<style>
body { font-family: Arial; background:#111; color:white; padding:30px;}
textarea { width:100%; height:120px; background:#222; color:#0f0; border:1px solid #444; padding:10px;}
button { padding:10px 20px; background:#0f0; border:none; cursor:pointer;}
pre { background:#000; padding:15px; margin-top:20px; overflow:auto;}
</style>
</head>
<body>

<h2>💻 Code Generator AI (HF Enabled)</h2>

<textarea id="prompt" placeholder="Describe the code you want..."></textarea>
<br><br>
<button onclick="generate()">Generate</button>

<pre id="output"></pre>

<script>
async function generate(){
    let prompt = document.getElementById("prompt").value;
    document.getElementById("output").innerText = "Generating...";
    
    let response = await fetch("/generate", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({prompt: prompt})
    });
    
    let data = await response.json();
    document.getElementById("output").innerText = data.response;
}
</script>

</body>
</html>
"""

# ==========================================
# CODE GENERATOR FUNCTION
# ==========================================
def generate_code(user_prompt):

    system_prompt = """
You are an expert software engineer.

Rules:
- Output ONLY valid code.
- No explanations.
- No markdown.
- Code must be complete and runnable.
"""

    output = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_tokens=700,
        stop=["</s>"]
    )

    return output["choices"][0]["message"]["content"]

# ==========================================
# ROUTES
# ==========================================
@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    user_prompt = data.get("prompt", "")
    result = generate_code(user_prompt)
    return jsonify({"response": result})

# ==========================================
# START SERVER + NGROK
# ==========================================
public_url = ngrok.connect(5000)
print("🌍 Public URL:", public_url)

app.run(port=5000)
