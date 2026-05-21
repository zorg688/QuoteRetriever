# QuoteRetriever

A vector search-based retriever of quotes from movies, tv shows, authors and comedians. Uses Qdrant for storing and embedding via fastembed. The app uses a streamlit UI for easy interaction in a web window. The code for this project was written without the involvement of AI, Claude Code was used for the batch file as well as Dockerfile setup.

This project was created while working under Metacore Games Oy and is a personal learning project with the goal to understand RAG pipelinesas well as interaction with the database

## Prerequisites

- [Docker](https://www.docker.com/get-started/) installed and running
- Python 3.12+ (only needed for local development)

## Docker Compose (recommended)

Runs both Qdrant and the Streamlit app in containers. The app is accessible to anyone on your local network.

```bash
docker compose up --build
```

The app will be available at `http://localhost:8501`. Other devices on the same network can reach it at `http://<your-ip>:8501`.

To run in the background:

```bash
docker compose up --build -d
```

To stop:

```bash
docker compose down
```

## Quick setup for local development (Windows)

Run the setup script to check prerequisites, create the venv, start Qdrant, and initialize the database in one step:

```bat
setup.bat
```

## Manual setup

### 1. Start Qdrant via Docker

This project uses a Dockerized Qdrant instance as its vector database. No local Qdrant installation is needed.

```bash
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

To persist data across container restarts, mount a volume:

```bash
docker run -d --name qdrant \
  -p 6333:6333 -p 6334:6334 \
  -v "$(pwd)/database:/qdrant/storage" \
  qdrant/qdrant
```

Verify Qdrant is running by visiting [http://localhost:6333/dashboard](http://localhost:6333/dashboard).

### 2. Install Python dependencies

```bash
python -m venv .ragsystem
# Windows
.ragsystem\Scripts\activate
# Linux/macOS
source .ragsystem/bin/activate

pip install -r requirements.txt
```

### 3. Initialize the database

On first run, this loads `data_raw/quotes.json` into Qdrant and creates the necessary payload indexes:

```bash
cd src
python update_database.py
```

## Usage

### Streamlit app

```bash
streamlit run app.py
```

### CLI

```bash
cd src
python infer_from_database.py
```

## Project structure

```
.
├── Dockerfile              # App container image
├── docker-compose.yml      # Orchestrates app + Qdrant containers
├── setup.bat               # Automated local setup script (Windows)
├── app.py                  # Streamlit web interface
├── data_raw/
│   └── quotes.json         # Raw quote data (movie, tv show, author, philosopher, anime)
├── database/               # Qdrant storage (Docker volume mount)
└── src/
    ├── update_database.py  # Database initialization and payload updates
    └── infer_from_database.py  # Query and retrieval logic
```

## Notes

- Qdrant **must** be running via Docker before starting the app or running any scripts. The Qdrant URL defaults to `http://localhost:6333` and can be overridden with the `QDRANT_URL` environment variable (set automatically by Docker Compose).
- The embedding model used is `BAAI/bge-small-en-v1.5` (downloaded automatically by fastembed on first use).
- If you need to recreate the collection, stop the container and remove the volume, then re-run `update_database.py`.
