# Script para Atualizar processos_monitorados com Dados da Última Movimentação
# ============================================================================

import pymongo
from datetime import datetime, timezone
import time
from bson.objectid import ObjectId

# --- Configurações ---
MONGO_URI = "mongodb+srv://Administrador:PPGTI_BD_2025@dadoscnj.hopdkl5.mongodb.net/?retryWrites=true&w=majority&appName=DadosCNJ"
MONGO_DB_NAME = "processosjuridicos"

# Cores para feedback visual
class Cores:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    VERMELHO = '\033[91m'
    AMARELO = '\033[93m'
    VERDE = '\033[92m'
    CIANO = '\033[96m'
    AZUL = '\033[94m'
    MAGENTA = '\033[95m'

def conectar_mongodb():
    """Conecta ao MongoDB e retorna o cliente e banco de dados."""
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        # Testa a conexão
        client.admin.command('ping')
        print(f"{Cores.VERDE}✅ Conectado ao MongoDB com sucesso!{Cores.RESET}")
        return client, db
    except Exception as e:
        print(f"{Cores.VERMELHO}❌ Erro ao conectar ao MongoDB: {e}{Cores.RESET}")
        raise

def obter_ultima_movimentacao_processo(db, processo_cnj_id):
    """
    Obtém a última movimentação de um processo específico.
    Retorna um dicionário com os dados da última movimentação ou None se não houver.
    """
    try:
        # Busca a movimentação mais recente do processo ordenada por dataHora (decrescente)
        ultima_movimentacao = db.movimentacoes.find_one(
            {"processo_id": processo_cnj_id},
            sort=[("dataHora", -1)]  # -1 para ordem decrescente (mais recente primeiro)
        )
        
        if ultima_movimentacao:
            return {
                "ultima_movimentacao_id": ultima_movimentacao["_id"],
                "ultima_movimentacao_codigo": ultima_movimentacao.get("codigo"),
                "ultima_movimentacao_nome": ultima_movimentacao.get("nome"),
                "ultima_movimentacao_data": ultima_movimentacao.get("dataHora"),
                "ultima_movimentacao_complementos": ultima_movimentacao.get("complementosTabelados", [])
            }
        else:
            return None
            
    except Exception as e:
        print(f"{Cores.AMARELO}⚠️  Erro ao buscar última movimentação para {processo_cnj_id}: {e}{Cores.RESET}")
        return None

