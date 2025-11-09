# Planejamento do Serviço Flask - Recomendação de Músicas com Eclat

## Estrutura de Arquivos
```
/
├── app.py
├── requirements.txt
└── Dockerfile
```

---

## 1. app.py - Estrutura Detalhada

### **Imports**
```python
from flask import Flask, request, jsonify
import pandas as pd
import pickle
import json
import os
from datetime import datetime
from collections import defaultdict
from itertools import combinations
import requests
from io import StringIO
```

### **Classes Principais**

#### **EclatAlgorithm**
```python
class EclatAlgorithm:
    def __init__(self):
        self.min_support = 0.05  # Hard-coded
        self.min_confidence = 0.3  # Hard-coded
        self.frequent_itemsets = []
        self.rules = []
        self.tid_lists = {}
        
    def fit(self, transactions):
        """
        Args:
            transactions: Lista de listas (playlists)
                         [["Song1,Artist1", "Song2,Artist2"], ...]
        """
        # 1. Construir tid-lists (vertical database)
        # 2. Encontrar itemsets frequentes (DFS recursivo)
        # 3. Gerar regras de associação
        pass
    
    def _build_tid_lists(self, transactions):
        """Constrói tid-lists para cada item"""
        pass
    
    def _eclat_recursive(self, prefix, items, min_sup_count):
        """DFS para encontrar itemsets frequentes"""
        pass
    
    def _generate_rules(self):
        """Gera regras de associação dos itemsets"""
        pass
    
    def get_results(self):
        """Retorna dicionário com regras e métricas"""
        return {
            'frequent_itemsets': self.frequent_itemsets,
            'rules': self.rules,
            'num_rules': len(self.rules),
            'num_itemsets': len(self.frequent_itemsets)
        }
```

#### **ModelManager**
```python
class ModelManager:
    def __init__(self, models_dir='/app/models'):
        self.models_dir = models_dir
        self.metadata_file = os.path.join(models_dir, 'metadata.json')
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Cria diretórios se não existirem"""
        os.makedirs(self.models_dir, exist_ok=True)
        if not os.path.exists(self.metadata_file):
            self._init_metadata()
    
    def _init_metadata(self):
        """Inicializa metadata.json"""
        metadata = {
            'current_version': '0.0',
            'models': {}
        }
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def get_next_version(self):
        """Retorna próxima versão (1.0, 2.0, 3.0, ...)"""
        metadata = self.get_metadata()
        current = metadata.get('current_version', '0.0')
        major = int(float(current)) + 1
        return f"{major}.0"
    
    def save_model(self, model_data, num_rules, num_itemsets):
        """Salva modelo e atualiza metadata"""
        version = self.get_next_version()
        timestamp = datetime.now().isoformat()
        model_path = os.path.join(self.models_dir, f'association_rules_v{version}.pkl')
        
        # Salvar pickle
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        # Atualizar metadata
        metadata = self.get_metadata()
        metadata['current_version'] = version
        metadata['models'][version] = {
            'path': model_path,
            'timestamp': timestamp,
            'num_rules': num_rules,
            'num_itemsets': num_itemsets
        }
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return model_path, version, timestamp
    
    def get_metadata(self):
        """Retorna metadata atual"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {'current_version': '0.0', 'models': {}}
    
    def get_model_info(self):
        """Retorna informações do modelo atual"""
        metadata = self.get_metadata()
        current_version = metadata.get('current_version', '0.0')
        
        if current_version == '0.0':
            return None
        
        model_info = metadata['models'].get(current_version, {})
        return {
            'current_version': current_version,
            'last_modified': model_info.get('timestamp'),
            'model_path': model_info.get('path'),
            'num_rules': model_info.get('num_rules'),
            'num_itemsets': model_info.get('num_itemsets'),
            'available_versions': list(metadata['models'].keys())
        }
```

### **Funções Auxiliares**

