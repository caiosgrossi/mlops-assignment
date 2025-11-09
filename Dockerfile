FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema (se necessário)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app.py .

# Criar diretório para modelos
RUN mkdir -p /app/models

# Expor porta
EXPOSE 5005

# Variáveis de ambiente
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Comando para rodar com Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5005", "--workers", "2", "--timeout", "600", "app:app"]
