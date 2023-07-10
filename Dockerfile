FROM python:3.10.1-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . .
VOLUME ["/app"]
EXPOSE 8000
CMD ["chainlit", "run", "app.py", "--port", "8000", "--host", "0.0.0.0"]