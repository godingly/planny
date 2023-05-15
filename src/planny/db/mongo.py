from pymongo import MongoClient
import json
import os,sys

def find_documents(col, query: dict=None, fields: dict=None):
    # e.g. query= { "address":"Sideway 1633"  }, fields = {"_id":0, "name":1, "address":1}
    # "_id" is included automatically undless 
    query = query if query else {}
    fields = fields if fields else {}
    return col.find(query, fields)

def find_all_documents(col):
    return col.find()

def get_collections(db):
    return db.list_collection_names()

def insert_one_into_collection(collection, dct):
    """ e.g. dct = {"name":"john", }"""
    insertOnceRes = collection.insert_one(dct)
    return insertOnceRes # insertOnceRes.inserted_id

def insert_many_into_collection(collection, list_of_dicts):
    insertManyRes = collection.insert_many(list_of_dicts)
    return insertManyRes



class mongo:
    def __init__(self, mongo_json_path: str):
        with open(mongo_json_path, 'r') as f:
            d = json.load(f)
        self.username = d['username']
        self.password = d['password']
        self.client = MongoClient(f"mongodb+srv://{self.username}:{self.password}@cluster0.osgt4.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    
    def get_db(self, db_name: str): return self.client[db_name]

    def get_collection(self, db_name: str, col: str): return self.client[db_name][col]

    
    