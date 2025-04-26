import h5py

def explore_fast5(filepath):
    def print_attrs(name, obj):
        print(name)
        for key, val in obj.attrs.items():
            print(f"  - ATTR {key}: {val}")
    
    with h5py.File(filepath, "r") as f:
        print(f"Struktura pliku {filepath}:")
        f.visititems(print_attrs)

# Podaj ścieżkę do pliku
explore_fast5("../Chiron/chiron/example_data/DNA_input_new_schema/read1.fast5")