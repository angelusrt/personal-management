FROM apache/airflow:3.0.2

USER root

RUN apt-get update && \
    apt-get install -y \
    build-essential \
    git && \
    apt-get clean

USER airflow

COPY requirements.txt .

RUN pip install -r requirements.txt
