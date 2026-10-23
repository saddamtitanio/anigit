FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY anigit_server ./anigit_server
COPY scripts ./scripts
RUN useradd -m app && mkdir /data && chown app /data
USER app
ENV ANIGIT_DATA=/data
EXPOSE 8000
CMD ["uvicorn", "anigit_server.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
