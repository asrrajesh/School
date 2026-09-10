from pymongo import MongoClient
from pymongo.errors import PyMongoError

CONNECTION_STRING = "mongodb+srv://asrrajesh_db_user:Tdwhr20wZEg1dWXf@cluster0.citc42h.mongodb.net/?appName=Cluster0"

try:
    client = MongoClient(CONNECTION_STRING, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    databases = client.list_database_names()
    print("Connection successful")
    print("Available databases:")
    for database in databases:
        print(f"- {database}")

    if "myschool" in databases:
        print("myschool database exists")
        print("Collections in myschool:")
        for collection in client["myschool"].list_collection_names():
            print(f"- {collection}")
    else:
        print("myschool database does not exist")
finally:
    try:
        client.close()
    except (NameError, AttributeError):
        pass
except PyMongoError as error:
    print(f"Connection failed: {error}")
