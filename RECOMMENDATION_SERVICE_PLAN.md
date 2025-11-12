# Planejamento do Serviço de Recomendação

## Visão Geral

Serviço Flask que fornece recomendações de músicas baseadas em regras de associação geradas pelo algoritmo Eclat. O serviço lê modelos treinados de um diretório compartilhado e retorna recomendações através de uma API REST.

---

## Estrutura de Arquivos

```
/home/caiog/mlops-assignment/
├── training-service/          # Serviço de Treinamento
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
│
└── recommendation-service/    # NOVO Serviço de Recomendação
    ├── app.py
    ├── requirements.txt
    └── Dockerfile
```

**Volume Compartilhado:**
- Path: `/home/caiog/project2-pv/models`
- Training service: **ESCREVE** modelos (pkl + metadata.json)
- Recommendation service: **LÊ** modelos (pkl + metadata.json)

---

## API Specification

### Endpoint: POST /api/recommender

**URL:** `http://localhost:50005/api/recommender`

**Request:**
```json
{
  "songs": ["Yesterday", "Bohemian Rhapsody", "Hotel California"]
}
```

**Response (Success):**
```json
{
  "songs": ["Hey Jude", "Let It Be", "Come Together", "Something", "Here Comes the Sun"],
  "version": "1.0",
  "model_date": "2025-11-09T20:00:00"
}
```

**Response (No Model):**
```json
{
  "error": "No trained model available"
}
```

**Response (Invalid Input):**
```json
{
  "error": "Campo 'songs' é obrigatório"
}
```

### Endpoint: GET /health

**URL:** `http://localhost:50005/health`

**Response:**
```json
{
  "status": "healthy",
  "service": "music-recommendation-api",
  "model_loaded": true,
  "model_version": "1.0",
  "timestamp": "2025-11-09T20:00:00"
}
```

### Endpoint: POST /reload-model

**URL:** `http://localhost:50005/reload-model`

**Response:**
```json
{
  "status": "success",
  "version": "2.0",
  "model_date": "2025-11-09T21:00:00"
}
```

---

## recommendation-service/app.py - Estrutura

### Imports

```python
from flask import Flask, request, jsonify
import pickle
import json
import os
from datetime import datetime
from collections import defaultdict
```

### Classe: ModelLoader

```python
class ModelLoader:
    """Gerencia carregamento de modelos do diretório compartilhado"""
    
    def __init__(self, models_dir='/app/models'):
        self.models_dir = models_dir
        self.metadata_file = os.path.join(models_dir, 'metadata.json')
        self.current_model = None
        self.current_version = None
        self.model_date = None
        
    def load_latest_model(self):
        """
        Carrega o modelo mais recente do diretório compartilhado
        
        Passos:
        1. Ler metadata.json
        2. Identificar current_version
        3. Carregar pickle do modelo correspondente
        4. Armazenar version e timestamp
        
        Returns:
            dict: Dados do modelo carregado
        
        Raises:
            FileNotFoundError: Se não houver modelo treinado
            Exception: Se houver erro ao carregar pickle
        """
        # Verificar se metadata.json existe
        if not os.path.exists(self.metadata_file):
            raise FileNotFoundError("No metadata.json found. Train a model first.")
        
        # Ler metadata
        with open(self.metadata_file, 'r') as f:
            metadata = json.load(f)
        
        current_version = metadata.get('current_version', '0.0')
        
        if current_version == '0.0':
            raise FileNotFoundError("No trained model available")
        
        # Obter informações do modelo
        model_info = metadata['models'].get(current_version)
        if not model_info:
            raise Exception(f"Model version {current_version} not found in metadata")
        
        model_path = model_info['path']
        
        # Carregar pickle
        with open(model_path, 'rb') as f:
            self.current_model = pickle.load(f)
        
        self.current_version = current_version
        self.model_date = model_info['timestamp']
        
        return self.current_model
    
    def get_model_info(self):
        """Retorna informações do modelo carregado"""
        return {
            'version': self.current_version,
            'model_date': self.model_date
        }
    
    def is_model_loaded(self):
        """Verifica se há modelo carregado"""
        return self.current_model is not None
```

