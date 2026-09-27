# LeChatV2

Backend for **LeChat**, a LeBron James parody chatbot on my portfolio site ([moloruns.github.io](https://moloruns.github.io)). It is a small Flask API that takes the chat history from the frontend, sends it to OpenAI with a LeBron "persona" system prompt, and returns the bot's reply. It is deployed on Render at [lechatv2.onrender.com](https://lechatv2.onrender.com/).

Try it live: [moloruns.github.io/lebron_chat](https://moloruns.github.io/lebron_chat/)

- **What the backend does**

  One endpoint, `POST /chat`. It takes `{ "messages": [{ "role": "user" | "assistant", "content": "..." }] }`, where the last message is from the user. It keeps the last 10 messages, cuts each to 500 characters, and sends them to OpenAI with the LeBron prompt. It returns `{ "reply": "..." }`, or `{ "error": "..." }` with a 400 for bad input or a 502 if OpenAI fails.

- **How the frontend communicates with the backend**

  The frontend lives in my portfolio on GitHub Pages. Each time the user sends a message, it posts the full chat history to `https://lechatv2.onrender.com/chat`, then shows the `reply` (or the `error`) and adds the reply to its history for the next request.

- **How to set up and run the backend**

  ```bash
  pip install -r requirements.txt
  export OPENAI_API_KEY="sk-..."
  python app.py   # runs on http://localhost:5000
  ```

  `OPENAI_API_KEY` is required. `ALLOWED_ORIGINS` (default `https://moloruns.github.io`) and `OPENAI_MODEL` (default `gpt-4o-mini`) are optional. On Render, the start command is `gunicorn app:app`.

- **How authentication and secrets are handled**

  The OpenAI key is stored only as an environment variable on Render (or in your shell locally). It is never in the code or the frontend, and the frontend never calls OpenAI directly. There's no user login, so CORS restricts browser requests to my site, and the backend limits message length, history length, and reply length to keep costs down.
