import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)

# Only let your GitHub Pages site call this API from a browser.
# Add "http://localhost:5500" (or similar) here while testing locally.
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "https://moloruns.github.io"
).split(",")
CORS(app, origins=ALLOWED_ORIGINS)

# Set OPENAI_API_KEY in Render's dashboard (Environment tab), never in code.
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = (
    "You are an AI parody of LeBron James, the NBA superstar, chatting with "
    "visitors on Micheal Olorunsola's portfolio website. Speak in LeBron's "
    "confident, upbeat, team-first voice. Talk about basketball, leadership, "
    "hard work, family, and your career (Akron, Miami, Cleveland, the Lakers). "
    "Keep replies short (2-4 sentences). If asked, be clear that you are an AI "
    "and not the real LeBron James. Stay friendly and family-appropriate."
)

# Limits to keep API costs predictable.
MAX_HISTORY = 10          # how many past messages are sent to OpenAI
MAX_MESSAGE_CHARS = 500   # max length of any single user message


@app.get("/")
def health():
    return jsonify(status="ok")


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    history = data.get("messages", [])

    if not isinstance(history, list) or not history:
        return jsonify(error="Send a non-empty 'messages' list."), 400

    # Only keep well-formed user/assistant messages, trimmed to size.
    cleaned = []
    for msg in history[-MAX_HISTORY:]:
        role = msg.get("role") if isinstance(msg, dict) else None
        content = msg.get("content") if isinstance(msg, dict) else None
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            cleaned.append({"role": role, "content": content[:MAX_MESSAGE_CHARS]})

    if not cleaned or cleaned[-1]["role"] != "user":
        return jsonify(error="The last message must be from the user."), 400

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + cleaned,
            max_tokens=200,
            temperature=0.8,
        )
        reply = completion.choices[0].message.content
    except Exception as e:
        app.logger.exception("OpenAI request failed: %s", e)
        return jsonify(error="The King is taking a timeout. Try again soon."), 502

    return jsonify(reply=reply)


if __name__ == "__main__":
    # Local development only; Render runs this with gunicorn.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
