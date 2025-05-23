import os
import h5py
import numpy as np
import uuid

# Foldery
input_folder = "../Chiron/chiron/example_data/DNA_input_new_schema/"  # folder z plikami Chiron
output_folder = "../test_sample/chiron_sample/"  # folder na nowe pliki SACall-style

os.makedirs(output_folder, exist_ok=True)

def find_signal(f):
    """Znajdź pierwszy sygnał w pliku."""
    try:
        reads_group = f["Raw/Reads"]
        for read_name in reads_group:
            read_group = reads_group[read_name]
            if "Signal" in read_group:
                signal = read_group["Signal"][:]
                attrs = dict(read_group.attrs)
                return signal, attrs
    except KeyError:
        pass
    return None, None

def copy_metadata(f_in, f_out):
    """Kopiuj UniqueGlobalKey/channel_id, context_tags, tracking_id."""
    if "UniqueGlobalKey" in f_in:
        src = f_in["UniqueGlobalKey"]
        dst = f_out.create_group("UniqueGlobalKey")
        for group_name in src:
            src_grp = src[group_name]
            dst_grp = dst.create_group(group_name)
            for attr, val in src_grp.attrs.items():
                dst_grp.attrs[attr] = val

def create_sacall_compatible_fast5(signal, attrs, output_path, original_metadata_file):
    with h5py.File(output_path, "w") as f_out:
        # Create necessary groups
        read_id = attrs.get("read_id", str(uuid.uuid4()))  # albo z oryginału albo nowy
        read_group = f_out.create_group(f"Raw/Reads/{read_id}")
        raw_group = f_out["Raw"]

        # Add signal
        read_group.create_dataset("Signal", data=signal, dtype='i2')  # typ sygnału to zazwyczaj int16 (i2)

        # Copy or create dummy attributes
        read_group.attrs["start_time"] = attrs.get("start_time", 0)
        read_group.attrs["duration"] = attrs.get("duration", len(signal))
        read_group.attrs["read_id"] = read_id

        # Kopiuj lub stwórz metadane
        copy_metadata(original_metadata_file, f_out)

def convert_fast5_file(input_path, output_folder):
    with h5py.File(input_path, "r") as f_in:
        signal, attrs = find_signal(f_in)
        if signal is None:
            print(f"Nie znaleziono sygnału w {input_path}")
            return

        # Zapisz nowy plik
        base_filename = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(output_folder, f"{base_filename}_converted.fast5")
        create_sacall_compatible_fast5(signal, attrs, output_path, f_in)
        print(f"Utworzono {output_path}")

# Batch processing
for filename in os.listdir(input_folder):
    if filename.endswith(".fast5"):
        input_path = os.path.join(input_folder, filename)
        convert_fast5_file(input_path, output_folder)

print("Konwersja zakończona.")