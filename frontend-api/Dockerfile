FROM python:3.11-slim

WORKDIR /app

# Copiar e instalar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app.py .

# Criar diretório para modelos (será montado como volume)
RUN mkdir -p /app/models

# Expor porta 50005
EXPOSE 50005

# Variáveis de ambiente
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Comando para rodar com Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:50005", "--workers", "2", "--timeout", "120", "app:app"]
