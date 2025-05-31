from db_config import AzureCosmosConnector
import uuid
import argparse
import csv
import json

BEST_EXEC_TIME_WITH_BATCH_SIZE_QUERY = """
SELECT TOP 1 c.execution_time / c.file_size AS best_time, c.id, c.batch_size, c.execution_time, c.file_size
FROM c
WHERE c.batch_size = @batch_size
ORDER BY best_time ASC
"""

BEST_EXEC_TIME_BY_FILE_SIZE_AND_BATCH_SIZE_QUERY = """
SELECT *
FROM c
WHERE c.file_size = @file_size AND c.batch_size = @batch_size
ORDER BY c.execution_time ASC
"""

BEST_EXEC_TIME_BY_FILE_SIZE_AND_BATCH_SIZE_AND_MODE_QUERY = """
SELECT *
FROM c
WHERE c.file_size = @file_size AND c.batch_size = @batch_size AND c.mode = @mode
ORDER BY c.execution_time ASC
"""

def read_execution_statistics(file_path):
    """Reads execution statistics from CSV file (file_size, execution_time, batch_size)."""
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)
        values = next(reader)

        data_dict = dict(zip(headers, map(float, values))) 
        return {
            "file_size": data_dict.get("file_size", 0.0),
            "execution_time": data_dict.get("execution_time", 0.0),
            "batch_size": int(data_dict.get("batch_size", 0)),
            "mode": int(data_dict.get("mode", 0))
        }

def read_jetson_metrics(file_path):
    """Reads metrics from CSV file and converts values to appropriate types."""
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)
        values = next(reader)
        metrics = []
        for row in reader:
            metric = {
                "time": float(row[0]),
                "ram": float(row[1]),
                "cpu": float(row[2]),
                "temp_cpu": float(row[3])
            }
            metrics.append(metric)

        return metrics
    
def insert_data(container_name, execution_stat_file, jetson_metrics_file):
    # Connect to Cosmos DB with the provided database name
    connector = AzureCosmosConnector()
    connector.connect_container(container_name)

    # Read data from CSV files
    execution_data = read_execution_statistics(execution_stat_file)
    metrics_data = read_jetson_metrics(jetson_metrics_file)

    # Prepare the data object
    data = {
        "id": str(uuid.uuid4()),
        **execution_data,  # Merge execution statistics into main dictionary
        "metrics": metrics_data
    }

    try:
       connector.container.create_item(body=data)
       print("Data has been added to container!")
    except Exception as e:
        print(f"Error during process data to container: {e}")

def find_best_execution_time_by_batch_size(container_name, batch_size):
    try:
        # Connect to Cosmos DB with the provided database name
        connector = AzureCosmosConnector()
        connector.connect_container(container_name)
        
        parameters = [{"name": "@batch_size", "value": batch_size}]
        
        items = list(connector.container.query_items(query=BEST_EXEC_TIME_WITH_BATCH_SIZE_QUERY, parameters=parameters, enable_cross_partition_query=True))
        return items[0] if items else None
    except Exception as e:
        print(f"Error during query execution: {e}")
        return None
    
def find_best_execution_by_file_size_and_batch_size(container_name, file_size, batch_size):
    try:
        # Connect to Cosmos DB with the provided database name
        connector = AzureCosmosConnector()
        connector.connect_container(container_name)
        parameters = [{"name": "@batch_size", "value": batch_size}, {"name": "@file_size", "value": file_size}]
        
        items = list(connector.container.query_items(query=BEST_EXEC_TIME_BY_FILE_SIZE_AND_BATCH_SIZE_QUERY, parameters=parameters, enable_cross_partition_query=True))
        return items[0] if items else None
    except Exception as e:
        print(f"Error during query execution: {e}")
        return None
    
