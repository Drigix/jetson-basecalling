import os
import json
from dotenv import load_dotenv
from azure.cosmos import exceptions, CosmosClient, PartitionKey

load_dotenv()

# env variables
COSMOS_DB_URI = os.environ["COSMOS_DB_URI"]
COSMOS_DB_PRIMARY_KEY = os.environ["COSMOS_DB_PRIMARY_KEY"]
COSMOS_DB_DATABASE = os.environ["COSMOS_DB_DATABASE"]

class AzureCosmosConnector:
    def __init__(self, uri=COSMOS_DB_URI, primary_key=COSMOS_DB_PRIMARY_KEY):
        self.uri = uri
        self.primary_key = primary_key
        self.client = CosmosClient(self.uri, self.primary_key)
        self.db_id = COSMOS_DB_DATABASE

        try:
            self.database = self.client.create_database(id=self.db_id)
        except exceptions.CosmosResourceExistsError:
            self.database = self.client.get_database_client(database=self.db_id)

    def connect_container(self, container_name):
        try:
            self.container_name = container_name
            self.container = self.database.create_container(
                id=self.container_name,
                partition_key=PartitionKey(path="/id"),
            )
        except exceptions.CosmosResourceExistsError:
            self.container = self.database.get_container_client(self.container_name)