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
#explore_fast5("../test_sample/rodan_sample/a5e44b92-65bb-43d8-87dd-2bc3777859ee.fast5")
explore_fast5("../test_sample/medium/5210_N128870_20180727_FAH82747_MN19691_sequencing_run_Alfred_Imp4restart5_31649_read_9834_ch_461_strand.fast5")