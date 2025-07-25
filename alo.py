import sys
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId

# MongoDB connection string
MONGODB_URI = "mongodb+srv://Administrador:PPGTI_BD_2025@dadoscnj.hopdkl5.mongodb.net/?retryWrites=true&w=majority&appName=DadosCNJ"
DB_NAME = "processosjuridicos"

def get_movimentacoes_by_numero_processo(numero_processo):
    """
    Busca as movimentações de um processo pelo seu número.

    Args:
        numero_processo (str): O número do processo a ser buscado.

    Returns:
        list: Uma lista de documentos de movimentações ou None se o processo não for encontrado.
    """
    try:
        client = MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        processos_collection = db["processos"]
        movimentacoes_collection = db["movimentacoes"]

        print(f"Buscando processo com número: {numero_processo}")
        processo = processos_collection.find_one({"numeroProcesso": numero_processo})

        if not processo:
            print("Processo não encontrado.")
            return None

        processo_id = processo.get('_id')
        print(f"Processo encontrado com _id: {processo_id}")

        # A referência pode ser uma string ou um ObjectId, vamos tratar ambos os casos
        movimentacoes = list(movimentacoes_collection.find({"processo_id": str(processo_id)}))
        
        # Se não encontrar com string, tenta com ObjectId
        if not movimentacoes:
            movimentacoes = list(movimentacoes_collection.find({"processo_id": ObjectId(processo_id)}))

        return movimentacoes

    except PyMongoError as e:
        print(f"Erro ao conectar ou consultar o MongoDB: {e}")
        return None
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        numero_processo_exemplo = sys.argv[1]
    else:
        # Coloque um número de processo válido aqui para testes
        numero_processo_exemplo = "00029367720254058202" 

    movimentacoes = get_movimentacoes_by_numero_processo(numero_processo_exemplo)

    if movimentacoes:
        print(f"\nEncontradas {len(movimentacoes)} movimentações para o processo {numero_processo_exemplo}:")
        for mov in movimentacoes:
            print(mov)
    else:
        print(f"\nNenhuma movimentação encontrada para o processo {numero_processo_exemplo}.")