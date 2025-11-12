from flask import Flask, request, jsonify
import pickle
import json
import os
from datetime import datetime
from collections import defaultdict


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
