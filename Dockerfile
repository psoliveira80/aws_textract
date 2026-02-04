FROM python:3.11-slim

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH="${PYTHONPATH}:/"
WORKDIR /app

# 1. Instalação de dependências do Sistema (CRÍTICO)
# Adicionamos libgl1-mesa-glx, libglib2.0-0 e outros essenciais para processamento de imagem
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app

#RUN mkdir -p /app/static/downloads && chmod 777 /app/static/downloads

EXPOSE 5000

# 4. Comando de inicialização correto
# Como mapeamos a pasta app, o main.py está dentro de /app/main.py
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "4"]