def atualizar_processos_monitorados_com_ultima_movimentacao(db):
    """
    Atualiza todos os registros em processos_monitorados com informações da última movimentação.
    """
    print(f"\n{Cores.BOLD}{Cores.CIANO}🔄 INICIANDO ATUALIZAÇÃO DOS PROCESSOS MONITORADOS{Cores.RESET}")
    print(f"{Cores.CIANO}📊 Buscando processos monitorados...{Cores.RESET}")
    
    # Busca todos os processos monitorados
    processos_monitorados = list(db.processos_monitorados.find())
    total_processos = len(processos_monitorados)
    
    if total_processos == 0:
        print(f"{Cores.AMARELO}⚠️  Nenhum processo monitorado encontrado.{Cores.RESET}")
        return
    
    print(f"{Cores.AZUL}📋 Total de processos monitorados encontrados: {total_processos}{Cores.RESET}\n")
    
    # Contadores para estatísticas
    atualizados_com_sucesso = 0
    sem_movimentacoes = 0
    erros = 0
    
    # Prepara operações em lote para melhor performance
    bulk_operations = []
    
    for i, processo_monitorado in enumerate(processos_monitorados, 1):
        processo_cnj_id = processo_monitorado.get("processo_cnj_id")
        
        if not processo_cnj_id:
            print(f"{Cores.VERMELHO}❌ [{i}/{total_processos}] Processo sem processo_cnj_id válido{Cores.RESET}")
            erros += 1
            continue
        
        print(f"{Cores.AZUL}🔍 [{i}/{total_processos}] Processando: {processo_cnj_id}{Cores.RESET}")
        
        try:
            # Obtém dados da última movimentação
            dados_ultima_mov = obter_ultima_movimentacao_processo(db, processo_cnj_id)
            
            if dados_ultima_mov:
                # Prepara a atualização
                update_doc = {
                    "$set": {
                        **dados_ultima_mov,
                        "data_atualizacao_ultima_mov": datetime.now(timezone.utc)
                    }
                }
                
                # Adiciona à lista de operações em lote
                bulk_operations.append(
                    pymongo.UpdateOne(
                        {"_id": processo_monitorado["_id"]},
                        update_doc
                    )
                )
                
                print(f"   {Cores.VERDE}✅ Última movimentação: {dados_ultima_mov['ultima_movimentacao_nome'][:50]}...{Cores.RESET}")
                print(f"   {Cores.CIANO}�� Data: {dados_ultima_mov['ultima_movimentacao_data']}{Cores.RESET}")
                atualizados_com_sucesso += 1
                
            else:
                # Processo sem movimentações
                update_doc = {
                    "$set": {
                        "ultima_movimentacao_id": None,
                        "ultima_movimentacao_codigo": None,
                        "ultima_movimentacao_nome": "Sem movimentações",
                        "ultima_movimentacao_data": None,
                        "ultima_movimentacao_complementos": [],
                        "data_atualizacao_ultima_mov": datetime.now(timezone.utc)
                    }
                }
                
                bulk_operations.append(
                    pymongo.UpdateOne(
                        {"_id": processo_monitorado["_id"]},
                        update_doc
                    )
                )
                
                print(f"   {Cores.AMARELO}⚠️  Processo sem movimentações{Cores.RESET}")
                sem_movimentacoes += 1
                
        except Exception as e:
            print(f"   {Cores.VERMELHO}❌ Erro ao processar: {e}{Cores.RESET}")
            erros += 1
        
        # Executa operações em lote a cada 50 registros para otimizar performance
        if len(bulk_operations) >= 50 or i == total_processos:
            if bulk_operations:
                try:
                    resultado = db.processos_monitorados.bulk_write(bulk_operations, ordered=False)
                    print(f"\n{Cores.MAGENTA}💾 Lote executado: {resultado.modified_count} registros atualizados{Cores.RESET}\n")
                    bulk_operations = []
                except Exception as e:
                    print(f"{Cores.VERMELHO}❌ Erro na execução do lote: {e}{Cores.RESET}")
    
    # Executa operações restantes
    if bulk_operations:
        try:
            resultado = db.processos_monitorados.bulk_write(bulk_operations, ordered=False)
            print(f"\n{Cores.MAGENTA}�� Lote final executado: {resultado.modified_count} registros atualizados{Cores.RESET}")
        except Exception as e:
            print(f"{Cores.VERMELHO}❌ Erro na execução do lote final: {e}{Cores.RESET}")
    
    # Resumo final
    print(f"\n{Cores.BOLD}{Cores.CIANO}{'='*60}{Cores.RESET}")
    print(f"{Cores.BOLD}{Cores.CIANO}📊 RESUMO DA ATUALIZAÇÃO{Cores.RESET}")
    print(f"{Cores.BOLD}{Cores.CIANO}{'='*60}{Cores.RESET}")
    print(f"{Cores.AZUL}📋 Total de processos monitorados: {total_processos}{Cores.RESET}")
    print(f"{Cores.VERDE}✅ Atualizados com última movimentação: {atualizados_com_sucesso}{Cores.RESET}")
    print(f"{Cores.AMARELO}⚠️  Processos sem movimentações: {sem_movimentacoes}{Cores.RESET}")
    print(f"{Cores.VERMELHO}❌ Erros durante processamento: {erros}{Cores.RESET}")
    
    taxa_sucesso = ((atualizados_com_sucesso + sem_movimentacoes) / total_processos * 100) if total_processos > 0 else 0
    print(f"{Cores.BOLD}🎯 Taxa de sucesso: {taxa_sucesso:.1f}%{Cores.RESET}")
    print(f"{Cores.CIANO}{'='*60}{Cores.RESET}")

