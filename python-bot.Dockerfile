FROM python:3
COPY wait-for-it.sh /
WORKDIR /code
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt ; rm requirements.txt
ENTRYPOINT ["/wait-for-it.sh", "vh-db:8529", "--", "python", "-u"]
