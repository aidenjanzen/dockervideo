FROM python:3.10-slim
WORKDIR /app
COPY app.py .
RUN pip install flask
VOLUME ["/data/videos"]
EXPOSE 5000
CMD ["python", "app.py"]
