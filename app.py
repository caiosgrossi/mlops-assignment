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
import urllib3

# Disable SSL warnings when verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================================
# ECLAT ALGORITHM IMPLEMENTATION
# ============================================================================

class EclatAlgorithm:
    """
    Implementação do algoritmo Eclat para mineração de regras de associação
    usando representação vertical (tid-lists)
    """
    
    def __init__(self):
        self.min_support = 0.05  # Hard-coded: 5%
        self.min_confidence = 0.3  # Hard-coded: 30%
        self.frequent_itemsets = []
        self.rules = []
        self.tid_lists = {}
        self.num_transactions = 0
        
    def fit(self, transactions):
        """
        Executa o algoritmo Eclat nas transações
        
        Args:
            transactions: Lista de listas (playlists)
                         [["Song1,Artist1", "Song2,Artist2"], ...]
        """
        self.num_transactions = len(transactions)
        min_sup_count = int(self.min_support * self.num_transactions)
        
        # Passo 1: Construir tid-lists (vertical database)
        self._build_tid_lists(transactions)
        
        # Passo 2: Filtrar items frequentes (suporte >= min_support)
        frequent_items = {
            item: tids 
            for item, tids in self.tid_lists.items() 
            if len(tids) >= min_sup_count
        }
        
        # Adicionar itemsets de tamanho 1 aos resultados
        for item, tids in frequent_items.items():
            support = len(tids) / self.num_transactions
            self.frequent_itemsets.append({
                'itemset': [item],
                'support': support,
                'tid_list': tids
            })
        
        # Passo 3: Encontrar itemsets frequentes maiores (DFS)
        items = sorted(frequent_items.keys())
        for i, item in enumerate(items):
            # Explorar combinações com items posteriores
            self._eclat_recursive(
                prefix=[item],
                prefix_tids=frequent_items[item],
                remaining_items=items[i+1:],
                frequent_items=frequent_items,
                min_sup_count=min_sup_count
            )
        
        # Passo 4: Gerar regras de associação
        self._generate_rules()
        
        return self
    
    def _build_tid_lists(self, transactions):
        """Constrói tid-lists para cada item"""
        self.tid_lists = defaultdict(set)
        
        for tid, transaction in enumerate(transactions):
            for item in transaction:
                self.tid_lists[item].add(tid)
    
    def _eclat_recursive(self, prefix, prefix_tids, remaining_items, frequent_items, min_sup_count):
        """
        DFS recursivo para encontrar itemsets frequentes
        
        Args:
            prefix: Lista de items no itemset atual
            prefix_tids: Set de transaction IDs do prefix
            remaining_items: Items ainda não explorados
            frequent_items: Dicionário de items frequentes
            min_sup_count: Contagem mínima de suporte
        """
        for i, item in enumerate(remaining_items):
            # Intersectar tid-lists (operação chave do Eclat)
            new_tids = prefix_tids.intersection(frequent_items[item])
            
            # Verificar se é frequente
            if len(new_tids) >= min_sup_count:
                new_itemset = prefix + [item]
                support = len(new_tids) / self.num_transactions
                
                # Adicionar aos itemsets frequentes
                self.frequent_itemsets.append({
                    'itemset': new_itemset,
                    'support': support,
                    'tid_list': new_tids
                })
                
                # Recursão: explorar itemsets maiores
                # Limitando profundidade para performance
                if len(new_itemset) < 5:  # Max itemset size = 5
                    self._eclat_recursive(
                        prefix=new_itemset,
                        prefix_tids=new_tids,
                        remaining_items=remaining_items[i+1:],
                        frequent_items=frequent_items,
                        min_sup_count=min_sup_count
                    )
    
    def _generate_rules(self):
        """Gera regras de associação a partir dos itemsets frequentes"""
        self.rules = []
        
        # Criar dicionário para lookup rápido de suporte
        itemset_support = {}
        for fs in self.frequent_itemsets:
            key = frozenset(fs['itemset'])
            itemset_support[key] = fs['support']
        
        # Gerar regras de itemsets com tamanho >= 2
        for fs in self.frequent_itemsets:
            itemset = fs['itemset']
            if len(itemset) < 2:
                continue
            
            itemset_sup = fs['support']
            
            # Gerar todas as partições não-vazias (antecedent => consequent)
            for i in range(1, len(itemset)):
                for antecedent in combinations(itemset, i):
                    antecedent = list(antecedent)
                    consequent = [item for item in itemset if item not in antecedent]
                    
                    # Calcular confidence
                    antecedent_key = frozenset(antecedent)
                    if antecedent_key in itemset_support:
                        antecedent_sup = itemset_support[antecedent_key]
                        confidence = itemset_sup / antecedent_sup
                        
                        # Filtrar por min_confidence
                        if confidence >= self.min_confidence:
                            # Calcular lift
                            consequent_key = frozenset(consequent)
                            consequent_sup = itemset_support.get(consequent_key, 0.0001)
                            lift = confidence / consequent_sup
                            
                            self.rules.append({
                                'antecedent': antecedent,
                                'consequent': consequent,
                                'support': itemset_sup,
                                'confidence': confidence,
                                'lift': lift
                            })
    
    def get_results(self):
        """Retorna dicionário com regras e métricas"""
        return {
            'frequent_itemsets': [
                {
                    'itemset': fs['itemset'],
                    'support': fs['support']
                }
                for fs in self.frequent_itemsets
            ],
            'rules': self.rules,
            'num_rules': len(self.rules),
            'num_itemsets': len(self.frequent_itemsets)
        }


