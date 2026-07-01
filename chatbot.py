import os
import json
import torch
import time
import threading
import requests
import logging
from threading import Thread

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, TextIteratorStreamer
from langchain_huggingface import HuggingFacePipeline
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS

# Suppress verbose warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ── Configuration ────────────────────────────────────────────
model_id        = "Qwen/Qwen2-0.5B-Instruct"
MAX_NEW_TOKENS  = 256
TEMPERATURE     = 0.7
PORT            = 5000
HTML_DIR        = "D:/qwen-chatbot"   # folder where index.html lives

# ── 1. Load Model & Tokenizer ────────────────────────────────
print(f"Loading model: {model_id}...")
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype="auto",
    device_map="auto"
)
print("Model loaded.")

# ── 2. LangChain pipeline (used by non-streaming /chat) ──────
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=MAX_NEW_TOKENS,
    temperature=TEMPERATURE,
)
llm = HuggingFacePipeline(pipeline=pipe)

# ── Environment check ────────────────────────────────────────
if 'llm' not in globals() or 'tokenizer' not in globals():
    raise EnvironmentError("❌ 'llm' or 'tokenizer' not found.")
print("✅ Environment check passed. LLM found.")


# ── Helper functions ─────────────────────────────────────────
def create_qwen_prompt(user_text: str, history: list = None) -> str:
    """
    Build a Qwen-formatted prompt string.
    history: list of {"role": "user"|"assistant", "content": "..."} dicts
    """
    if history is None:
        history = []
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."}
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )


def clean_qwen_response(response: str, prompt: str) -> str:
    """Strip prompt echo and Qwen special tokens from raw output."""
    if prompt in response:
        response = response.replace(prompt, "").strip()
    if "<|im_start|>assistant" in response:
        response = response.split("<|im_start|>assistant")[-1].strip()
    response = response.replace("<|im_end|>", "").strip()
    return response


# ── Flask app ─────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


# ── Routes ────────────────────────────────────────────────────

@app.route('/')
def index():
    """Serve the chat UI."""
    return send_from_directory(HTML_DIR, 'index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """
    Non-streaming endpoint (fallback).
    Body: { "message": str, "history": [ {role, content}, ... ] }
    """
    try:
        data = request.json
        history = data.get('history', [])
        formatted_prompt = create_qwen_prompt(data.get('message', ''), history)
        raw_response = llm.invoke(formatted_prompt)
        ai_response = clean_qwen_response(raw_response, formatted_prompt)
        return jsonify({"status": "success", "response": ai_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    """
    Streaming endpoint using Server-Sent Events.
    Body: { "message": str, "history": [ {role, content}, ... ] }
    Streams: data: {"token": "..."}\n\n  then  data: {"done": true}\n\n
    """
    try:
        data = request.json
        message = data.get('message', '')
        history  = data.get('history', [])

        formatted_prompt = create_qwen_prompt(message, history)
        inputs = tokenizer(formatted_prompt, return_tensors='pt').to(model.device)

        streamer = TextIteratorStreamer(
            tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )

        gen_kwargs = dict(
            **inputs,
            streamer=streamer,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            do_sample=True,
        )

        # Run generation in background thread so we can stream
        t = Thread(target=model.generate, kwargs=gen_kwargs)
        t.start()

        def generate():
            try:
                for token in streamer:
                    # Drop any residual Qwen control tokens
                    token = token.replace("<|im_end|>", "").replace("<|im_start|>", "")
                    if token:
                        yield f"data: {json.dumps({'token': token})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/clear', methods=['POST'])
def clear():
    """Endpoint to acknowledge a history clear (history lives on the client)."""
    return jsonify({"status": "cleared"})


# ── Start server ──────────────────────────────────────────────
def run_flask():
    print(f"🚀 Flask Server started on http://127.0.0.1:{PORT}")
    app.run(port=PORT, use_reloader=False, threaded=True)


t = threading.Thread(target=run_flask)
t.daemon = True
t.start()

print(f"✅ Server is ready. Open http://127.0.0.1:{PORT} in your browser.")
print("   Press Ctrl+C to stop.\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n🛑 Server stopped.")