# streamlit

**Slot**: Quick Python data apps and internal dashboards.

## Why streamlit

Trades configurability for speed. A few decorators and you have a real web app with widgets, charts, file uploads, caching, and authentication-ready forms. Best fit when the consumer is a colleague or yourself — not the public internet.

## Conventions

- One `app.py` at repo root; subviews go in `pages/` (Streamlit's multi-page convention).
- Use `@st.cache_data` for pure data transforms; `@st.cache_resource` for connections / models.
- Settings via [pydantic-settings](../pydantic-settings/) — read once at the top of `app.py`.
- For charts: [altair](../../python-data/altair/) is the default; falling back to `st.line_chart` for one-liners.
- Long-running operations: use `st.status` or `st.spinner` — never block silently.
- Auth-sensitive apps: put Streamlit behind Traefik / oauth2-proxy. Don't roll your own.

## Alternatives considered

- **gradio** — use when the app is an *ML model demo* with chat / image / audio inputs.
- **Dash / Plotly** — heavier; better when you need fine-grained callbacks.
- **FastAPI + a JS frontend** — when you outgrow Streamlit.

## Gotchas

- Streamlit reruns the whole script on every interaction. Cache aggressively; don't do heavy work at module top-level.
- Session state (`st.session_state`) is the escape hatch for "remember this across reruns."
- Don't use it for high-traffic public apps — single worker, single Python process.
- For containerization: `streamlit run --server.headless true --server.port 8501`.
