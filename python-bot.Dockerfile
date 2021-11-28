FROM python:3
WORKDIR /code
COPY wait-for-it.sh ./
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt ; rm requirements.txt
