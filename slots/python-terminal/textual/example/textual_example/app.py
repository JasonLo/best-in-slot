from textual.app import App, ComposeResult
from textual.widgets import Button, Footer, Header, Static


class ExampleApp(App[None]):
    CSS = "Static { padding: 1 2; } Button { margin: 1 2; }"
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Hello, textual!", id="msg")
        yield Button("Press me", id="btn")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn":
            self.query_one("#msg", Static).update("clicked!")


def run() -> None:
    ExampleApp().run()
