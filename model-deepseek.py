
# ==========================================
# 🔑 SET YOUR NGROK TOKEN
# ==========================================
NGROK_AUTH_TOKEN = "NGROK AUTH KEY"

# ==========================================
# INSTALL DEPENDENCIES
# ==========================================
!apt-get -qq install -y git build-essential cmake
!pip install -q flask pyngrok llama-cpp-python

# ==========================================
# BUILD LLAMA.CPP WITH CPU OPTIMIZATION
# ==========================================
!CMAKE_ARGS="-DLLAMA_AVX2=ON" pip install llama-cpp-python --force-reinstall --no-cache-dir

# ==========================================
# DOWNLOAD DEEPSEEK GGUF (QUANTIZED)
# ==========================================
!wget -q https://huggingface.co/TheBloke/deepseek-llm-6.7b-chat-GGUF/resolve/main/deepseek-llm-6.7b-chat.Q4_K_M.gguf -O model.gguf

# ==========================================
# IMPORTS
# ==========================================
from llama_cpp import Llama
from flask import Flask, request, jsonify, render_template_string
from pyngrok import ngrok
import threading

ngrok.set_auth_token(NGROK_AUTH_TOKEN)

# ==========================================
# LOAD MODEL (LOW RAM FAST CPU MODE)
# ==========================================
llm = Llama(
    model_path="model.gguf",
    n_ctx=2048,
    n_threads=4,      # CPU threads (increase if needed)
    n_batch=128
)

# ==========================================
# FLASK APP
# ==========================================
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>DeepSeek CPU Chat</title>
<style>
body{background:#202123;color:white;font-family:Arial;display:flex;justify-content:center;}
.container{width:70%;margin-top:30px;}
.chatbox{background:#343541;padding:20px;border-radius:10px;height:500px;overflow-y:auto;}
.user{color:#4CAF50;margin:10px 0;}
.ai{color:#00BCD4;margin:10px 0;}
input{width:80%;padding:10px;border-radius:5px;border:none;}
button{padding:10px;border-radius:5px;border:none;background:#10A37F;color:white;}
</style>
</head>
<body>
<div class="container">
<h2>🚀 DeepSeek CPU AI (Fast Mode)</h2>
<div class="chatbox" id="chatbox"></div><br>
<input type="text" id="msg" placeholder="Type message...">
<button onclick="send()">Send</button>
</div>
<script>
async function send(){
let input=document.getElementById("msg");
let message=input.value;
if(!message)return;
let box=document.getElementById("chatbox");
box.innerHTML+="<div class='user'><b>You:</b> "+message+"</div>";
input.value="";
let res=await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:message})});
let data=await res.json();
box.innerHTML+="<div class='ai'><b>AI:</b> "+data.response+"</div>";
box.scrollTop=box.scrollHeight;
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return HTML

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json["message"]

    output = llm(
        f"[INST] {user_input} [/INST]",
        max_tokens=200,
        temperature=0.6,
        top_p=0.9
    )

    response = output["choices"][0]["text"]
    return jsonify({"response": response})

# ==========================================
# START SERVER + NGROK
# ==========================================
def run():
    app.run(port=5000)

threading.Thread(target=run).start()

public_url = ngrok.connect(5000)
print("🌍 Public URL:", public_url)
