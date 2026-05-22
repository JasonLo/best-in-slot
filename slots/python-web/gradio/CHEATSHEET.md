# gradio cheatsheet

## Run

```sh
uv add gradio
uv run python app.py   # serves on http://localhost:7860
```

## Single function (Interface)

```python
import gradio as gr

def upper(text: str) -> str:
    return text.upper()

app = gr.Interface(fn=upper, inputs="textbox", outputs="textbox")
if __name__ == "__main__":
    app.launch()
```

## Chat (ChatInterface)

```python
import gradio as gr

def respond(message: str, history: list[tuple[str, str]]) -> str:
    return f"You said: {message}"

app = gr.ChatInterface(fn=respond, title="echo-bot")
if __name__ == "__main__":
    app.launch()
```

## Streaming

```python
import time
import gradio as gr

def slow_echo(message: str, history):
    for i in range(len(message)):
        time.sleep(0.05)
        yield message[: i + 1]

gr.ChatInterface(fn=slow_echo).launch()
```

## Blocks (custom layout)

```python
import gradio as gr

with gr.Blocks(title="my-app") as app:
    gr.Markdown("# my-app")
    with gr.Row():
        inp = gr.Textbox(label="Input")
        out = gr.Textbox(label="Output")
    btn = gr.Button("Run")
    btn.click(fn=str.upper, inputs=inp, outputs=out)

app.launch(server_name="0.0.0.0", server_port=7860)
```