# ============================================================================
# MODEL MANAGER
# ============================================================================

class ModelManager:
    """Gerencia salvamento e metadata dos modelos"""
    
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


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def download_and_process_dataset(dataset_url):
    """
    Baixa CSV da URL e processa em playlists
    
    Args:
        dataset_url: URL do CSV
        
    Returns:
        tuple: (playlists, total_transactions, total_playlists, unique_items)
    """
    try:
        # Download do CSV
        print(f"[INFO] Downloading dataset from: {dataset_url}")
        response = requests.get(dataset_url, timeout=300, verify=False)
        response.raise_for_status()
        
        # Ler CSV
        print("[INFO] Parsing CSV...")
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        
        # Validar colunas necessárias
        required_cols = ['pid', 'track_name', 'artist_name']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"CSV deve conter colunas: {required_cols}")
        
        print(f"[INFO] Dataset loaded: {len(df)} rows")
        
        # Criar chave única "track_name,artist_name"
        df['item'] = df['track_name'] + ',' + df['artist_name']
        
        # Agrupar por playlist
        print("[INFO] Grouping by playlist...")
        playlists = df.groupby('pid')['item'].apply(list).tolist()
        
        total_transactions = len(df)
        total_playlists = len(playlists)
        unique_items = df['item'].nunique()
        
        print(f"[INFO] Processed: {total_playlists} playlists, {unique_items} unique songs")
        
        return playlists, total_transactions, total_playlists, unique_items
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro ao baixar dataset: {str(e)}")
    except Exception as e:
        raise Exception(f"Erro ao processar dataset: {str(e)}")


def validate_train_request(data):
    """Valida request do POST /train"""
    if not data:
        return False, "Request body vazio"
    
    if 'dataset_url' not in data:
        return False, "Campo 'dataset_url' é obrigatório"
    
    url = data['dataset_url']
    if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
        return False, "URL inválida"
    
    return True, None


# ============================================================================
# FLASK APP
# ============================================================================

app = Flask(__name__)
model_manager = ModelManager()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'music-recommendation-eclat',
        'timestamp': datetime.now().isoformat(),
        'port': 5005
    }), 200


@app.route('/train', methods=['POST'])
def train_model():
    """
    Treina novo modelo a partir de dataset CSV
    
    Request JSON:
    {
        "dataset_url": "https://example.com/dataset.csv"
    }
    
    Response JSON:
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
        print("\n" + "="*70)
        print("[TRAIN] New training request received")
        print("="*70)
        
        data = request.get_json()
        
        # Validar request
        valid, error_msg = validate_train_request(data)
        if not valid:
            print(f"[ERROR] Validation failed: {error_msg}")
            return jsonify({'status': 'error', 'message': error_msg}), 400
        
        dataset_url = data['dataset_url']
        print(f"[TRAIN] Dataset URL: {dataset_url}")
        
        # Download e processar dataset
        print("[TRAIN] Step 1/3: Downloading and processing dataset...")
        playlists, total_trans, total_playlists, unique_items = \
            download_and_process_dataset(dataset_url)
        
        # Treinar Eclat (min_support=0.05, min_confidence=0.3 hard-coded)
        print("[TRAIN] Step 2/3: Training Eclat algorithm...")
        print(f"[TRAIN] Parameters: min_support=0.05, min_confidence=0.3")
        eclat = EclatAlgorithm()
        eclat.fit(playlists)
        results = eclat.get_results()
        
        print(f"[TRAIN] Eclat completed: {results['num_itemsets']} itemsets, {results['num_rules']} rules")
        
        # Salvar modelo
        print("[TRAIN] Step 3/3: Saving model...")
        model_path, version, timestamp = model_manager.save_model(
            results,
            results['num_rules'],
            results['num_itemsets']
        )
        
        print(f"[TRAIN] Model saved: version {version} at {model_path}")
        print("="*70 + "\n")
        
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
        print(f"[ERROR] Training failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/model/info', methods=['GET'])
def model_info():
    """
    Retorna informações do modelo atual
    
    Response JSON:
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
    print("="*70)
    print("  MUSIC RECOMMENDATION SERVICE - ECLAT ALGORITHM")
    print("="*70)
    print(f"  Port: 5005")
    print(f"  Min Support: 0.05 (hard-coded)")
    print(f"  Min Confidence: 0.3 (hard-coded)")
    print(f"  Models Directory: {model_manager.models_dir}")
    print("="*70)
    print("\nEndpoints:")
    print("  GET  /health       - Health check")
    print("  POST /train        - Train new model")
    print("  GET  /model/info   - Get model information")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5005, debug=False)
