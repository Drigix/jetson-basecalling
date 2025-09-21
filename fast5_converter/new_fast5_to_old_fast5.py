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

def create_sacall_compatible_fast5(signal, attrs, output_path):
    with h5py.File(output_path, "w") as f_out:
        # Create necessary groups
        raw_group = f_out.create_group("Raw")
        reads_group = raw_group.create_group("Reads")
        
        # Generate or reuse read_id
        read_id = attrs.get("read_id", str(uuid.uuid4()))
        read_group = reads_group.create_group(read_id)

        # Add signal
        read_group.create_dataset("Signal", data=signal, dtype='i2')  # int16
        
        # Add attributes
        read_group.attrs["read_id"] = read_id.encode() if isinstance(read_id, str) else read_id
        read_group.attrs["duration"] = attrs.get("duration", len(signal))
        read_group.attrs["start_time"] = attrs.get("start_time", 0)
        read_group.attrs["median_before"] = attrs.get("median_before", 250.0)
        read_group.attrs["read_number"] = attrs.get("read_number", 1)
        read_group.attrs["start_mux"] = attrs.get("start_mux", 1)

        # Create UniqueGlobalKey
        ugk = f_out.create_group("UniqueGlobalKey")

        # channel_id
        ch_id = ugk.create_group("channel_id")
        ch_id.attrs["channel_number"] = attrs.get("channel_number", b"123")
        ch_id.attrs["digitisation"] = attrs.get("digitisation", 8192.0)
        ch_id.attrs["offset"] = attrs.get("offset", 10.0)
        ch_id.attrs["range"] = attrs.get("range", 1467.6)
        ch_id.attrs["sampling_rate"] = attrs.get("sampling_rate", 4000.0)

        # context_tags
        ctx_tags = ugk.create_group("context_tags")
        ctx_tags.attrs.update({
            "experiment_type": b"genomic_dna",
            "sequencing_kit": b"sqk-lsk109",
            "flowcell_type": b"flo-min106",
            "local_basecalling": b"0",
            "sample_frequency": b"4000",
            "fast5_raw": b"1",
            "fast5_output_fastq_in_hdf": b"1"
        })

        # tracking_id
        trk_id = ugk.create_group("tracking_id")
        trk_id.attrs.update({
            "run_id": attrs.get("run_id", str(uuid.uuid4()).replace("-", "").encode()),
            "flow_cell_id": b"FAH00000",
            "device_id": b"MN00000",
            "exp_start_time": b"2025-01-01T00:00:00Z",
            "protocol_run_id": b"12345678-1234-1234-1234-1234567890ab",
            "sample_id": b"sample",
            "operating_system": b"Ubuntu 20.04",
            "asic_version": b"IA02C",
            "device_type": b"minion",
        })

def convert_fast5_file(input_path, output_folder):
    with h5py.File(input_path, "r") as f_in:
        signal, attrs = find_signal(f_in)
        if signal is None:
            print(f"Nie znaleziono sygnału w {input_path}")
            return

        # Zapisz nowy plik
        base_filename = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(output_folder, f"{base_filename}_converted.fast5")
        create_sacall_compatible_fast5(signal, attrs, output_path)
        print(f"Utworzono {output_path}")

# Batch processing
for filename in os.listdir(input_folder):
    if filename.endswith(".fast5"):
        input_path = os.path.join(input_folder, filename)
        convert_fast5_file(input_path, output_folder)

print("Konwersja zakończona.")