from db_config import AzureCosmosConnector

def add_mode_to_container(container_name, connector):
    container = connector.connect_container(container_name)
    for item in container.read_all_items():
        if 'mode' not in item:
            item['mode'] = 0  # Default value for 'mode'
            container.replace_item(item=item, body=item)

def main():
    connector = AzureCosmosConnector()
    add_mode_to_container("SACALL_STATS", connector)
    add_mode_to_container("CHIRON_STATS", connector)
    add_mode_to_container("RODAN_STATS", connector)

if __name__ == "__main__":
    main()