```python
def download_and_process_dataset(dataset_url):
    """
    Baixa CSV da URL e processa em playlists
    
    Args:
        dataset_url: URL do CSV
        
    Returns:
        Lista de playlists: [["Song1,Artist1", ...], ...]
    """
    try:
        # Download do CSV
        response = requests.get(dataset_url, timeout=300)
        response.raise_for_status()
        
        # Ler CSV
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        
        # Validar colunas necessárias
        required_cols = ['pid', 'track_name', 'artist_name']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"CSV deve conter colunas: {required_cols}")
        
        # Criar chave única
        df['item'] = df['track_name'] + ',' + df['artist_name']
        
        # Agrupar por playlist
        playlists = df.groupby('pid')['item'].apply(list).tolist()
        
        return playlists, len(df), len(playlists), df['item'].nunique()
        
    except Exception as e:
        raise Exception(f"Erro ao processar dataset: {str(e)}")


def validate_train_request(data):
    """Valida request do POST /train"""
    if 'dataset_url' not in data:
        return False, "Campo 'dataset_url' é obrigatório"
    
    url = data['dataset_url']
    if not url.startswith(('http://', 'https://')):
        return False, "URL inválida"
    
    return True, None
```

### **Endpoints Flask**

```python
app = Flask(__name__)
model_manager = ModelManager()

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'music-recommendation',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/train', methods=['POST'])
def train_model():
    """
    Treina novo modelo a partir de dataset CSV
    
    Request:
    {
        "dataset_url": "https://example.com/dataset.csv"
    }
    
    Response:
    {
        "status": "success",
        "model_path": "/app/models/association_rules_v1.0.pkl",
        "version": "1.0",
        "timestamp": "2025-11-09T20:00:00",
        "num_rules": 234,
        "num_itemsets": 1567,
        "dataset_stats": {
            "total_transactions": 241458,
            "total_playlists": 2306,
            "unique_items": 5593
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validar request
        valid, error_msg = validate_train_request(data)
        if not valid:
            return jsonify({'status': 'error', 'message': error_msg}), 400
        
        # Parâmetros
        dataset_url = data['dataset_url']
        
        # Download e processar dataset
        playlists, total_trans, total_playlists, unique_items = \
            download_and_process_dataset(dataset_url)
        
        # Treinar Eclat (min_support=0.05, min_confidence=0.3 hard-coded)
        eclat = EclatAlgorithm()
        eclat.fit(playlists)
        results = eclat.get_results()
        
        # Salvar modelo
        model_path, version, timestamp = model_manager.save_model(
            results,
            results['num_rules'],
            results['num_itemsets']
        )
        
        return jsonify({
            'status': 'success',
            'model_path': model_path,
            'version': version,
            'timestamp': timestamp,
            'num_rules': results['num_rules'],
            'num_itemsets': results['num_itemsets'],
            'dataset_stats': {
                'total_transactions': total_trans,
                'total_playlists': total_playlists,
                'unique_items': unique_items
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/model/info', methods=['GET'])
def model_info():
    """
    Retorna informações do modelo atual
    
    Response:
    {
        "current_version": "2.0",
        "last_modified": "2025-11-09T20:00:00",
        "model_path": "/app/models/association_rules_v2.0.pkl",
        "num_rules": 234,
        "num_itemsets": 1567,
        "available_versions": ["1.0", "2.0"]
    }
    """
    try:
        info = model_manager.get_model_info()
        
        if info is None:
            return jsonify({
                'status': 'no_model',
                'message': 'Nenhum modelo treinado ainda'
            }), 404
        
        return jsonify(info), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=False)
```

---

## 2. requirements.txt

```
Flask==3.0.0
pandas==2.1.3
requests==2.31.0
gunicorn==21.2.0
```

**Nota:** Não usar bibliotecas externas para Eclat - implementar do zero.

---

## 3. Dockerfile

```dockerfile
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
```

**Configurações:**
- `--workers 2`: 2 workers (ajustar conforme recursos)
- `--timeout 600`: 10 minutos (datasets grandes + treinamento)
- `--bind 0.0.0.0:5005`: Porta **5005** (hard-coded)
- Volume mount: `-v /home/caiogrossi/project2-pv/models:/app/models`
- **min_support**: 0.05 (hard-coded)
- **min_confidence**: 0.3 (hard-coded)

---

