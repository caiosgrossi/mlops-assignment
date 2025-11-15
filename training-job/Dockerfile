FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema (se necessário)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação (standalone training script)
COPY train_job.py .

# Criar diretório para modelos
RUN mkdir -p /app/models

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1

# Comando para rodar training script
CMD ["python", "train_job.py"]