def find_best_execution_by_file_size_and_batch_size_and_mode(container_name, file_size, batch_size, mode):
    try:
        # Connect to Cosmos DB with the provided database name
        connector = AzureCosmosConnector()
        connector.connect_container(container_name)
        parameters = [{"name": "@batch_size", "value": batch_size}, {"name": "@file_size", "value": file_size}, {"name": "@mode", "value": mode}]
        
        items = list(connector.container.query_items(query=BEST_EXEC_TIME_BY_FILE_SIZE_AND_BATCH_SIZE_AND_MODE_QUERY, parameters=parameters, enable_cross_partition_query=True))
        resultItem = items[0] if items else None
        avg_execution_time = count_avg_execution_time(items)
        if resultItem is not None:
            resultItem['avg_execution_time'] = avg_execution_time
        return resultItem
    except Exception as e:
        print(f"Error during query execution: {e}")
        return None  
    
def find_avg_execution_by_file_size_and_batch_size_and_mode(container_name, file_size, batch_size, mode):
    try:
        # Connect to Cosmos DB with the provided database name
        connector = AzureCosmosConnector()
        connector.connect_container(container_name)
        parameters = [
            {"name": "@batch_size", "value": batch_size},
            {"name": "@file_size", "value": file_size},
            {"name": "@mode", "value": mode}
        ]
        
        items = list(connector.container.query_items(
            query=BEST_EXEC_TIME_BY_FILE_SIZE_AND_BATCH_SIZE_AND_MODE_QUERY,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        return count_avg_execution_time(items)
    except Exception as e:
        print(f"Error during query execution: {e}")
        return None  

def count_avg_execution_time(items):
    if not items:
        return None
     # Extract execution_time and calculate the average
    execution_times = [item.get("execution_time", 0) for item in items if "execution_time" in item]
    if not execution_times:
        return None
        
    avg_execution_time = sum(execution_times) / len(execution_times)
    return avg_execution_time

def main():
    parser = argparse.ArgumentParser(description="Insert data into Cosmos DB")
    parser.add_argument("--query_type", type=str, required=True, help="Type of query to execute")
    parser.add_argument("--container_name", type=str, help="Cosmos container name")
    
    # Parameters to create record
    parser.add_argument("--execution_stat_file", type=str, help="Path to execution_statistic.csv")
    parser.add_argument("--jetson_metrics_file", type=str, help="Path to jetson_metrics.csv")
    
    # Parameters to find records
    parser.add_argument("--batch_size", type=int, help="Current basecalling batch size")
    parser.add_argument("--jetson_mode", type=int, help="Current basecalling batch size")

    args = parser.parse_args()

    if args.query_type == "INSERT":
        if args.execution_stat_file and args.jetson_metrics_file:
            insert_data(args.container_name, args.execution_stat_file, args.jetson_metrics_file)
        else:
            print("Both execution_stat_file and jetson_metrics_file are required for INSERT query type.")
    elif args.query_type == "FIND":
        file_size = read_execution_statistics(args.execution_stat_file).get("file_size", None)
        if args.batch_size is not None and file_size is not None:
            if args.jetson_mode is not None:
                return find_best_execution_by_file_size_and_batch_size_and_mode(args.container_name, file_size, args.batch_size, args.jetson_mode)
            return find_best_execution_by_file_size_and_batch_size(args.container_name, file_size, args.batch_size)
        else:
            print("batch_size is required for FIND query type.")
    elif args.query_type == "FIND_CURRENT_EXECUTION_TIME":
        return read_execution_statistics(args.execution_stat_file).get("execution_time", None)
    elif args.query_type == "FIND_CURRENT_METRICS":
        return read_jetson_metrics(args.jetson_metrics_file)
    elif args.query_type == "FIND_AVG_EXECUTION_TIME":
        return find_avg_execution_by_file_size_and_batch_size_and_mode(args.container_name, file_size, args.batch_size, args.jetson_mode)
    else:
        print("Invalid query_type. Use 'INSERT' or 'FIND'.")

if __name__ == "__main__":
    result = main()
    print(json.dumps(result))