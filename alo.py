import sys
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId

# MongoDB connection string
MONGODB_URI = "mongodb+srv://Administrador:PPGTI_BD_2025@dadoscnj.hopdkl5.mongodb.net/?retryWrites=true&w=majority&appName=DadosCNJ"
DB_NAME = "processosjuridicos"

def find_latest_movimentacao(processosNumeros):
    """
    Dado uma lista de processosNumeros, retorna o objeto da coleção movimentacoes que possua a maior dataHora.
    Agora busca o _id do processo na coleção processos e utiliza esse valor para buscar movimentações pelo campo processo_id.
    """
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    processos_collection = db["processos"]
    movimentacoes_collection = db["movimentacoes"]

    for numeroProcesso in processosNumeros:
        processo = processos_collection.find_one({"numeroProcesso": numeroProcesso})
        if not processo:
            print(f"Processo {numeroProcesso} não encontrado na coleção processos.")
            continue
        processo_id = processo.get("_id")
        movimentacoes = list(movimentacoes_collection.find({"processo_id": processo_id}))
        if movimentacoes:
            latest_movimentacao = max(movimentacoes, key=lambda x: x["dataHora"])
            print(f"Processo {numeroProcesso}: {latest_movimentacao['dataHora']} - {latest_movimentacao['nome']}")
        else:
            print(f"Nenhuma movimentação encontrada para o processo {numeroProcesso}.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        find_latest_movimentacao(sys.argv[1:])
