import h5py
import os
import argparse

def convert_multi_to_single(multi_fast5_file, output_dir):
    """ Konwertuje multi-FAST5 na pojedyncze FAST5 bez dodatkowej grupy read_xxx """

    with h5py.File(multi_fast5_file, 'r') as multi_f5:
        for read_id in multi_f5.keys():
            single_fast5_path = os.path.join(output_dir, f"{read_id}.fast5")
            with h5py.File(single_fast5_path, 'w') as single_f5:
                raw_reads_group = single_f5.create_group("Raw/Reads")
                multi_f5.copy(f"{read_id}/Raw/Signal", raw_reads_group, name="Signal")
                raw_reads_group.attrs['read_id'] = read_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="multi-FAST5 to single-FAST5")
    parser.add_argument("--multi_fast5_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)

    args = parser.parse_args()
    convert_multi_to_single(args.multi_fast5_path, args.output_path)
