#!/usr/bin/env python3
"""
Standalone Training Job for Music Recommendation System
Uses Eclat Algorithm for association rule mining
Designed to run as a Kubernetes Job (batch execution)
"""

import logging
import sys
import os
import pandas as pd
import pickle
import json
from datetime import datetime
from collections import defaultdict
from itertools import combinations
import requests
from io import StringIO
import urllib3

# Disable SSL warnings when verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


# ============================================================================
# DATASET PROCESSING
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
        logger.info(f"Downloading dataset from: {dataset_url}")
        response = requests.get(dataset_url, timeout=300, verify=False)
        response.raise_for_status()
        
        # Ler CSV
        logger.info("Parsing CSV...")
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        
        # Validar colunas necessárias
        required_cols = ['pid', 'track_name', 'artist_name']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"CSV deve conter colunas: {required_cols}")
        
        logger.info(f"Dataset loaded: {len(df)} rows")
        
        # Criar chave única "track_name,artist_name"
        df['item'] = df['track_name'] + ',' + df['artist_name']
        
        # Agrupar por playlist
        logger.info("Grouping by playlist...")
        playlists = df.groupby('pid')['item'].apply(list).tolist()
        
        total_transactions = len(df)
        total_playlists = len(playlists)
        unique_items = df['item'].nunique()
        
        logger.info(f"Processed: {total_playlists} playlists, {unique_items} unique songs")
        
        return playlists, total_transactions, total_playlists, unique_items
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro ao baixar dataset: {str(e)}")
    except Exception as e:
        raise Exception(f"Erro ao processar dataset: {str(e)}")


# ============================================================================
# MAIN TRAINING FUNCTION
# ============================================================================

def train_and_save_model():
    """
    Main training function that orchestrates the entire process
    Returns True on success, False on failure
    """
    try:
        logger.info("="*70)
        logger.info("  TRAINING JOB STARTED")
        logger.info("="*70)
        
        # Read configuration from environment variables
        dataset_url = os.environ.get('DATASET_URL')
        dataset_version = os.environ.get('DATASET_VERSION', 'unknown')
        dataset_name = os.environ.get('DATASET_NAME', 'unknown')
        
        if not dataset_url:
            logger.error("DATASET_URL environment variable is not set")
            return False
        
        logger.info(f"Dataset URL: {dataset_url}")
        logger.info(f"Dataset Version: {dataset_version}")
        logger.info(f"Dataset Name: {dataset_name}")
        logger.info(f"Algorithm: Eclat (min_support=0.05, min_confidence=0.3)")
        
        # Step 1: Download and process dataset
        logger.info("Step 1/3: Downloading and processing dataset...")
        playlists, total_trans, total_playlists, unique_items = \
            download_and_process_dataset(dataset_url)
        
        logger.info(f"Dataset stats: {total_playlists} playlists, {unique_items} unique items, {total_trans} transactions")
        
        # Step 2: Train Eclat algorithm
        logger.info("Step 2/3: Training Eclat algorithm...")
        eclat = EclatAlgorithm()
        eclat.fit(playlists)
        results = eclat.get_results()
        
        logger.info(f"Training completed: {results['num_itemsets']} itemsets, {results['num_rules']} rules generated")
        
        # Step 3: Save model
        logger.info("Step 3/3: Saving model to persistent storage...")
        model_manager = ModelManager(models_dir='/app/models/dev')
        model_path, version, timestamp = model_manager.save_model(
            results,
            results['num_rules'],
            results['num_itemsets']
        )
        
        logger.info(f"Model saved successfully:")
        logger.info(f"  - Path: {model_path}")
        logger.info(f"  - Version: {version}")
        logger.info(f"  - Timestamp: {timestamp}")
        logger.info(f"  - Rules: {results['num_rules']}")
        logger.info(f"  - Itemsets: {results['num_itemsets']}")
        
        logger.info("="*70)
        logger.info("  TRAINING JOB COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        
        return True
        
    except Exception as e:
        logger.error(f"Training job failed with error: {str(e)}", exc_info=True)
        return False


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        logger.info("Starting training job execution")
        success = train_and_save_model()
        
        if success:
            logger.info("Exiting with success code (0)")
            sys.exit(0)
        else:
            logger.error("Training failed, exiting with error code (1)")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error in training job: {str(e)}", exc_info=True)
        sys.exit(1)
