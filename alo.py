from pymongo import MongoClient
from pymongo.errors import PyMongoError

# MongoDB connection string
MONGODB_URI = "mongodb+srv://Administrador:PPGTI_BD_2025@dadoscnj.hopdkl5.mongodb.net/?retryWrites=true&w=majority&appName=DadosCNJ"
DB_NAME = "processosjuridicos"
COLLECTION_NAME = "movimentacoes"

try:
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    print(f"Connected to database: {DB_NAME}, collection: {COLLECTION_NAME}")

    # Fetch and print all documents
    documents = list(collection.find())
    if documents:
        for doc in documents:
            print(doc)
    else:
        print("No documents found in the collection.")
except PyMongoError as e:
    print(f"Error connecting to MongoDB: {e}")