### Classe: RecommendationEngine

```python
class RecommendationEngine:
    """Gera recomendações usando matching parcial de nomes"""
    
    def __init__(self, model_data):
        """
        Args:
            model_data: Dict com 'rules' e 'frequent_itemsets'
        """
        self.rules = model_data['rules']
        self.frequent_itemsets = model_data.get('frequent_itemsets', [])
    
    def recommend(self, input_songs, top_n=5):
        """
        Gera recomendações baseadas nas músicas de entrada
        
        Args:
            input_songs: Lista de strings ["Yesterday", "Hey Jude"]
            top_n: Número de recomendações a retornar
            
        Returns:
            Lista de strings: ["Let It Be", "Come Together", ...]
            
        Algoritmo:
            1. Normalizar input_songs (lowercase, strip)
            2. Para cada regra:
               - Extrair nomes das músicas do antecedent (remover artista)
               - Verificar se TODOS estão no input
               - Se sim, calcular score = confidence * lift
               - Adicionar consequentes aos candidatos
            3. Remover músicas já presentes no input
            4. Ordenar por score e retornar top_n
        """
        # Normalizar input
        input_normalized = [s.lower().strip() for s in input_songs]
        
        # Encontrar regras aplicáveis
        candidates = {}  # {song_name: score}
        
        for rule in self.rules:
            # Verificar se antecedente match com input
            if self._matches_input(rule['antecedent'], input_normalized):
                score = rule['confidence'] * rule['lift']
                
                # Adicionar consequentes
                for consequent in rule['consequent']:
                    song_name = self._extract_song_name(consequent)
                    
                    # Não recomendar músicas já no input
                    if not self._is_in_input(song_name, input_normalized):
                        if song_name in candidates:
                            # Manter score máximo
                            candidates[song_name] = max(candidates[song_name], score)
                        else:
                            candidates[song_name] = score
        
        # Ordenar por score e retornar top_n
        ranked = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        return [song for song, score in ranked[:top_n]]
    
    def _extract_song_name(self, full_string):
        """
        Extrai nome da música de "Song Name,Artist Name"
        
        Args:
            full_string: "Yesterday,Beatles"
            
        Returns:
            "Yesterday"
        """
        return full_string.split(',')[0].strip()
    
    def _matches_input(self, antecedent, input_normalized):
        """
        Verifica se antecedente match com input
        
        Args:
            antecedent: ["Yesterday,Beatles", "Hey Jude,Beatles"]
            input_normalized: ["yesterday", "hey jude"]
            
        Returns:
            True se TODOS os items do antecedent estão no input
        """
        for item in antecedent:
            song_name = self._extract_song_name(item).lower().strip()
            if song_name not in input_normalized:
                return False
        return True
    
    def _is_in_input(self, song_name, input_normalized):
        """
        Verifica se música já está no input
        
        Args:
            song_name: "Let It Be"
            input_normalized: ["yesterday", "hey jude"]
            
        Returns:
            True se música está no input
        """
        return song_name.lower().strip() in input_normalized
```

### Funções Auxiliares

```python
def validate_recommend_request(data):
    """
    Valida request do POST /api/recommender
    
    Args:
        data: Request JSON
        
    Returns:
        (bool, error_message or None)
    """
    if not data or 'songs' not in data:
        return False, "Campo 'songs' é obrigatório"
    
    songs = data['songs']
    
    if not isinstance(songs, list):
        return False, "'songs' deve ser uma lista"
    
    if len(songs) == 0:
        return False, "'songs' não pode ser vazia"
    
    # Validar que são strings
    for song in songs:
        if not isinstance(song, str):
            return False, "Cada música deve ser uma string"
        if not song.strip():
            return False, "Nome de música não pode ser vazio"
    
    return True, None
```

