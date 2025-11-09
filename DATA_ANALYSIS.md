# Identificação dos Dados - PVC: /home/caiogrossi/project2-pv/

## Estrutura do Diretório

```
/home/caiogrossi/project2-pv/
├── models/          # Diretório vazio (para armazenar pickles dos modelos)
└── spotify/         # Datasets do Spotify
    ├── 2023_spotify_ds1.csv      (40 MB - 241,458 linhas)
    ├── 2023_spotify_ds2.csv      (39 MB - 240,250 linhas)
    └── 2023_spotify_songs.csv    (205 KB - 6,975 linhas)
```

---

## Análise dos Datasets

### **1. 2023_spotify_ds1.csv** (Dataset para Versão 1.0 do Modelo)

**Estrutura:**
```
Colunas: track_uri, album_name, album_uri, artist_name, artist_uri, duration_ms, pid, track_name
```

**Estatísticas:**
- **Total de linhas:** 241,458 (incluindo header)
- **Total de playlists (pid):** 2,306 playlists únicas
- **Total de músicas únicas (track_name,artist_name):** 5,593
- **Média de músicas por playlist:** ~104.7 músicas
- **Range de tamanho das playlists:** 27 a 269 músicas

**Formato dos Itens (chave para Eclat):**
- **Formato:** `"track_name,artist_name"`
- **Exemplos:**
  - `"Ride Wit Me,Nelly"`
  - `"Sweet Home Alabama,Lynyrd Skynyrd"`
  - `"Paradise,Coldplay"`

**Estrutura de Transação (Playlist):**
- **ID da transação:** Campo `pid` (ex: 115, 100039, etc.)
- **Itemset:** Lista de todas as músicas (track_name,artist_name) naquela playlist

---

### **2. 2023_spotify_ds2.csv** (Dataset para Versão 2.0 do Modelo)

**Estrutura:**
```
Mesma estrutura do ds1: track_uri, album_name, album_uri, artist_name, artist_uri, duration_ms, pid, track_name
```

**Estatísticas:**
- **Total de linhas:** 240,250 (incluindo header)
- **Total de playlists (pid):** 2,287 playlists únicas
- **Total de músicas únicas (track_name,artist_name):** 5,377
- **Overlap com ds1:** 1,063 PIDs aparecem em ambos datasets

**Observações:**
- Datasets parcialmente sobrepostos (algumas playlists estão em ambos)
- Podem conter músicas diferentes nas mesmas playlists
- Representa evolução temporal das playlists

---

### **3. 2023_spotify_songs.csv** (Catálogo de Músicas)

**Estrutura:**
```
Colunas: artist_name, track_name
```

**Estatísticas:**
- **Total de músicas:** 6,975 músicas únicas (artist_name,track_name)

**Exemplos:**
```
Sam Hunt,Bottle It Up - Acoustic Mixtape
Knife Party,Bonfire
Avenged Sevenfold,Welcome to the Family
```

**Propósito:**
- Catálogo de referência de músicas
- Pode ser usado para validação ou enriquecimento
- Formato já no padrão "track_name,artist_name"

---

## Formato para o Serviço Flask

### **Input do POST /train:**

O serviço deve aceitar uma URL do dataset CSV:

```json
{
  "dataset_url": "https://homepages.dcc.ufmg.br/~cunha/hosted/cloudcomp-2023s2-datasets/2023_spotify_ds1.csv"
}
```

**Parâmetros Hard-coded:**
- `min_support`: 0.05 (5% das playlists)
- `min_confidence`: 0.3 (30% de confiança)
- `port`: 5005

**Processamento interno:**
1. Fazer download/streaming do CSV da URL
2. Parsear o CSV e extrair colunas `pid`, `track_name`, `artist_name`
3. Agrupar por `pid` para formar playlists
4. Criar itens no formato `"track_name,artist_name"`
5. Executar Eclat com as playlists processadas (min_support=0.05, min_confidence=0.3)

### **Estrutura de Dados Interna (Eclat):**

