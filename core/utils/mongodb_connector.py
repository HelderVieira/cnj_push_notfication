from django.conf import settings
from pymongo import MongoClient
from pymongo.errors import PyMongoError

def get_mongodb_collection(collection_name):
    """Establishes a connection to a MongoDB collection."""
    try:
        client = MongoClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB_NAME]
        collection = db[collection_name]
        return collection
    except PyMongoError as e:
        # Em um ambiente de produção, seria melhor logar este erro.
        print(f"Error connecting to MongoDB: {e}")
        return None

def find_process_by_number(numero_processo):
    """Finds a document in the 'processos' collection by numeroProcesso."""
    collection = get_mongodb_collection("processos")
    if collection is not None:
        try:
            document = collection.find_one({"numeroProcesso": numero_processo})
            return document
        except PyMongoError as e:
            print(f"Error querying MongoDB: {e}")
    return None
