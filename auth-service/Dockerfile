FROM python:3.10-slim
WORKDIR /app
COPY app.py .
RUN pip install flask mysql-connector-python
EXPOSE 5000
CMD ["python", "app.py"]
