from pymongo import MongoClient







class DB_Client:

    def __init__(self, connection_string, db_name='CR_PQE_DPM_MONGO_DB',logger=None) -> None:
        client = MongoClient(connection_string)
        self._db = client[db_name]
        self.logger=logger

        #Setting logger to self.logger if not provided
        if self.logger == None: self.logger = print

    def collection_exists(self, collection_name):
        """Check if a collection exists in the database."""
        return collection_name in self._db.list_collection_names()

    def get_collection(self, collection_name):
        if not self.collection_exists(collection_name):
            self.logger(f"Collection {collection_name} not in the database!")
            return None
        return self._db[collection_name]

    def create_collection(self, collection_name):
        if self.collection_exists(collection_name):
            self.logger(f"Collection {collection_name} already exists!")
        else:
            self._db.create_collection(collection_name)
            self.logger(f"Collection {collection_name} created successfully.")

    def delete_collection(self, collection_name):
        if self.collection_exists(collection_name):
            self._db.drop_collection(collection_name)
            self.logger(f"Collection {collection_name} deleted successfully.")
        else:
            self.logger(f"Collection {collection_name} does not exist!")

    def add_item(self, collection_name, item):
        if self.collection_exists(collection_name):
            collection = self._db[collection_name]
            collection.insert_one(item)
            self.logger(f"Item added to collection {collection_name}.")
        else:
            self.logger(f"Collection {collection_name} not found.")

    def delete_item(self, collection_name, query):
        if self.collection_exists(collection_name):
            collection = self._db[collection_name]
            result = collection.delete_one(query)
            if result.deleted_count > 0:
                self.logger(f"Item deleted from collection {collection_name}.")
            else:
                self.logger(f"No item matching the query found in collection {collection_name}.")
        else:
            self.logger(f"Collection {collection_name} not found.")

    def get_all_items(self, collection_name):
        if self.collection_exists(collection_name):
            collection = self._db[collection_name]
            return list(collection.find())
        else:
            self.logger(f"Collection {collection_name} not found.")
            return []

    def filter_items(self, collection_name, filter_query):
        if self.collection_exists(collection_name):
            collection = self._db[collection_name]
            return list(collection.find(filter_query))
        else:
            self.logger(f"Collection {collection_name} not found.")
            return []



