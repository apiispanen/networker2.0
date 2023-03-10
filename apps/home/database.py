from pymongo import MongoClient
from bson.objectid import ObjectId
import os


from datetime import datetime, date

MONGO_CLIENT = os.getenv('MONGO_CLIENT')

if MONGO_CLIENT is not None:
    # RUNNING ON RAILWAY
    MONGO_CLIENT = os.getenv('MONGO_CLIENT')
else:
    try:
        from creds import MONGO_CLIENT     
    except:
        from apps.home.creds import MONGO_CLIENT
# Connect to the MongoDB instance
client = MongoClient(MONGO_CLIENT)

def get_conversation(n, db_name, collection_name, response_type=None ,client=client):
    db = client[db_name]
    query = {}
    if response_type:
        query['type'] = response_type
    cursor = db[collection_name].find(query, {'prompt': 1, 'response': 1, '_id': 0}).limit(n).sort([('timestamp', -1)])
    conversation =[]
    for doc in cursor:
        # print(doc['prompt'])
        conversation.append({"role": "assistant", "content": doc['response']})
        conversation.append({"role": "user", "content": doc['prompt']})
    conversation.append({"role": "system", "content": "you are an assistant"})
    conversation.reverse()
    # print(f"{n} conversations: {conversation}")
    return conversation


def get_people(client=client):
    # Pick out the DB we'd like to use.
    db = client.db
    # GET THE PEOPLE COLLECTION (NOT The Document)
    collection = db['people']
    people = collection.find_one({"_id": ObjectId("63fd0087b9b2b4001ccb7c5f")})
    if people == None:
        print("NO OBJECT FOUND")
    # Returns the JSON string of people, as detailed in our example
    # print(people['People'])
    return people

def delete_person(name, client=client):
    db = client.db
    collection = db['people']
    name = str(name)
    result = collection.update_one({"People": {"$exists": True}}, {"$unset": {"People."+name: ""}})
    if result.modified_count == 1:
        print("Successfully deleted " + name + " from the JSON table.")
    else:
        print(name + " not found in the JSON table.")

def update_person(name, json_input, oldvalue, client=client):
    db =client.db
    collection = db['people']
    name = str(name)
    if json_input == '':
        print('no json here silly, removing the field')
        print({"$set": {"People."+name+"."+str(oldvalue): ""}})
        collection.update_one({"People": {"$exists": True}}, {"$set": {"People."+name+"."+str(oldvalue): ""}})
        # DELETE THE FIELD THAT HAS BEEN ASKED OF
    for key in json_input:
        if json_input[key] != "" and json_input[key]:  
            collection.update_one({"People": {"$exists": True}}, {"$set": {"People."+name+"."+str(key): str(json_input[key])}})
            print(f"{key} : {json_input[key]}")

    # If doing user-specific DBs, do:
    # collection.insert({"People": {"$exists": True}}, {"$set": {"People."+name+"."+str(key): str(json_input[key])}}) 
    return name+" Updated"


def log_user_response(user, prompt, response="", type="prompt", person_of_interest='', client=client):
    # Connect to MongoDB
    client = MongoClient(MONGO_CLIENT)
    db = client["db"]
    collection = db["user_responses"]
    
    # Check how many entries the user has already submitted today
    today = date.today()
    query = {
        "user": user,
        "timestamp": {"$gte": datetime.combine(today, datetime.min.time()), "$lt": datetime.combine(today, datetime.max.time())}
    }
    num_entries = collection.count_documents(query)
    
    # DAILY LIMIT
    if num_entries >= 100:
        # If the user has already submitted two entries, prevent further submissions
        client.close()
        print("LIMIT REACHED FOR USER ", user)
        return None
    else:
        # If the user has not yet submitted two entries, create a new one
        doc = {
            "user": user,
            "prompt": prompt,
            "response": response,
            "type":type,
            "timestamp": datetime.utcnow(),
            'person':person_of_interest
        }
        result = collection.insert_one(doc)
        client.close()
        
        # Return the ID of the inserted document
        return result.inserted_id
  

def delete_object(collection, objectID, client=client):
    db = client.db
    collection = db[collection]
    # print(f"ObjectId('{objectID}')")
    result = collection.delete_one({'_id': ObjectId(objectID)} ) # <- HELP
    if result.deleted_count == 1:
        print("Successfully deleted " + objectID + " from the JSON table.")
    else:
        print(f"ObjectID: {objectID} not found in the JSON table.")


# print(log_user_response(1, "what's for dinner?", "Salmon"))
# print(update_person("Sam Casey", conversation_json))
