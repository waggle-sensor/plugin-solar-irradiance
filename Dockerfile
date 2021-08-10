FROM waggle/plugin-base:1.1.1-ml-cuda10.2-l4t

COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY app.py /app/

ARG SAGE_STORE_URL="https://osn.sagecontinuum.org"

ENV SAGE_STORE_URL=${SAGE_STORE_URL}

WORKDIR /app
ENTRYPOINT ["python3", "-u", "/app/app.py"]