### Endpoints Flask

```python
app = Flask(__name__)
model_loader = ModelLoader(models_dir='/app/models')

# Carregar modelo na inicialização
try:
    model_loader.load_latest_model()
    print(f"[INFO] Model loaded: version {model_loader.current_version}")
except Exception as e:
    print(f"[WARNING] No model available: {e}")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    model_info = model_loader.get_model_info() if model_loader.is_model_loaded() else {}
    
    return jsonify({
        'status': 'healthy',
        'service': 'music-recommendation-api',
        'model_loaded': model_loader.is_model_loaded(),
        'model_version': model_info.get('version'),
        'timestamp': datetime.now().isoformat(),
        'port': 50005
    }), 200


@app.route('/api/recommender', methods=['POST'])
def recommend():
    """
    Endpoint principal de recomendação
    
    Request:
    {
        "songs": ["Yesterday", "Bohemian Rhapsody"]
    }
    
    Response (Success):
    {
        "songs": ["Hey Jude", "Let It Be", "Come Together"],
        "version": "1.0",
        "model_date": "2025-11-09T20:00:00"
    }
    """
    try:
        # Verificar se modelo está carregado
        if not model_loader.is_model_loaded():
            return jsonify({
                'error': 'No trained model available'
            }), 503
        
        # Validar request
        data = request.get_json()
        valid, error_msg = validate_recommend_request(data)
        if not valid:
            return jsonify({
                'error': error_msg
            }), 400
        
        # Extrair músicas de entrada
        input_songs = data['songs']
        
        # Gerar recomendações
        engine = RecommendationEngine(model_loader.current_model)
        recommendations = engine.recommend(input_songs, top_n=5)
        
        # Formatar resposta
        model_info = model_loader.get_model_info()
        
        return jsonify({
            'songs': recommendations,
            'version': model_info['version'],
            'model_date': model_info['model_date']
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/reload-model', methods=['POST'])
def reload_model():
    """
    Endpoint para recarregar modelo sem reiniciar serviço
    
    Útil após novo treinamento no training-service
    """
    try:
        model_loader.load_latest_model()
        info = model_loader.get_model_info()
        
        return jsonify({
            'status': 'success',
            'version': info['version'],
            'model_date': info['model_date']
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    print("="*70)
    print("  MUSIC RECOMMENDATION API SERVICE")
    print("="*70)
    print(f"  Port: 50005")
    print(f"  Models Directory: {model_loader.models_dir}")
    print(f"  Model Version: {model_loader.current_version or 'Not loaded'}")
    print("="*70)
    print("\nEndpoints:")
    print("  GET  /health           - Health check")
    print("  POST /api/recommender  - Get song recommendations")
    print("  POST /reload-model     - Reload model without restart")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=50005, debug=False)
```

---

## recommendation-service/requirements.txt

```
Flask==3.0.0
gunicorn==21.2.0
```

**Nota:** Apenas Flask e Gunicorn necessários. Não precisa de pandas, requests, etc.

---

## recommendation-service/Dockerfile

```dockerfile
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
```

**Configurações:**
- Porta: **50005** (diferente do training service que usa 5005)
- Workers: 2 (inferência é leve)
- Timeout: 120s (2 minutos - apenas lookup de regras)

---

## Algoritmo de Recomendação - Detalhado

### Problema: Matching Parcial

**Dataset treina com:**
```
"Yesterday,Beatles"
"Hey Jude,Beatles"
"Let It Be,Beatles"
```

**Cliente envia:**
```json
{"songs": ["Yesterday"]}
```

**Solução:** Extrair apenas o nome da música para matching.

### Fluxo Completo

#### 1. Input do Cliente
```json
{
  "songs": ["Yesterday", "Hey Jude"]
}
```

#### 2. Normalização
```python
input_normalized = ["yesterday", "hey jude"]
```

#### 3. Iteração sobre Regras