def verificar_estrutura_atualizada(db):
    """
    Verifica alguns registros atualizados para confirmar que a estrutura está correta.
    """
    print(f"\n{Cores.BOLD}{Cores.MAGENTA}�� VERIFICANDO ESTRUTURA ATUALIZADA{Cores.RESET}")
    
    # Busca alguns registros atualizados
    registros_exemplo = list(db.processos_monitorados.find().limit(3))
    
    for i, registro in enumerate(registros_exemplo, 1):
        print(f"\n{Cores.AZUL}📋 Exemplo {i}:{Cores.RESET}")
        print(f"   🆔 Processo: {registro.get('processo_cnj_id', 'N/A')}")
        print(f"   📄 Última movimentação: {registro.get('ultima_movimentacao_nome', 'N/A')}")
        print(f"   📅 Data da última movimentação: {registro.get('ultima_movimentacao_data', 'N/A')}")
        print(f"   🔢 Código da movimentação: {registro.get('ultima_movimentacao_codigo', 'N/A')}")
        print(f"   🔄 Atualizado em: {registro.get('data_atualizacao_ultima_mov', 'N/A')}")

def criar_indices_otimizacao(db):
    """
    Cria índices para otimizar consultas futuras.
    """
    print(f"\n{Cores.BOLD}{Cores.CIANO}⚡ CRIANDO ÍNDICES PARA OTIMIZAÇÃO{Cores.RESET}")
    
    try:
        # Índice para busca por processo_cnj_id em processos_monitorados
        db.processos_monitorados.create_index("processo_cnj_id")
        print(f"{Cores.VERDE}✅ Índice criado: processos_monitorados.processo_cnj_id{Cores.RESET}")
        
        # Índice para busca por data da última movimentação
        db.processos_monitorados.create_index("ultima_movimentacao_data")
        print(f"{Cores.VERDE}✅ Índice criado: processos_monitorados.ultima_movimentacao_data{Cores.RESET}")
        
        # Índice composto para busca por organização e data
        db.processos_monitorados.create_index([("organizacao_id", 1), ("ultima_movimentacao_data", -1)])
        print(f"{Cores.VERDE}✅ Índice composto criado: organizacao_id + ultima_movimentacao_data{Cores.RESET}")
        
        # Índice para busca por processo_id em movimentacoes (se não existir)
        db.movimentacoes.create_index("processo_id")
        print(f"{Cores.VERDE}✅ Índice criado: movimentacoes.processo_id{Cores.RESET}")
        
        # Índice composto para busca otimizada de última movimentação
        db.movimentacoes.create_index([("processo_id", 1), ("dataHora", -1)])
        print(f"{Cores.VERDE}✅ Índice composto criado: movimentacoes.processo_id + dataHora{Cores.RESET}")
        
    except Exception as e:
        print(f"{Cores.AMARELO}⚠️  Alguns índices podem já existir: {e}{Cores.RESET}")

# --- Execução Principal ---
def main():
    """Função principal do script."""
    print(f"{Cores.BOLD}{Cores.CIANO}{'='*80}{Cores.RESET}")
    print(f"{Cores.BOLD}{Cores.CIANO}🔄 ATUALIZAÇÃO DE PROCESSOS MONITORADOS COM ÚLTIMA MOVIMENTAÇÃO{Cores.RESET}")
    print(f"{Cores.BOLD}{Cores.CIANO}{'='*80}{Cores.RESET}")
    
    try:
        # Conecta ao MongoDB
        client, db = conectar_mongodb()
        
        # Cria índices para otimização
        criar_indices_otimizacao(db)
        
        # Executa a atualização principal
        atualizar_processos_monitorados_com_ultima_movimentacao(db)
        
        # Verifica alguns registros atualizados
        verificar_estrutura_atualizada(db)
        
        print(f"\n{Cores.VERDE}🎉 Atualização concluída com sucesso!{Cores.RESET}")
        
    except Exception as e:
        print(f"\n{Cores.VERMELHO}❌ Erro durante a execução: {e}{Cores.RESET}")
    
    finally:
        try:
            client.close()
            print(f"{Cores.CIANO}🔌 Conexão com MongoDB fechada.{Cores.RESET}")
        except:
            pass

# Executa o script
if __name__ == "__main__":
    main()