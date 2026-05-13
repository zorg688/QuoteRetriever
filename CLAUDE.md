# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Run commands

Full stack (Qdrant + Ollama + Streamlit + Caddy reverse proxy on port 80):
```bash
docker compose up --build
```

Local dev without Docker (Qdrant still required as a container):
```bash
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 -v "$(pwd)/database:/qdrant/storage" qdrant/qdrant
python -m venv .ragsystem && source .ragsystem/bin/activate
pip install -r requirements.txt
cd data_raw && python download_datasets_quotes.py && python download_datasets_steamGames.py && cd ..
cd src && python update_database.py && cd ..
streamlit run app.py
```

Windows one-shot equivalent: `setup.bat` (creates venv, starts Qdrant container, runs `update_database.py`).

There are no tests, no linter config, no build step beyond the Docker image.

## Architecture

Two-collection RAG over Qdrant. The same code paths serve both collections; the collection name is the routing key.

**Data flow on first boot** (`Dockerfile` `CMD`):
1. `data_raw/download_datasets_quotes.py` and `data_raw/download_datasets_steamGames.py` pull Hugging Face datasets and write `quotes.json` / `steam_games.json` into `data_raw/`.
2. `src/update_database.py` scans `data_raw/` for `*.json`, derives collection names from filenames, and for each collection that does not already exist in Qdrant: creates it with `BAAI/bge-small-en-v1.5` (size from `client.get_embedding_size`), creates payload indexes (different fields per collection — see `initialise_database`), embeds via `fastembed`-backed `models.Document`, and uploads payloads.
3. Streamlit launches `app.py`, which is a two-page nav: `app_page_quotes.py` and `app_page_steam.py`.

**Query path** (`src/infer_from_database.py`):
- `get_unique_types(collection)` is collection-aware — facets on `type` for quotes, `genres` for steam_games. UI uses this to populate the radio filter and to also decide whether to apply a filter at all (the selected value must appear in the facet result, otherwise no filter).
- `get_result(user_query, collection_name, domain)` — passes `models.Document` as the query so embedding happens server-side via Qdrant's fastembed integration; if `user_query is None`, generates a random vector of `client.get_embedding_size(model_name)` dims for the "I am feeling lucky" path.

**LLM path** (Steam page only): `src/generate_answer.py` connects to Ollama (`OLLAMA_HOST` env), pins `qwen3.5:9b`, and **pre-loads the model into GPU memory at module import time** via `client.generate(... keep_alive=-1)`. This blocks app startup until Ollama is reachable and the model is resident. The `docker-compose.yml` `ollama-pull` service exists solely to ensure the model is pulled before the app container starts, gated by `depends_on: ollama-pull: service_completed_successfully`.

**Adding a new collection**: drop a `*.json` file into `data_raw/`, then add the collection-specific branches in:
- `src/update_database.py` `generate_embeddings()` (how to build the embedding text from each row)
- `src/update_database.py` `initialise_database()` `index_names` block (which payload fields to index)
- `src/infer_from_database.py` `get_unique_types()` (which facet key to use)

Otherwise the new collection will be created with no payload indexes and the filter UI will break.

## Environment variables

- `QDRANT_URL` — defaults to `http://localhost:6333`. Set to `http://qdrant:6333` in compose.
- `OLLAMA_HOST` — defaults to `http://localhost:11434`. Set to `http://ollama:11434` in compose.

## Gotchas

- `requirements.txt` includes both CPU and GPU variants of `fastembed` and `onnxruntime` (`fastembed-gpu`, `onnxruntime-gpu`). The GPU wheels are large CUDA builds; they're only useful on hosts with NVIDIA. On CPU-only deploys, removing them shrinks the image substantially.
- `pywin32` is in `requirements.txt` gated by `sys_platform == "win32"` — harmless on macOS/Linux but don't unpin it.
- `data_raw/explorer.py` is a scratch/exploration script, not part of the runtime path.
- `update_database.py` is idempotent at the collection level (`client.collection_exists` check), but is **not** idempotent at the row level — if you change the source JSON you must delete the collection (or the `database/` volume) to re-embed.
- The Steam dataset embed step is the slow part of first boot (minutes on CPU); it runs inside the app container, not Qdrant.
