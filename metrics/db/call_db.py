from db_config import AzureCosmosConnector
import uuid
import argparse
import csv

def read_execution_statistics(file_path):
    """Reads execution statistics from CSV file (file_size, execution_time, batch_size)."""
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)  # Read header row
        values = next(reader)   # Read first data row

        data_dict = dict(zip(headers, map(float, values)))  # Convert to dict with float values
        return {
            "file_size": data_dict.get("file_size", 0.0),
            "execution_time": data_dict.get("execution_time", 0.0),
            "batch_size": int(data_dict.get("batch_size", 0))  # Convert batch_size to int
        }

def read_jetson_metrics(file_path):
    """Reads metrics from CSV file and converts values to appropriate types."""
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)  # Read header row
        values = next(reader)
        metrics = []
        for row in reader:
            metric = {
                "time": float(row[0]),      # Convert time to float
                "ram": float(row[1]),       # Convert RAM to float
                "cpu": float(row[2]),       # Convert CPU to float
                "temp_cpu": float(row[3])   # Convert CPU temp to float
            }
            metrics.append(metric)

        return metrics

def main():
    parser = argparse.ArgumentParser(description="Insert data into Cosmos DB")
    parser.add_argument("container_name", type=str, help="Cosmos container name")
    parser.add_argument("execution_stat_file", type=str, help="Path to execution_statistic.csv")
    parser.add_argument("jetson_metrics_file", type=str, help="Path to jetson_metrics.csv")
    args = parser.parse_args()

    # Connect to Cosmos DB with the provided database name
    connector = AzureCosmosConnector()
    connector.connect_container(args.container_name)

    # Read data from CSV files
    execution_data = read_execution_statistics(args.execution_stat_file)
    metrics_data = read_jetson_metrics(args.jetson_metrics_file)

    # Prepare the data object
    data = {
        "id": str(uuid.uuid4()),
        **execution_data,  # Merge execution statistics into main dictionary
        "metrics": metrics_data
    }

    # Insert into Cosmos DB
    try:
       connector.container.create_item(body=data)
       print("Data has been added to container!")
    except Exception as e:
        print(f"Error during process data to container: {e}")

if __name__ == "__main__":
    main()