from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["lexragdb"]

documents_collection = db["documents"]   
chunks_collection = db["chunks"]         