**Regra 1:**
```python
{
  'antecedent': ["Yesterday,Beatles", "Hey Jude,Beatles"],
  'consequent': ["Let It Be,Beatles"],
  'confidence': 0.92,
  'lift': 4.1
}
```

**Processamento:**
1. Extrair nomes: `["Yesterday", "Hey Jude"]`
2. Normalizar: `["yesterday", "hey jude"]`
3. Verificar match: `"yesterday" in input_normalized` ✓ AND `"hey jude" in input_normalized` ✓
4. **Regra é aplicável!**
5. Score: `0.92 * 4.1 = 3.77`
6. Extrair consequente: `"Let It Be"` (de `"Let It Be,Beatles"`)
7. Adicionar aos candidatos: `{"Let It Be": 3.77}`

**Regra 2:**
```python
{
  'antecedent': ["Yesterday,Beatles"],
  'consequent': ["Come Together,Beatles"],
  'confidence': 0.75,
  'lift': 2.8
}
```

**Processamento:**
1. Extrair nomes: `["Yesterday"]`
2. Normalizar: `["yesterday"]`
3. Verificar match: `"yesterday" in input_normalized` ✓
4. **Regra é aplicável!**
5. Score: `0.75 * 2.8 = 2.1`
6. Extrair consequente: `"Come Together"`
7. Adicionar aos candidatos: `{"Come Together": 2.1}`

#### 4. Filtragem e Ranqueamento

```python
candidates = {
  "Let It Be": 3.77,
  "Come Together": 2.1,
  "Something": 1.8,
  "Here Comes the Sun": 1.5
}

# Remover músicas já no input
candidates = {
  # "Yesterday" removido
  # "Hey Jude" removido
  "Let It Be": 3.77,
  "Come Together": 2.1,
  "Something": 1.8,
  "Here Comes the Sun": 1.5
}

# Ordenar por score
ranked = [
  ("Let It Be", 3.77),
  ("Come Together", 2.1),
  ("Something", 1.8),
  ("Here Comes the Sun", 1.5)
]

# Retornar top 5
recommendations = ["Let It Be", "Come Together", "Something", "Here Comes the Sun"]
```

#### 5. Response
```json
{
  "songs": ["Let It Be", "Come Together", "Something", "Here Comes the Sun"],
  "version": "1.0",
  "model_date": "2025-11-09T20:00:00"
}
```

---

## Deployment

### Build da Imagem

```bash
cd /home/caiog/mlops-assignment/recommendation-service
docker build -t recommendation-service .
```

### Run do Container

```bash
docker run -d -p 50005:50005 \
  -v /home/caiog/project2-pv/models:/app/models \
  --name recommendation-container \
  recommendation-service
```

### Verificar Logs

```bash
docker logs -f recommendation-container
```

### Testar Health

```bash
curl http://localhost:50005/health
```

### Exemplo de Requisição

```bash
curl -X POST http://localhost:50005/api/recommender \
  -H "Content-Type: application/json" \
  -d '{"songs": ["Yesterday", "Bohemian Rhapsody"]}'
```

---

## Workflow Completo

### 1. Treinar Modelo (Training Service)

```bash
curl -X POST http://localhost:5005/train \
  -H "Content-Type: application/json" \
  -d '{"dataset_url": "https://homepages.dcc.ufmg.br/~cunha/hosted/cloudcomp-2023s2-datasets/2023_spotify_ds1.csv"}'
```

**Aguardar:** ~5-10 minutos

### 2. Recarregar Modelo (Recommendation Service)

```bash
curl -X POST http://localhost:50005/reload-model
```

**Response:**
```json
{
  "status": "success",
  "version": "1.0",
  "model_date": "2025-11-09T20:00:00"
}
```

### 3. Obter Recomendações

```bash
curl -X POST http://localhost:50005/api/recommender \
  -H "Content-Type: application/json" \
  -d '{"songs": ["Paradise", "Fix You"]}'
```

