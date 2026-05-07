FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Initialize the database (skips if collection already exists), then start the app
CMD cd src && python update_database.py && cd .. && \
    streamlit run app.py --server.address=0.0.0.0 --server.port=8501
