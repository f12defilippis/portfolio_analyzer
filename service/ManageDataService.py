import glob
import os
import pandas as pd


def load_all_csv_by_folder(folder_path):
    all_files = glob.glob(
        os.path.join(folder_path, "*.csv"))  # advisable to use os.path.join as this makes concatenation OS independent
    df_from_each_file = (pd.read_csv(f) for f in all_files)
    data_original = pd.concat(df_from_each_file, ignore_index=True)
    return data_original


def merge_dataframe(data_original, data_anagrafica):
    data = pd.merge(
        data_original,
        data_anagrafica,
        how="inner",
        on="strategy",
        left_on=None,
        right_on=None,
        left_index=False,
        right_index=False,
        sort=True,
        suffixes=("_x", "_y"),
        copy=True,
        indicator=False,
        validate=None,
    )
    return data
