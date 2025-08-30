#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atualizador Automático de Movimentações - DataJud CNJ
=====================================================

Script para atualização automática das movimentações dos processos monitorados.
Executa consultas na API do DataJud CNJ e atualiza o banco MongoDB.

Uso:
    python atualizador_movimentacoes.py

Agendamento:
    Linux/Mac: crontab -e
    0 * * * * /usr/bin/python3 /caminho/para/atualizador_movimentacoes.py

    Windows: Task Scheduler
    Executar a cada 1 hora

Autor: Sistema ETL DataJud
Data: 2025-07-25
"""

import sys
import os
import logging
import json
import hashlib
import time
import requests
import pymongo
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import traceback

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

# Configurações do MongoDB
MONGO_URI = "mongodb+srv://Administrador:PPGTI_BD_2025@dadoscnj.hopdkl5.mongodb.net/?retryWrites=true&w=majority&appName=DadosCNJ"
MONGO_DB_NAME = "processosjuridicos"

# Configurações da API DataJud
API_BASE_URL = "https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal}/_search"
DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
API_TIMEOUT = 60
MAX_RETRIES = 3

# Configurações de processamento
LOTE_TAMANHO = 50  # Processos por lote
INTERVALO_ENTRE_LOTES = 5  # segundos
INTERVALO_RATE_LIMIT = 30  # segundos

# Configurações de atualização
HORAS_JANELA_ATUALIZACAO = 24  # Atualiza processos consultados há mais de X horas
MAX_PROCESSOS_POR_EXECUCAO = 500  # Limite para evitar execução muito longa

# =============================================================================
# CONFIGURAÇÃO DE LOGGING
# =============================================================================

def configurar_logging():
    """Configura o sistema de logging."""
    
    # Cria diretório de logs se não existir
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Nome do arquivo de log com data
    log_filename = os.path.join(log_dir, f'atualizador_{datetime.now().strftime("%Y%m%d")}.log')
    
    # Configuração do logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

# =============================================================================
# CLASSES E FUNÇÕES AUXILIARES
# =============================================================================

class AtualizadorMovimentacoes:
    """Classe principal para atualização de movimentações."""
    
    def __init__(self):
        self.logger = configurar_logging()
        self.mongo_client = None
        self.db = None
        self.estatisticas = {
            'processos_verificados': 0,
            'processos_atualizados': 0,
            'novas_movimentacoes': 0,
            'processos_sem_mudancas': 0,
            'processos_com_erro': 0,
            'tempo_inicio': datetime.now(),
            'tempo_fim': None
        }
    
    def conectar_mongodb(self) -> bool:
        """Conecta ao MongoDB."""
        try:
            self.mongo_client = pymongo.MongoClient(MONGO_URI)
            self.db = self.mongo_client[MONGO_DB_NAME]
            # Testa a conexão
            self.mongo_client.admin.command('ping')
            self.logger.info("✅ Conectado ao MongoDB com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao conectar ao MongoDB: {e}")
            return False
    
    def desconectar_mongodb(self):
        """Desconecta do MongoDB."""
        if self.mongo_client:
            self.mongo_client.close()
            self.logger.info("🔌 Conexão MongoDB fechada")
    
    def string_para_datetime_utc(self, date_string: str) -> Optional[datetime]:
        """Converte string de data da API para datetime UTC."""
        if not date_string:
            return None
        
        try:
            # Corrige nanosegundos
            if date_string.endswith('Z'):
                date_string = date_string[:-1] + '+00:00'
            
            if '+' in date_string and '.' in date_string:
                date_part, tz_part = date_string.split('+')
                if '.' in date_part:
                    main_part, frac_part = date_part.split('.')
                    if len(frac_part) > 6:
                        frac_part = frac_part[:6]
                    date_string = f"{main_part}.{frac_part}+{tz_part}"
            
            dt = datetime.fromisoformat(date_string)
            return dt.astimezone(timezone.utc)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao parsear data '{date_string}': {e}")
            return None
    
    def obter_processos_para_atualizar(self) -> List[Dict]:
        """Obtém lista de processos que precisam ser atualizados."""
        try:
            # Data limite para considerar processo desatualizado
            data_limite = datetime.now(timezone.utc) - timedelta(hours=HORAS_JANELA_ATUALIZACAO)
            
            # Query para buscar processos que precisam atualização
            query = {
                "status_monitoramento": "ativo",
                "$or": [
                    {"data_ultima_consulta_api": {"$lt": data_limite}},
                    {"data_ultima_consulta_api": {"$exists": False}}
                ]
            }
            
            # Busca processos ordenados por data da última consulta (mais antigos primeiro)
            processos = list(
                self.db.processos_monitorados.find(query)
                .sort("data_ultima_consulta_api", 1)
                .limit(MAX_PROCESSOS_POR_EXECUCAO)
            )
            
            self.logger.info(f"📋 Encontrados {len(processos)} processos para atualizar")
            return processos
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao buscar processos para atualizar: {e}")
            return []
    
    def consultar_api_datajud_lote(self, tribunal: str, numeros_processos: List[str]) -> Dict[str, Dict]:
        """Consulta múltiplos processos na API DataJud."""
        url = API_BASE_URL.format(tribunal=tribunal.lower())
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'ApiKey {DATAJUD_API_KEY}'
        }
        
        query = {
            "query": {
                "terms": {
                    "numeroProcesso": numeros_processos
                }
            },
            "size": len(numeros_processos)
        }
        
        for tentativa in range(MAX_RETRIES):
            try:
                self.logger.debug(f"🔍 Consultando {len(numeros_processos)} processos no {tribunal} (tentativa {tentativa + 1})")
                
                response = requests.post(url, headers=headers, json=query, timeout=API_TIMEOUT)
                
                if response.status_code == 429:
                    self.logger.warning(f"⏰ Rate limit atingido. Aguardando {INTERVALO_RATE_LIMIT}s...")
                    time.sleep(INTERVALO_RATE_LIMIT)
                    continue
                
                response.raise_for_status()
                
                response_json = response.json()
                total_hits = response_json.get("hits", {}).get("total", {}).get("value", 0)
                
                # Mapeia resultados por número do processo
                processos_encontrados = {}
                for hit in response_json.get("hits", {}).get("hits", []):
                    numero_processo = hit.get("_source", {}).get("numeroProcesso")
                    if numero_processo:
                        processos_encontrados[numero_processo] = hit
                
                self.logger.debug(f"✅ API retornou {total_hits} processos de {len(numeros_processos)} consultados")
                return processos_encontrados
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"⚠️ Erro na tentativa {tentativa + 1}: {e}")
                if tentativa < MAX_RETRIES - 1:
                    time.sleep(5 * (tentativa + 1))
                else:
                    self.logger.error(f"❌ Falha após {MAX_RETRIES} tentativas para {tribunal}")
                    return {}
        
        return {}
    
    def processar_movimentacoes_processo(self, processo_cnj_id: str, movimentos_api: List[Dict]) -> Tuple[int, Dict]:
        """Processa e salva movimentações de um processo."""
        timestamp_atual = datetime.now(timezone.utc)
        novas_movimentacoes = 0
        dados_ultima_movimentacao = None
        
        try:
            # Busca movimentações existentes
            movimentacoes_existentes = set(
                self.db.movimentacoes.distinct("_id", {"processo_id": processo_cnj_id})
            )
            
            mov_bulk_ops = []
            movimentos_ordenados = []
            
            for mov_idx, mov_api_data in enumerate(movimentos_api):
                # Gera ID determinístico
                mov_hash_parts = [
                    str(processo_cnj_id),
                    str(mov_api_data.get("codigo")),
                    str(mov_api_data.get("dataHora")),
                    json.dumps(mov_api_data.get("complementosTabelados", []), sort_keys=True),
                    str(mov_idx)
                ]
                mov_id = hashlib.sha1("".join(filter(None, mov_hash_parts)).encode('utf-8')).hexdigest()
                
                # Verifica se é nova movimentação
                if mov_id not in movimentacoes_existentes:
                    mov_doc = {
                        "_id": mov_id,
                        "processo_id": processo_cnj_id,
                        "codigo": mov_api_data.get("codigo"),
                        "nome": mov_api_data.get("nome"),
                        "dataHora": self.string_para_datetime_utc(mov_api_data.get("dataHora")),
                        "complementosTabelados": mov_api_data.get("complementosTabelados", []),
                        "data_criacao_sistema": timestamp_atual,
                        "data_atualizacao_sistema": timestamp_atual,
                        "data_ultima_consulta_api": timestamp_atual
                    }
                    
                    mov_bulk_ops.append(pymongo.InsertOne(mov_doc))
                    novas_movimentacoes += 1
                
                # Adiciona à lista para encontrar a última
                movimentos_ordenados.append({
                    "id": mov_id,
                    "codigo": mov_api_data.get("codigo"),
                    "nome": mov_api_data.get("nome"),
                    "dataHora": self.string_para_datetime_utc(mov_api_data.get("dataHora")),
                    "complementos": mov_api_data.get("complementosTabelados", [])
                })
            
            # Executa inserções em lote
            if mov_bulk_ops:
                self.db.movimentacoes.bulk_write(mov_bulk_ops, ordered=False)
            
            # Encontra a última movimentação
            if movimentos_ordenados:
                movimentos_ordenados.sort(
                    key=lambda x: x["dataHora"] or datetime.min.replace(tzinfo=timezone.utc),
                    reverse=True
                )
                ultima = movimentos_ordenados[0]
                
                dados_ultima_movimentacao = {
                    "ultima_movimentacao_id": ultima["id"],
                    "ultima_movimentacao_codigo": ultima["codigo"],
                    "ultima_movimentacao_nome": ultima["nome"],
                    "ultima_movimentacao_data": ultima["dataHora"],
                    "ultima_movimentacao_complementos": ultima["complementos"]
                }
            
            return novas_movimentacoes, dados_ultima_movimentacao
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar movimentações de {processo_cnj_id}: {e}")
            return 0, None
    
    def atualizar_processo_monitorado(self, processo_monitorado: Dict, dados_ultima_mov: Optional[Dict]):
        """Atualiza registro em processos_monitorados."""
        timestamp_atual = datetime.now(timezone.utc)
        
        try:
            update_doc = {
                "$set": {
                    "data_ultima_consulta_api": timestamp_atual,
                    "ult_data_sinc_cnj": timestamp_atual
                }
            }
            
            # Adiciona dados da última movimentação se disponível
            if dados_ultima_mov:
                update_doc["$set"].update(dados_ultima_mov)
                update_doc["$set"]["data_atualizacao_ultima_mov"] = timestamp_atual
            
            self.db.processos_monitorados.update_one(
                {"_id": processo_monitorado["_id"]},
                update_doc
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar processo monitorado {processo_monitorado.get('processo_cnj_id')}: {e}")
    
    def processar_lote_processos(self, processos_lote: List[Dict]):
        """Processa um lote de processos."""
        if not processos_lote:
            return
        
        # Agrupa por tribunal
        processos_por_tribunal = {}
        for processo in processos_lote:
            # Extrai tribunal do processo_cnj_id (formato: TJPB_G1_numero)
            processo_cnj_id = processo.get("processo_cnj_id", "")
            if "_" in processo_cnj_id:
                tribunal = processo_cnj_id.split("_")[0]
                if tribunal not in processos_por_tribunal:
                    processos_por_tribunal[tribunal] = []
                processos_por_tribunal[tribunal].append(processo)
        
        # Processa cada tribunal
        for tribunal, processos_tribunal in processos_por_tribunal.items():
            try:
                self.logger.info(f"🏛️ Processando {len(processos_tribunal)} processos do {tribunal}")
                
                # Extrai números dos processos para consulta
                numeros_processos = []
                mapa_processo = {}
                
                for processo in processos_tribunal:
                    processo_cnj_id = processo.get("processo_cnj_id", "")
                    # Extrai número do processo do ID (formato: TRIBUNAL_GRAU_NUMERO)
                    if "_" in processo_cnj_id:
                        partes = processo_cnj_id.split("_")
                        if len(partes) >= 3:
                            numero_processo = partes[2]  # Terceira parte é o número
                            numeros_processos.append(numero_processo)
                            mapa_processo[numero_processo] = processo
                
                if not numeros_processos:
                    self.logger.warning(f"⚠️ Nenhum número de processo válido encontrado para {tribunal}")
                    continue
                
                # Consulta API em lote
                processos_api = self.consultar_api_datajud_lote(tribunal, numeros_processos)
                
                # Processa cada processo
                for numero_processo, dados_api in processos_api.items():
                    if numero_processo in mapa_processo:
                        processo_monitorado = mapa_processo[numero_processo]
                        processo_cnj_id = processo_monitorado.get("processo_cnj_id")
                        
                        try:
                            # Processa movimentações
                            movimentos_api = dados_api.get("_source", {}).get("movimentos", [])
                            novas_movs, dados_ultima_mov = self.processar_movimentacoes_processo(
                                processo_cnj_id, movimentos_api
                            )
                            
                            # Atualiza processo monitorado
                            self.atualizar_processo_monitorado(processo_monitorado, dados_ultima_mov)
                            
                            # Atualiza estatísticas
                            self.estatisticas['processos_verificados'] += 1
                            if novas_movs > 0:
                                self.estatisticas['processos_atualizados'] += 1
                                self.estatisticas['novas_movimentacoes'] += novas_movs
                                self.logger.info(f"✅ {processo_cnj_id}: {novas_movs} novas movimentações")
                            else:
                                self.estatisticas['processos_sem_mudancas'] += 1
                                self.logger.debug(f"ℹ️ {processo_cnj_id}: sem novas movimentações")
                            
                        except Exception as e:
                            self.estatisticas['processos_com_erro'] += 1
                            self.logger.error(f"❌ Erro ao processar {processo_cnj_id}: {e}")
                
                # Processa processos não encontrados na API
                for numero_processo, processo_monitorado in mapa_processo.items():
                    if numero_processo not in processos_api:
                        processo_cnj_id = processo_monitorado.get("processo_cnj_id")
                        self.logger.debug(f"ℹ️ {processo_cnj_id}: não encontrado na API")
                        
                        # Atualiza apenas a data de consulta
                        self.atualizar_processo_monitorado(processo_monitorado, None)
                        self.estatisticas['processos_verificados'] += 1
                        self.estatisticas['processos_sem_mudancas'] += 1
                
            except Exception as e:
                self.logger.error(f"❌ Erro ao processar tribunal {tribunal}: {e}")
                for processo in processos_tribunal:
                    self.estatisticas['processos_com_erro'] += 1
    
    def executar_atualizacao(self):
        """Executa o processo completo de atualização."""
        self.logger.info("🚀 Iniciando atualização de movimentações")
        
        try:
            # Conecta ao banco
            if not self.conectar_mongodb():
                return False
            
            # Obtém processos para atualizar
            processos = self.obter_processos_para_atualizar()
            
            if not processos:
                self.logger.info("ℹ️ Nenhum processo precisa ser atualizado no momento")
                return True
            
            # Processa em lotes
            total_lotes = (len(processos) + LOTE_TAMANHO - 1) // LOTE_TAMANHO
            
            for i in range(0, len(processos), LOTE_TAMANHO):
                lote_num = (i // LOTE_TAMANHO) + 1
                processos_lote = processos[i:i + LOTE_TAMANHO]
                
                self.logger.info(f"📦 Processando lote {lote_num}/{total_lotes} ({len(processos_lote)} processos)")
                
                self.processar_lote_processos(processos_lote)
                
                # Pausa entre lotes
                if i + LOTE_TAMANHO < len(processos):
                    self.logger.debug(f"⏰ Aguardando {INTERVALO_ENTRE_LOTES}s antes do próximo lote...")
                    time.sleep(INTERVALO_ENTRE_LOTES)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro durante atualização: {e}")
            self.logger.error(traceback.format_exc())
            return False
        
        finally:
            self.desconectar_mongodb()
    
    def imprimir_estatisticas(self):
        """Imprime estatísticas finais da execução."""
        self.estatisticas['tempo_fim'] = datetime.now()
        duracao = self.estatisticas['tempo_fim'] - self.estatisticas['tempo_inicio']
        
        self.logger.info("📊 ESTATÍSTICAS DA EXECUÇÃO:")
        self.logger.info(f"   ⏱️  Duração: {duracao}")
        self.logger.info(f"   📋 Processos verificados: {self.estatisticas['processos_verificados']}")
        self.logger.info(f"   ✅ Processos atualizados: {self.estatisticas['processos_atualizados']}")
        self.logger.info(f"   📄 Novas movimentações: {self.estatisticas['novas_movimentacoes']}")
        self.logger.info(f"   ℹ️  Processos sem mudanças: {self.estatisticas['processos_sem_mudancas']}")
        self.logger.info(f"   ❌ Processos com erro: {self.estatisticas['processos_com_erro']}")

# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

def main():
    """Função principal do script."""
    atualizador = AtualizadorMovimentacoes()
    
    try:
        atualizador.logger.info("=" * 80)
        atualizador.logger.info("🔄 ATUALIZADOR AUTOMÁTICO DE MOVIMENTAÇÕES - DataJud CNJ")
        atualizador.logger.info("=" * 80)
        
        sucesso = atualizador.executar_atualizacao()
        
        atualizador.imprimir_estatisticas()
        
        if sucesso:
            atualizador.logger.info("✅ Atualização concluída com sucesso!")
            sys.exit(0)
        else:
            atualizador.logger.error("❌ Atualização finalizada com erros!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        atualizador.logger.info("⏹️ Execução interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        atualizador.logger.error(f"❌ Erro fatal: {e}")
        atualizador.logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()