**Response:**
```json
{
  "songs": ["Viva La Vida", "The Scientist", "Clocks", "Yellow", "Speed of Sound"],
  "version": "1.0",
  "model_date": "2025-11-09T20:00:00"
}
```

---

## Edge Cases e Tratamento de Erros

### 1. Nenhum Modelo Disponível

**Request:**
```bash
curl -X POST http://localhost:50005/api/recommender \
  -H "Content-Type: application/json" \
  -d '{"songs": ["Yesterday"]}'
```

**Response (503):**
```json
{
  "error": "No trained model available"
}
```

### 2. Input Vazio

**Request:**
```json
{"songs": []}
```

**Response (400):**
```json
{
  "error": "'songs' não pode ser vazia"
}
```

### 3. Formato Incorreto

**Request:**
```json
{"songs": "Yesterday"}
```

**Response (400):**
```json
{
  "error": "'songs' deve ser uma lista"
}
```

### 4. Nenhuma Recomendação Encontrada

**Cenário:** Músicas não existem no modelo ou não há regras aplicáveis

**Response (200):**
```json
{
  "songs": [],
  "version": "1.0",
  "model_date": "2025-11-09T20:00:00"
}
```

**Nota:** Não é erro - apenas significa que não há recomendações disponíveis.

### 5. Músicas Desconhecidas

**Request:**
```json
{"songs": ["Unknown Song 12345"]}
```

**Response (200):**
```json
{
  "songs": [],
  "version": "1.0",
  "model_date": "2025-11-09T20:00:00"
}
```

---

## Comparação: Training vs Recommendation Service

| Aspecto | Training Service | Recommendation Service |
|---------|-----------------|----------------------|
| **Porta** | 5005 | 50005 |
| **Função** | Treinar modelos Eclat | Servir recomendações |
| **Volume Access** | Read/Write | Read-only |
| **Dependencies** | pandas, requests, pickle | pickle apenas |
| **Timeout** | 600s (10 min) | 120s (2 min) |
| **Endpoints** | /train, /model/info | /api/recommender, /reload-model |
| **Complexidade** | Alta (algoritmo Eclat) | Baixa (lookup de regras) |
| **Frequência** | Ocasional (treinamento) | Contínuo (inferência) |
| **CPU Usage** | Alto durante treino | Baixo |
| **Memory** | 1-2 GB durante treino | ~100-200 MB |

---

## Considerações de Performance

### Otimizações Implementadas

1. **Matching Eficiente:**
   - Normalização uma vez no início
   - Comparação lowercase para case-insensitive

2. **Score Máximo:**
   - Se múltiplas regras recomendam mesma música, mantém maior score
   - Evita duplicatas

3. **Early Stopping:**
   - Retorna top_n ao invés de todas as recomendações
   - Reduz processamento desnecessário

4. **Cache de Modelo:**
   - Modelo carregado na inicialização
   - Recarregamento apenas via endpoint `/reload-model`

### Escalabilidade

**Para datasets maiores:**
- Aumentar workers no Gunicorn: `--workers 4`
- Considerar cache de recomendações frequentes
- Implementar pagination para mais de 5 recomendações

**Limite Prático:**
- ~10,000 regras: <100ms por request
- ~50,000 regras: <500ms por request
- >100,000 regras: Considerar indexação

---

## Próximos Passos

1. ✅ **Planejamento concluído**
2. ⏭️ **Implementar `recommendation-service/app.py`**
3. ⏭️ **Criar Dockerfile**
4. ⏭️ **Testar com modelo treinado**
5. ⏭️ **Implementar cliente CLI**
6. ⏭️ **Documentar uso completo**

---

## Notas Importantes

- **Formato de Input:** Apenas nomes de músicas (não precisa de artista)
- **Matching:** Parcial - extrai nome da música do formato "Nome,Artista" do modelo
- **Porta:** 50005 (não confundir com 5005 do training service)
- **Endpoint:** `/api/recommender` (não `/api/recommend`)
- **Volume:** Compartilhado com training service em `/home/caiog/project2-pv/models`
