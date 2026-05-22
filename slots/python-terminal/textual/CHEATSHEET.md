# textual cheatsheet

## Run / dev

```sh
uv add textual
uv add --dev "textual[dev]"
uv run textual run --dev mypkg.app:MyApp     # with hot reload
uv run textual console                         # devtools (separate terminal)
```

## Minimal app

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static


class MyApp(App[None]):
    CSS = "Static { padding: 1 2; }"
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Hello, textual!", id="msg")
        yield Button("Press me", id="btn")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn":
            self.query_one("#msg", Static).update("clicked!")


if __name__ == "__main__":
    MyApp().run()
```

## Async work

```python
from textual.worker import work

class MyApp(App[None]):
    @work(exclusive=True)
    async def fetch_data(self) -> None:
        async with httpx.AsyncClient() as c:
            r = await c.get("https://api.example.com/")
            self.query_one("#out", Static).update(r.text)
```

## Test

```python
import pytest
from mypkg.app import MyApp

@pytest.mark.asyncio
async def test_runs():
    async with MyApp().run_test() as pilot:
        await pilot.press("q")
```

## Distribute

```toml
[project.scripts]
myapp = "mypkg.app:run"

# in mypkg/app.py
def run() -> None:
    MyApp().run()
```

```sh
uv tool install git+https://github.com/jasonlo/myapp
```
