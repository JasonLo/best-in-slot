import gradio as gr


def respond(message: str, history: list[dict]) -> str:
    return f"You said: {message!r} ({len(message)} chars)"


app = gr.ChatInterface(fn=respond, title="gradio-example")

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
