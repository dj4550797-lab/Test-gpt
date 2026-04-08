from pymongo import MongoClient
import info

client = MongoClient(info.MONGO_URI)
db = client['flixora_db']
users = db['users']

def add_user(user_id, name):
    if not users.find_one({"user_id": user_id}):
        users.insert_one({"user_id": user_id, "name": name, "premium": False})
