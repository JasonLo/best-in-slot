# streamlit example

```sh
uv sync
uv run streamlit run app.py
# open http://localhost:8501
```

Headless smoke test:

```sh
uv run streamlit run app.py --server.headless true --server.port 8501 &
sleep 5
curl -sf http://localhost:8501/_stcore/health
kill %1
```
