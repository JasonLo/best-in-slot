# gradio

**Slot**: Web UI for ML model demos (chat, audio, image, video).

## Why gradio

Built specifically for ML inputs/outputs — drag-and-drop audio, image uploads, chatbot history, streaming generation. Hugging Face Spaces uses it as the default; Qwen / Whisper / TTS demos use it everywhere.

Use gradio when the app *is* a model. Use [streamlit](../streamlit/) when the app is a data view that happens to call a model.

## Conventions

- One `app.py` exposing a `gr.Blocks` or `gr.Interface`, with `if __name__ == "__main__": app.launch()`.
- Use `gr.ChatInterface` for chatbots; `gr.Interface` for one-shot in/out; `gr.Blocks` when you need layout.
- Stream outputs with `yield` — gradio renders progressively.
- Model loading lives behind `@functools.cache` or at module top-level if it has to be eager.
- For Docker, expose `7860` and `app.launch(server_name="0.0.0.0", server_port=7860)`.

## Alternatives considered

- **streamlit** — better for tabular dashboards, worse for media/chat I/O.
- **chainlit** — chat-only, great if that's your entire scope.

## Gotchas

- `app.launch(share=True)` opens a public tunnel via gradio.live. Don't do this with private models / data.
- Type-hinted function parameters drive the input widgets — keep them simple (`str`, `int`, `np.ndarray`).
- For long-running generation, set `concurrency_count` so the UI doesn't queue forever.
