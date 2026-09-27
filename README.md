# LeChatV2

Backend for **LeChat**, a LeBron James parody chatbot on my portfolio site ([moloruns.github.io](https://moloruns.github.io)). It is a small Flask API that takes the chat history from the frontend, sends it to OpenAI with a LeBron "persona" system prompt, and returns the bot's reply. It is deployed on Render at [lechatv2.onrender.com](https://lechatv2.onrender.com/).

## Endpoints

### `GET /`

Health check. Takes no parameters.

**Response** `200`

```json
{ "status": "ok" }
```

### `POST /chat`

Generates the next chatbot reply.

**Request body** (JSON)

| Field      | Type  | Description |
|------------|-------|-------------|
| `messages` | array | The conversation so far, oldest first. Each item is `{ "role": "user" \| "assistant", "content": "<text>" }`. The last message must be from the user. |

```json
{
  "messages": [
    { "role": "user", "content": "Who's the GOAT?" },
    { "role": "assistant", "content": "You already know, fam 👑" },
    { "role": "user", "content": "How's Philly treating you?" }
  ]
}
```

**What the backend does with it**

- Keeps only the last 10 messages (`MAX_HISTORY`).
- Drops anything that isn't a non-empty `user` or `assistant` message (so the client can't inject its own `system` prompt).
- Cuts each message to 500 characters (`MAX_MESSAGE_CHARS`).
- Adds the LeBron system prompt at the front and calls OpenAI (`gpt-4o-mini` by default, `max_tokens=200`, `temperature=0.8`).

**Responses**

| Status | Body | When |
|--------|------|------|
| `200` | `{ "reply": "<LeBron's response>" }` | Success |
| `400` | `{ "error": "Send a non-empty 'messages' list." }` | `messages` is missing, empty, or not a list |
| `400` | `{ "error": "The last message must be from the user." }` | After cleaning, there are no valid messages or the last one isn't from the user |
| `502` | `{ "error": "The King is taking a timeout. Try again soon." }` | The OpenAI request failed (the details are logged on the server) |

## How the frontend talks to the backend

The frontend lives in my portfolio on GitHub Pages. The backend doesn't store anything, so the frontend keeps the conversation history in the browser.

1. When the user sends a message, the frontend adds `{ role: "user", content: ... }` to its local `messages` array.
2. It sends `POST https://lechatv2.onrender.com/chat` with `Content-Type: application/json` and the body `{ "messages": [...] }`.
3. If the response has a `reply`, the frontend shows it as a chat bubble and adds `{ role: "assistant", content: reply }` to `messages`, so the next request includes the full conversation.
4. If the response has an `error` (a 400 or 502), the frontend shows that message instead.

The frontend can also call `GET /` to check that the server is awake. Render's free tier spins down when idle, so the first request after a while can take a few seconds.

CORS only allows browser requests from the origins in `ALLOWED_ORIGINS` (by default, `https://moloruns.github.io`).

## Running locally

**Requirements:** Python 3.10+ and an OpenAI API key.

```bash
git clone https://github.com/moloruns/LeChatV2.git
cd LeChatV2
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export OPENAI_API_KEY="sk-..."   # required
export ALLOWED_ORIGINS="http://localhost:5500,https://moloruns.github.io"  # optional
python app.py
```

The server runs at `http://localhost:5000`. To test it:

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Yo Bron, what up?"}]}'
```

### Environment variables

| Variable          | Required | Default                      | Purpose |
|-------------------|----------|------------------------------|---------|
| `OPENAI_API_KEY`  | Yes      | none                         | Key used to call the OpenAI API. The app won't start without it. |
| `ALLOWED_ORIGINS` | No       | `https://moloruns.github.io` | Comma-separated list of frontend origins allowed by CORS. Add your local dev server (e.g. `http://localhost:5500`) when testing. |
| `OPENAI_MODEL`    | No       | `gpt-4o-mini`                | OpenAI model to use. |
| `PORT`            | No       | `5000`                       | Port for the local dev server. |

### Deploying (Render)

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`
- Set `OPENAI_API_KEY` (and optionally the other variables) under the service's **Environment** tab.

## Authentication and secrets

- **The OpenAI API key only lives on the backend.** It is read from the `OPENAI_API_KEY` environment variable: locally from your shell, and in production from Render's Environment settings. It is never hard-coded, committed to the repo, or sent to the browser.
- **The frontend never calls OpenAI directly.** It only calls this backend, so anyone viewing the site's source or network traffic can't see the key.
- **There is no user login.** The `/chat` endpoint is public. To limit abuse and keep costs predictable:
  - CORS only allows browsers on the listed origins to call the API. This doesn't stop non-browser clients such as `curl`, but it keeps other websites from using the API.
  - The backend caps the history length, message size, and reply length (`max_tokens`).
  - The system prompt is set on the server, and client-sent `system` messages are dropped.
- If you create a local `.env` file, don't commit it (add it to `.gitignore`).