## Algoritmo Eclat - Implementação Detalhada

### **Conceito:**
- Usa representação **vertical** do banco de dados
- Cada item tem uma **tid-list** (lista de IDs de transações)
- Intersecção de tid-lists = suporte do itemset

### **Passos:**

1. **Construir tid-lists iniciais:**
```python
# Para cada item único, guardar lista de playlists que o contêm
tid_lists = {
    "Song1,Artist1": {0, 2, 5, 8},  # Playlists 0, 2, 5, 8
    "Song2,Artist2": {1, 2, 4, 7},
    ...
}
```

2. **Encontrar itemsets frequentes (DFS):**
```python
# Começar com itemsets de tamanho 1
# Para cada par de items frequentes:
#   - Intersectar tid-lists
#   - Se |intersecção| >= min_support * num_playlists:
#       - Item é frequente
#       - Recursivamente explorar combinações maiores
```

3. **Gerar regras de associação:**
```python
# Para cada itemset frequente de tamanho >= 2:
#   - Gerar todas as partições (antecedente => consequente)
#   - Calcular confidence = support(A∪B) / support(A)
#   - Se confidence >= min_confidence: adicionar regra
```

### **Estrutura das Regras:**
```python
{
    'antecedent': ['Song1,Artist1', 'Song2,Artist2'],
    'consequent': ['Song3,Artist3'],
    'support': 0.15,        # 15% das playlists
    'confidence': 0.75,     # 75% de confiança
    'lift': 2.5             # 2.5x mais provável que aleatório
}
```

---

## Exemplo de Uso Completo

### **1. Build e Run:**
```bash
# Build da imagem
docker build -t music-recommendation-service .

# Run com volume montado
docker run -d -p 5005:5005 \
  -v /home/caiogrossi/project2-pv/models:/app/models \
  --name music-rec \
  music-recommendation-service

# Ver logs
docker logs -f music-rec
```

### **2. Treinar Versão 1.0:**
```bash
curl -X POST http://localhost:5005/train \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_url": "https://homepages.dcc.ufmg.br/~cunha/hosted/cloudcomp-2023s2-datasets/2023_spotify_ds1.csv"
  }'

**Response esperado:**
```json
{
  "status": "success",
  "model_path": "/app/models/association_rules_v1.0.pkl",
  "version": "1.0",
  "timestamp": "2025-11-09T20:15:30.123456",
  "num_rules": 234,
  "num_itemsets": 1567,
  "dataset_stats": {
    "total_transactions": 241458,
    "total_playlists": 2306,
    "unique_items": 5593
  }
}
```

### **3. Treinar Versão 2.0:**
```bash
curl -X POST http://localhost:5005/train \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_url": "https://homepages.dcc.ufmg.br/~cunha/hosted/cloudcomp-2023s2-datasets/2023_spotify_ds2.csv"
  }'
```

### **4. Verificar Informações do Modelo:**
```bash
curl http://localhost:5005/model/info
```

**Response esperado:**
```json
{
  "current_version": "2.0",
  "last_modified": "2025-11-09T20:30:45.678901",
  "model_path": "/app/models/association_rules_v2.0.pkl",
  "num_rules": 256,
  "num_itemsets": 1623,
  "available_versions": ["1.0", "2.0"]
}
```

### **5. Health Check:**
```bash
curl http://localhost:5005/health
```

---

## Considerações de Performance

### **Otimizações do Eclat:**
1. **Poda precoce:** Remover items não-frequentes antes da recursão
2. **Ordenação:** Processar items mais frequentes primeiro
3. **Limite de profundidade:** Max itemset size (ex: 5 items)
4. **Cache:** Guardar intersecções já calculadas

### **Timeout e Recursos:**
- Dataset grande (~240K linhas) pode levar 5-10 minutos
- Memória: ~1-2 GB durante processamento
- Gunicorn timeout: 600s (10 minutos)

### **Persistência:**
- Volume Docker garante que modelos sobrevivem a restarts
- `metadata.json` mantém histórico de versões
- Pickles pequenos (~MB) com regras compactadas

---

## Pronto para Implementação! 🚀
