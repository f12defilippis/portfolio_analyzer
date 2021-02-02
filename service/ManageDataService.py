import glob
import os
import pandas as pd
import numpy as np

from service import CalculateDataService


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


def get_rotated_data(data_original_nomm, data, num_strategies, capital, risk, method, how_many_month, monthly_or_weekly, controlled):
    data_rotated = CalculateDataService.rotate_portfolio(data_original_nomm, data, num_strategies, method, how_many_month, monthly_or_weekly)
    table_month_rotated = pd.DataFrame()
    if not data_rotated.empty:
        data_rotated = data_rotated.sort_values(by=['date', 'time'])
        CalculateDataService.calculate_values(data_rotated, controlled, capital, risk, False, True)
        table_month_rotated = pd.pivot_table(data_rotated, values='profit_net', index=['year'],
                                             columns=['month'], aggfunc=np.sum).fillna(0)
    return data_rotated, table_month_rotated


def get_summary(data, data_controlled, data_rotated, data_controlled_rotated,
                                                                         data_rotated_corr, data_controlled_rotated_corr,
                                                                         capital, risk):
    data_merged = CalculateDataService.calculate_data_merged(data, data_controlled, data_rotated, data_controlled_rotated,
                                                                         data_rotated_corr, data_controlled_rotated_corr,
                                                                         capital, risk)

    data_merged.to_csv(r'Z:\portfolio_analyzer/data_merged.csv')

    all_summaries = []

    all_types = data_merged["type"].unique()
    for one_type in all_types:
        data_selected = data_merged[data_merged.type == one_type]
        summary = pd.DataFrame()
        first_trade = data_selected.iloc[1:2, :]
        CalculateDataService.calculate_strategy_summary(summary, first_trade, data_selected)
        summary["type"] = one_type
        all_summaries.append(summary)

    data_merged_summary = pd.concat(all_summaries)
    return data_merged, data_merged_summary

