FROM waggle/plugin-base:1.1.1-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip3 install --no-cache-dir --upgrade pip \
#  && pip3 install --no-cache-dir -r /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY app.py /app/
WORKDIR /app
ENTRYPOINT ["python3", "-u", "/app/app.py"]
