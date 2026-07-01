# AI Chatbot

A lightweight, fully local AI chatbot powered by **Qwen2-0.5B-Instruct**, served via a **Flask** REST API and a clean browser-based chat interface. No cloud API keys required. All inference runs on your machine.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Roadmap](#roadmap)
- [Troubleshooting](#troubleshooting)

---

## Overview

| Property | Detail |
|---|---|
| **Model** | Qwen/Qwen2-0.5B-Instruct |
| **Backend** | Python 3.10 · Flask · LangChain · Transformers |
| **Frontend** | Vanilla HTML/CSS/JS (no framework) |
| **Inference** | Local CPU (GPU auto-detected if available) |
| **Dependencies** | No external API · No internet required at runtime |

---

## Architecture

```
Browser (index.html)
       │
       │  POST /chat  { "message": "..." }
       ▼
Flask Server (127.0.0.1:5000)
       │
       │  create_qwen_prompt()
       ▼
HuggingFacePipeline (LangChain)
       │
       │  llm.invoke(formatted_prompt)
       ▼
Qwen2-0.5B-Instruct (Transformers)
       │
       │  clean_qwen_response()
       ▼
Flask → JSON { "status": "success", "response": "..." }
       │
       ▼
Browser renders AI reply
```

---

## Prerequisites

- Python **3.10** or higher
- pip **23+**
- ~2 GB free disk space (model cache)
- Internet connection on first run only (to download the model)

---

## Installation

### 1. Clone or download the project

```bash
# If using Git
git clone https://github.com/your-username/qwen-chatbot.git
cd qwen-chatbot

# Or simply create the folder and place the files inside
mkdir qwen-chatbot && cd qwen-chatbot
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

```bash
# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Windows (Command Prompt)
venv\Scripts\activate.bat

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install torch transformers langchain-huggingface langchain-core flask flask-cors requests accelerate
```

> **Note:** `torch` is a large package (~2 GB). Installation may take several minutes depending on your connection speed.

---

## Running the Application

### Step 1 — Start the backend server

```bash
# Windows
& d:\qwen-chatbot\venv\Scripts\python.exe d:/qwen-chatbot/chatbot.py

# macOS / Linux
python chatbot.py
```

Expected output on first run:

```
Loading model: Qwen/Qwen2-0.5B-Instruct...
Device set to use cpu
✅ Environment check passed. LLM found.
🚀 Flask Server started on http://127.0.0.1:5000
✅ Server is ready. Open http://127.0.0.1:5000 in your browser.
   Press Ctrl+C to stop.
```

> The model is downloaded once and cached at `C:\Users\<you>\.cache\huggingface\hub`. Subsequent starts load from cache and are significantly faster.

### Step 2 — Open the chat interface

Navigate to the following URL in your browser:

```
http://127.0.0.1:5000
```

### Step 3 — Stop the server

Press `Ctrl+C` in the terminal at any time.

---

## Project Structure

```
qwen-chatbot/
│
├── chatbot.py          # Flask server + model loading + API routes
├── index.html          # Browser chat interface
├── README.md           # This file
│
└── venv/               # Virtual environment (not committed to version control)
```

---

## Configuration

All configurable values are near the top of `chatbot.py`:

| Variable | Default | Description |
|---|---|---|
| `model_id` | `"Qwen/Qwen2-0.5B-Instruct"` | Hugging Face model identifier |
| `max_new_tokens` | `128` | Maximum tokens the model generates per reply |
| `temperature` | `0.7` | Creativity of responses (0 = deterministic, 1 = creative) |
| `port` | `5000` | Port the Flask server listens on |

To use a different model, change `model_id` to any causal LM available on [huggingface.co/models](https://huggingface.co/models). For example:

```python
model_id = "microsoft/phi-2"
model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
```

---

## API Reference

### `POST /chat`

Send a message to the AI and receive a response.

**Request body**

```json
{
  "message": "What is the capital of France?"
}
```

**Success response** `200 OK`

```json
{
  "status": "success",
  "response": "The capital of France is Paris."
}
```

**Error response** `500 Internal Server Error`

```json
{
  "error": "Error description here"
}
```

---
## Roadmap

The following features are planned for future versions:

- [ ] **Conversation memory** — maintain chat history across turns so the model remembers context
- [ ] **Streaming responses** — render tokens incrementally instead of waiting for the full reply
- [ ] **System prompt editor** — change the AI's persona from the UI at runtime
- [ ] **Multiple chat sessions** — sidebar with named, persistent conversation threads
- [ ] **Model switcher** — select a different model from a dropdown without restarting
- [ ] **Document Q&A (RAG)** — upload a PDF and ask questions about its contents
- [ ] **Voice input** — speak messages using the browser Web Speech API
- [ ] **Export chat** — download any conversation as `.txt`

---


## License

This project is for personal and educational use. The Qwen2 model is subject to the [Qwen License Agreement](https://huggingface.co/Qwen/Qwen2-0.5B-Instruct).

## Author
Mohammad Naeem 

Computer Systems Engineer 
