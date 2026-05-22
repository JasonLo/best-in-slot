from textual.widgets import Static

from textual_example.app import ExampleApp


async def test_renders_initial() -> None:
    app = ExampleApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert "Hello, textual!" in app.query_one("#msg", Static).content


async def test_button_click() -> None:
    app = ExampleApp()
    async with app.run_test() as pilot:
        await pilot.click("#btn")
        await pilot.pause()
        assert "clicked!" in app.query_one("#msg", Static).content
