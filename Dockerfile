FROM waggle/plugin-base:1.1.0-ml-cuda11.0-amd64

COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY app.py /app/

ARG SAGE_STORE_URL="HOST"
ARG SAGE_USER_TOKEN="-10"
ARG BUCKET_ID_MODEL="BUCKET_ID_MODEL"

ENV SAGE_STORE_URL=${SAGE_STORE_URL} \
    SAGE_USER_TOKEN=${SAGE_USER_TOKEN} \
    BUCKET_ID_MODEL=${BUCKET_ID_MODEL}

WORKDIR /app
ENTRYPOINT ["python3", "/app/app.py"]
