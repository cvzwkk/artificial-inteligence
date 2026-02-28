
# ==========================================
# SETTINGS
# ==========================================
HF_TOKEN = "YOUR HUGGING FACE TOKEN"
NGROK_AUTH_TOKEN = "YOUR NGROK TOKEN"

MODEL_REPO = "bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF"
MODEL_FILE = "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf"

# ==========================================
# INSTALL DEPENDENCIES
# ==========================================
!pip install -q flask pyngrok llama-cpp-python huggingface_hub

# ==========================================
# LOGIN TO HUGGINGFACE
# ==========================================
from huggingface_hub import login, hf_hub_download
login(HF_TOKEN)

# ==========================================
# DOWNLOAD MODEL
# ==========================================
model_path = hf_hub_download(
    repo_id=MODEL_REPO,
    filename=MODEL_FILE
)

print("Model downloaded to:", model_path)

# ==========================================
# LOAD MODEL (CPU OPTIMIZED)
# ==========================================
from llama_cpp import Llama

llm = Llama(
    model_path=model_path,
    n_ctx=2048,
    n_threads=4,      # adjust if needed
    n_batch=256,
    verbose=False
)

print("Model loaded successfully")

# ==========================================
# CREATE WEB APP
# ==========================================
from flask import Flask, request, jsonify, render_template_string
from pyngrok import ngrok

ngrok.set_auth_token(NGROK_AUTH_TOKEN)

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>DeepSeek Chat</title>
<style>
body { font-family: Arial; background: #111; color: white; padding: 20px; }
textarea { width: 100%; height: 100px; }
button { padding: 10px; margin-top: 10px; }
#response { margin-top: 20px; white-space: pre-wrap; }
</style>
</head>
<body>
<h2>DeepSeek Chat (HF Token Version)</h2>
<textarea id="prompt"></textarea><br>
<button onclick="send()">Send</button>
<div id="response"></div>

<script>
async function send() {
    const prompt = document.getElementById("prompt").value;
    document.getElementById("response").innerText = "Generating...";
    const res = await fetch("/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({prompt})
    });
    const data = await res.json();
    document.getElementById("response").innerText = data.response;
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    user_prompt = request.json["prompt"]

    output = llm(
        f"[INST] {user_prompt} [/INST]",
        max_tokens=512,
        temperature=0.7
    )

    return jsonify({"response": output["choices"][0]["text"]})

# ==========================================
# START NGROK
# ==========================================
public_url = ngrok.connect(5000)
print("Public URL:", public_url)

app.run(port=5000)