**Formato transacional:**
```python
# Lista de transações (playlists)
transactions = [
    ["Ride Wit Me,Nelly", "Sweet Home Alabama,Lynyrd Skynyrd", "Paradise,Coldplay"],
    ["Shape of You,Ed Sheeran", "Ride Wit Me,Nelly", "Faded,Alan Walker"],
    # ... mais playlists
]

# Ou formato tid-list (Transaction ID list) para Eclat:
tid_lists = {
    "Ride Wit Me,Nelly": {0, 1, 5, 8, 12},  # IDs das playlists que contêm esta música
    "Paradise,Coldplay": {0, 2, 7, 15},
    # ... todas as músicas
}
```

---

## Fluxo de Trabalho Esperado

### **Cenário 1: Treinamento Inicial (v1.0)**
```bash
curl -X POST http://localhost:5005/train \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_url": "https://homepages.dcc.ufmg.br/~cunha/hosted/cloudcomp-2023s2-datasets/2023_spotify_ds1.csv"
  }'
```

**Processamento:**
1. Flask baixa CSV da URL
2. Agrupa por `pid` para criar playlists
3. Formata cada item como `"{track_name},{artist_name}"`
4. Executa algoritmo Eclat (min_support=0.05, min_confidence=0.3)
5. Modelo v1.0 salvo em `/app/models/association_rules_v1.0.pkl`

### **Cenário 2: Atualização do Modelo (v2.0)**
```bash
curl -X POST http://localhost:5005/train \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_url": "https://homepages.dcc.ufmg.br/~cunha/hosted/cloudcomp-2023s2-datasets/2023_spotify_ds2.csv"
  }'
```

**Resultado:**
- Modelo v2.0 salvo em `/app/models/association_rules_v2.0.pkl`
- Metadata atualizado com nova versão e timestamp

---

## Características Importantes para Implementação

### **1. Escala dos Dados**
- ~2,300 playlists por dataset
- ~5,500 músicas únicas
- ~100 músicas por playlist em média
- **Desafio:** Eclat precisa ser eficiente para lidar com essa escala

### **2. Formato dos Itens**
- **Chave única:** `"track_name,artist_name"`
- **Separador:** Vírgula (`,`)
- **Importante:** Tratar vírgulas dentro dos nomes (ex: `"Courtesy Of The Red,Toby Keith"`)

### **3. Parâmetros (Hard-coded)**
- **min_support:** 0.05 (5% das playlists)
  - Com 2,300 playlists, min_support=0.05 = músicas em pelo menos 115 playlists
- **min_confidence:** 0.3 (30% de confiança)
  - Balanço entre regras úteis e ruído
- **port:** 5005

### **4. Output Esperado**
- Regras do tipo: `["Paradise,Coldplay"] => ["Sweet Home Alabama,Lynyrd Skynyrd"]`
- Com métricas: support, confidence, lift
- Salvas em formato pickle para reutilização

---

## Pré-processamento Necessário

### **Para usar os CSVs no serviço:**

```python
import pandas as pd

# Carregar dataset
df = pd.read_csv('/home/caiogrossi/project2-pv/spotify/2023_spotify_ds1.csv')

# Criar chave única
df['item'] = df['track_name'] + ',' + df['artist_name']

# Agrupar por playlist
playlists = df.groupby('pid')['item'].apply(list).tolist()

# Resultado: lista de listas para o request
# [
#   ["Ride Wit Me,Nelly", "Red Solo Cup,Toby Keith", ...],
#   ["Another Song,Artist", ...],
#   ...
# ]
```

---

## Próximos Passos

1. ✅ **Identificação dos dados concluída**
2. ⏭️ **Implementar o serviço Flask com:**
   - `app.py` - Endpoints e lógica do Eclat
   - `requirements.txt` - Dependências
   - `Dockerfile` - Containerização
3. ⏭️ **Configurar montagem do volume:**
   - `-v /home/caiogrossi/project2-pv/models:/app/models`
4. ⏭️ **Testar com dados reais do ds1 e ds2**
