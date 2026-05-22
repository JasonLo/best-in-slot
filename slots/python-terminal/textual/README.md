# textual

**Slot**: Full-screen interactive terminal UI (TUI).

## Why textual

Reactive components, async-native, CSS-style theming, and tooling (devtools, headless screenshots) better than the alternatives. The same library that ships `undock` and `uw-s3`.

## Conventions

- `App` subclass in `<pkg>/app.py`; widgets in `<pkg>/widgets/`.
- `def compose(self) -> ComposeResult:` defines the layout.
- Use `@work(thread=True)` for blocking calls, `@work` for async — never block the event loop.
- Log to a file (`logging.basicConfig(filename="myapp.log", ...)`) — stdout is owned by Textual.
- Settings via [pydantic-settings](../../python-web/pydantic-settings/) or [python-dotenv](../../python-web/python-dotenv/).
- Ship as a `uv tool install` target — `[project.scripts]` entry that calls `MyApp().run()`.

## Alternatives considered

- **rich** alone — for static colored output / progress bars, not full-screen UIs. Textual uses rich underneath; if you only need rich, use rich.
- **prompt_toolkit** — older, harder to lay out.
- **urwid** — battle-tested but the API shows its age.

## Embedded / appendix

For ESP32 / CircuitPython terminal output you don't use textual at all — `print()` to the serial console; rich's `Console(force_terminal=True)` if you really must. See `JasonLo/claude-quota-esp32` for the pattern.

## Gotchas

- The dev tools (`textual console` in a second terminal) are essential — wire them up early.
- Use `App.run(headless=True)` + `app.test()` for tests; `pytest-asyncio` with `asyncio_mode = "auto"` is the easiest setup.
- Custom widgets need `compose` *or* `render`, never both.
