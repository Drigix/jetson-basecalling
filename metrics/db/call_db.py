from config_db import AzureCosmosConnector
import uuid

connector = AzureCosmosConnector()
connector.connect_container("test")

data = {
    "id": str(uuid.uuid4()),
    "file_size": 0.6407470703125,
    "time": 0.057817697525024414,
    "ram": 1619.9140625,
    "cpu":
}

try:
    connector.container.create_item(body=data)
    print("Dane zostały dodane do kontenera!")
except Exception as e:
    print(f"Błąd podczas dodawania danych: {e}")