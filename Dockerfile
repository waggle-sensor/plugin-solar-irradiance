FROM waggle/plugin-base:1.1.1-ml-cuda10.2-l4t

RUN apt-get update && apt-get install -y --no-install-recommends \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

COPY app.py requirements.txt /app/
RUN pip3 install --no-cache-dir --upgrade pip \
  && pip3 install --no-cache-dir -r /app/requirements.txt

WORKDIR /app
ENTRYPOINT ["python3", "-u", "/app/app.py"]
