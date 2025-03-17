# Use official Python image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy all files into container
COPY backend backend
COPY frontend frontend
COPY requirements.txt .
COPY api_key.env .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variable for API key
ENV GOOGLE_API_KEY=$(cat api_key.env | grep GOOGLE_API_KEY | cut -d '=' -f2)

# Expose Streamlit's default port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
