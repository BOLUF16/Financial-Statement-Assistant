FROM python:3.11.9

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip3 install --timeout 900 --cache-dir=/var/tmp/ torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu && \
    pip3 install --no-cache-dir -r requirements.txt && \
    apt-get update -y --no-install-recommends

COPY . /app

EXPOSE 5000

RUN ls -la /app/

ENTRYPOINT [ "gunicorn", "-k", "uvicorn.workers.UvicornWorker" ]
CMD [ "src.app:app", "--bind", "0.0.0.0:5000", "--timeout", "900", "--preload" ]

