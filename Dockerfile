FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501



# Download data, initialize the database (skips if collection already exists), then start the app
CMD cd data_raw && python download_datasets_quotes.py && python download_datasets_steamGames.py && cd .. \
    cd src && python update_database.py && cd .. && \
    streamlit run app.py --server.address=0.0.0.0 --server.port=8501 \
    --server.headless=true
