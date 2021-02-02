import numpy as np
import pandas as pd
import Utils
from dateutil.relativedelta import relativedelta
from service import ManageDataService
from scipy import stats
import math


def load_data(capital, risk):
    data_original = ManageDataService.load_all_csv_by_folder(r'Z:\portfolio_analyzer\reports')
    data_anagrafica = pd.read_csv(r'Z:\portfolio_analyzer/strategy_list.txt')

    data = ManageDataService.merge_dataframe(data_original, data_anagrafica)
    data['strategy'] = data.strategy.str.replace('/\_', '', regex=False)
    # calculate data
    data_anagrafica['ncon'] = ((capital * risk / 100) / (data_anagrafica['stop'] * data_anagrafica['unity'])).astype(
        int)
    data_anagrafica['multiplier'] = data_anagrafica['ncon'] * data_anagrafica['unity']
    data_anagrafica['margin_used'] = data_anagrafica['margin'] * data_anagrafica['multiplier']
    margin_used = data_anagrafica['margin_used'].sum()
    data = data.sort_values(by='date')
    data['month'] = pd.DatetimeIndex(data['date']).month
    data['year'] = pd.DatetimeIndex(data['date']).year
    data['week'] = pd.DatetimeIndex(data['date']).week

    return data


def calculate_values(data, have_enabled, capital, risk, single_strategy, position_sizing, slippage=True):
    max_margin_per_position = int(capital * 0.15)

    data['max_con'] = (max_margin_per_position / data['margin'] / data['unity']).astype(int)
    data['calculated_con'] = ((capital * risk / 100) / (data['stop'] * data['unity'])).astype(int)

    data['ncon'] = np.where(data['calculated_con'] > data['max_con'], data['max_con'], data['calculated_con']) if position_sizing else 1

    if have_enabled:
        data['multiplier'] = data['enabled'].fillna(1) * data['ncon'] * data['unity']
    else:
        data['multiplier'] = data['ncon'] * data['unity']
    data['profit_net'] = (data['profit'] - data['slippage']) * data['multiplier'] if slippage else data['profit'] * data['multiplier']
    data['equity_calc'] = data['profit_net'].cumsum()
    if single_strategy:
        data['equity_calc_single_strategy'] = data['profit_net'].cumsum()
        data['drawdown_single_strategy'] = data['equity_calc_single_strategy'] - data['equity_calc_single_strategy'].max()
    data['equity_peak'] = data['equity_calc'].cummax()
    data['drawdown'] = data['equity_calc'] - data['equity_peak']
    data['max_drawdown'] = data['drawdown'].cummin()
    data['ddOnCapital'] = data['drawdown'] / (capital + data['equity_calc']) * 100
    data['unita'] = 1
    data['contatore'] = data.unita.cumsum()
    data['avg_trade'] = data['equity_calc'] / data[data['profit_net'] != 0].profit_net.count()
    data['avg_trade_rolling20'] = data[data['profit_net'] != 0].profit_net.rolling(20).mean().fillna(0)
    data['slippage_paid'] = data['multiplier'] * data['slippage']


def calculate_equity_control(data, ddlimit):
    data['new_drawdown'] = np.where(
        (data['drawdown'] * -1 > ddlimit) & (data['drawdown'] < data['max_drawdown'].shift(1)), True, False)
    data['equity_mean50'] = data['equity_calc'].rolling(50).mean()
    data['equity_std50'] = data['equity_calc'].rolling(50).std()
    data['upper_band501'] = data['equity_mean50'] + data['equity_std50']
    data['lower_band501'] = data['equity_mean50'] - data['equity_std50']
    data['stop_trigger'] = np.where((data['new_drawdown']) | (data['lower_band501'] > data['equity_calc']), -1,
                                    0)
    data['stopping_point'] = np.where(data['stop_trigger'] < 0, data['equity_calc'], 0)
    data['restart_trigger'] = np.where(
        (data['upper_band501'] < data['equity_calc']) & (data['stopping_point'].shift(1) < data['equity_calc']), 1,
        np.where(data['equity_calc'] > data['equity_peak'].shift(1), 1, 0))
    data['stopping_point'] = np.where(data['restart_trigger'] <= 0, data['stopping_point'].shift(1), data['stopping_point'])

    data['enabled'] = equitycontrol_generator(data.stop_trigger, data.restart_trigger)


def equitycontrol_generator(stop_trigger, restart_trigger):
    service_dataframe = pd.DataFrame(index=stop_trigger.index)
    service_dataframe['stop_trigger'] = stop_trigger
    service_dataframe['restart_trigger'] = restart_trigger

    status = 1
    enabled = []

    for (a, b) in zip(stop_trigger, restart_trigger):
        if status == 1:
            if a == -1:
                status = 0
        else:
            if b == 1:
                status = 1

        enabled.append(status)

    service_dataframe['enabled_new'] = enabled
    service_dataframe.enabled_new = service_dataframe.enabled_new.shift(1)
    return service_dataframe.enabled_new


def rotate_portfolio(data_original_nomm, data, num_strategies, method, how_many_months, monthly_or_weekly):
    number_of_live_strategies = num_strategies
    live_trade = []
    first_date = pd.to_datetime(data.iloc[1:2, :1].date.max())
    first_year = first_date.year
    first_month = first_date.month
    for year in range(first_year + 1, 2022):
        if year == (first_year + 1):
            m = first_month
        else:
            m = 1
        for month in range(m, 13):
            date_ref = Utils.get_first_saturday_of_month(year, month)
            next_month = month + 1
            next_month_year = year
            if month == 12:
                next_month = 1
                next_month_year = year + 1
            date_ref_next_month = Utils.get_first_saturday_of_month(next_month_year, next_month)

            table_strategy = pd.DataFrame()
            if method == "np_avgdd":
                table_strategy = calculate_ranking_npavgdd(data_original_nomm[pd.to_datetime(data['date']) <= date_ref], date_ref)
            elif method == "np_corr":
                table_strategy = calculate_ranking_npcorr(data_original_nomm[pd.to_datetime(data['date']) <= date_ref], date_ref, how_many_months, monthly_or_weekly)
            selected_strategies = table_strategy.iloc[1:number_of_live_strategies + 1, :].index.unique().to_numpy()
            for strategy in selected_strategies:
                selected_trade = data[data.strategy == strategy].copy()
                mask = (pd.to_datetime(selected_trade['date']) >= date_ref) & (
                            pd.to_datetime(selected_trade['date']) < date_ref_next_month)
                selected_trade = selected_trade.loc[mask]
                live_trade.append(selected_trade)
            print("Method: " + str(method) + " Period: " + str(how_many_months) + " Type: " + monthly_or_weekly + " Year: " + str(year) + " Month: " + str(month) + " Trade size: " + str(len(live_trade)))
            print(selected_strategies)
            print("-------------------------------------")

    rotated_portfolio_data = pd.DataFrame()
    if len(live_trade) > 0:
        rotated_portfolio_data = pd.concat(live_trade)
    return rotated_portfolio_data


def calculate_ranking_npavgdd(data, date_ref):
    one_year_ago = date_ref - relativedelta(months=12)
    data_filtered = data[pd.to_datetime(data['date']) > one_year_ago].copy()

    table_strategy_np = pd.pivot_table(data_filtered, values='profit_net', index=['strategy'], aggfunc=np.sum).fillna(0)
    table_strategy_dd = pd.pivot_table(data_filtered[data_filtered.drawdown_single_strategy < 0], values='drawdown_single_strategy', index=['strategy'],
                                       aggfunc=np.mean).fillna(0)
    table_strategy = pd.merge(
        table_strategy_np,
        table_strategy_dd,
        how="inner",
        on="strategy",
        left_on=None,
        right_on=None,
        left_index=False,
        right_index=False,
        sort=False,
        suffixes=("_x", "_y"),
        copy=True,
        indicator=False,
        validate=None
    )
    table_strategy['npavgdd'] = round(table_strategy.profit_net / table_strategy.drawdown_single_strategy * -1, 2)
    table_strategy = table_strategy.sort_values(by=['npavgdd'], ascending=False)
    return table_strategy[table_strategy.profit_net > 0]


def calculate_ranking_npcorr(data, date_ref, how_many_months, method):
    one_year_ago = date_ref - relativedelta(months=12)
    data_filtered = data[pd.to_datetime(data['date']) > one_year_ago].copy()

    table_strategy_np = pd.pivot_table(data_filtered, values='profit_net', index=['strategy'], aggfunc=np.sum).fillna(0)
    strategy_list = table_strategy_np.index.tolist()
    table_strategy_np["correlation_index"] = 0

    correlation_index = table_strategy_np.index.size
    while data_filtered.size > 0:
        data_correlated = correlate_data_with_parameter(data_filtered, how_many_months, method)
        strategy_correlated_sorted = data_correlated.sum().sort_values(ascending=False).index.values
        strategy_max_correlated = strategy_correlated_sorted[0]
        table_strategy_np.loc[table_strategy_np.index == strategy_max_correlated, 'correlation_index'] = correlation_index
        data_filtered = data_filtered[data_filtered.strategy != strategy_max_correlated]
        correlation_index = correlation_index - 1


    table_strategy_np = table_strategy_np.sort_values(by=['correlation_index'], ascending=True)

    return table_strategy_np[table_strategy_np.profit_net > 0]



def calculate_strategy_summary(strategy, first_trade, selected_trade):
    selected_trade['one'] = 1
    selected_trade['cumcount'] = selected_trade['one'].cumsum()
    operation_per_year = selected_trade.groupby('year').sum()['one'].max()
    slope, intercept, r_value, p_value, std_err = stats.linregress(selected_trade['cumcount'], selected_trade['equity_calc'].array)

    k_ratio = (slope / std_err) * (math.sqrt(operation_per_year) / selected_trade['one'].count())

    strategy['slippage'] = first_trade['slippage']
    strategy['stop_loss'] = first_trade['stop'] * first_trade['unity']
    strategy['oos_from'] = first_trade['oos_from']
    strategy['profit'] = selected_trade['profit_net'].sum()
    strategy['max_dd'] = selected_trade['max_drawdown'].min() * -1
    strategy['np_maxdd'] = round(strategy['profit'] / strategy['max_dd'], 2)
    strategy['num_trades'] = selected_trade[selected_trade['profit_net'] != 0].profit_net.count()
    strategy['avg_trade'] = round(strategy['profit'] / strategy['num_trades'], 2)
    strategy['profit_factor'] = round(selected_trade[selected_trade['profit_net'] > 0].profit_net.sum() / selected_trade[selected_trade['profit_net'] < 0].profit_net.sum() * -1, 2)
    strategy['k_ratio'] = round(k_ratio, 2)
    strategy['perc_profit'] = round(selected_trade[selected_trade['profit_net'] > 0].profit_net.count() / selected_trade.profit_net.count(), 2)
    strategy['worst_trade'] = selected_trade['profit_net'].min() * -1
    grouped_st = selected_trade.groupby(by=["month", "year"], dropna=False)['profit_net'].sum()
    strategy['worst_month'] = grouped_st.min() * -1
    strategy['avg_loosing_month'] = grouped_st[grouped_st < 0].mean() * -1
    today, one_month_ago, three_month_ago, six_month_ago, nine_month_ago, one_year_ago = Utils.get_dates_from_today()
    one_month_ago_trade = selected_trade[pd.to_datetime(selected_trade['date']) >= pd.to_datetime(one_month_ago)].copy()
    three_month_ago_trade = selected_trade[pd.to_datetime(selected_trade['date']) >= pd.to_datetime(three_month_ago)].copy()
    six_month_ago_trade = selected_trade[pd.to_datetime(selected_trade['date']) >= pd.to_datetime(six_month_ago)].copy()
    nine_month_ago_trade = selected_trade[pd.to_datetime(selected_trade['date']) >= pd.to_datetime(nine_month_ago)].copy()
    one_year_ago_trade = selected_trade[pd.to_datetime(selected_trade['date']) >= pd.to_datetime(one_year_ago)].copy()
    strategy['profit_1m'] = one_month_ago_trade['profit_net'].sum()
    strategy['profit_3m'] = three_month_ago_trade['profit_net'].sum()
    strategy['profit_6m'] = six_month_ago_trade['profit_net'].sum()
    strategy['profit_9m'] = nine_month_ago_trade['profit_net'].sum()
    strategy['profit_1y'] = one_year_ago_trade['profit_net'].sum()
    sel_copy = selected_trade.copy()
    calculate_values(sel_copy, False, 30000, 2.5, True, False, slippage=False)
    calculate_equity_control(sel_copy, 3000)
    strategy['enabled'] = sel_copy.iloc[len(sel_copy)-1].enabled


def get_controlled_and_uncontrolled_data(data, capital, risk, dd_limit):
    strategy_list = data.strategy.unique()
    all_operations = []
    all_operations_uncontrolled = []
    all_operations_uncontrolled_nomm = []
    for strategy in strategy_list:
        name = strategy.replace("\\", "").replace("/", "")
        data_onestrategy_nomm = data[data['strategy'] == strategy].copy()
        calculate_values(data_onestrategy_nomm, False, capital, risk, True, False)
        all_operations_uncontrolled_nomm.append(data_onestrategy_nomm.copy())

        data_onestrategy = data[data['strategy'] == strategy].copy()
        calculate_values(data_onestrategy, False, capital, risk, True, True)
        all_operations_uncontrolled.append(data_onestrategy.copy())

        calculate_values(data_onestrategy, False, capital, risk, True, False, slippage=False)
        calculate_equity_control(data_onestrategy, dd_limit)
        calculate_values(data_onestrategy, True, capital, risk, True, True)
        all_operations.append(data_onestrategy)

    data_controlled = pd.concat(all_operations)
    data_controlled = data_controlled.sort_values(by=['date', 'time'])
    data_uncontrolled = pd.concat(all_operations_uncontrolled)
    data_uncontrolled = data_uncontrolled.sort_values(by=['date', 'time'])
    data_uncontrolled_nomm = pd.concat(all_operations_uncontrolled_nomm)
    data_uncontrolled_nomm = data_uncontrolled_nomm.sort_values(by=['date', 'time'])
    calculate_values(data_controlled, True, capital, risk, False, True)
    calculate_values(data_uncontrolled, False, capital, risk, False, True)
    calculate_values(data_uncontrolled_nomm, False, capital, risk, False, False)

    table_month = pd.pivot_table(data_uncontrolled, values='profit_net', index=['year'],
                                 columns=['month'], aggfunc=np.sum).fillna(0)

    table_month_controlled = pd.pivot_table(data_controlled, values='profit_net', index=['year'],
                                            columns=['month'], aggfunc=np.sum).fillna(0)

    return data_controlled, data_uncontrolled, data_uncontrolled_nomm, table_month, table_month_controlled


def calculate_data_merged(data, data_controlled, data_rotated, data_controlled_rotated,
                                                                         data_rotated_corr, data_controlled_rotated_corr,
                                                                         capital, risk):
    data["type"] = "Original"
    data_controlled["type"] = "Controlled"
    data_rotated["type"] = "Rotated"
    data_controlled_rotated["type"] = "ControlledRotated"
    data_rotated_corr["type"] = "Rotated Corr"
    data_controlled_rotated_corr["type"] = "ControlledRotatedCorr"

    if len(data_rotated) > 0:
        data_syncdate = data[
            pd.to_datetime(data['date']) >= pd.to_datetime(data_rotated.date.array[0])].copy()
        calculate_values(data_syncdate, False, capital, risk, False, True)
    else:
        data_syncdate = data.copy()


    if len(data_controlled_rotated) > 0:
        data_controlled_syncdate = data_controlled[
            pd.to_datetime(data_controlled['date']) >= pd.to_datetime(data_controlled_rotated.date.array[0])].copy()
        calculate_values(data_controlled_syncdate, True, capital, risk, False, True)
    else:
        data_controlled_syncdate = data_controlled.copy()

    frames = [data_syncdate, data_controlled_syncdate, data_rotated,
              data_controlled_rotated, data_rotated_corr, data_controlled_rotated_corr]

    data_merged = pd.concat(frames)
    return data_merged


def correlate(data):
    data_correlation = data[data.year >= (data.year.max()-1)].copy()
    correlation_table = pd.pivot_table(data_correlation, values='profit_net', index=['year', 'month'],
                                       columns=['strategy'], aggfunc=np.sum).fillna(0)
    watchlist = correlation_table.columns.tolist()
    equity_df = pd.DataFrame()
    for ticker in watchlist:
        equity_df[ticker] = correlation_table[ticker].cumsum()
    change_df = pd.DataFrame()
    for ticker in watchlist:
        change_df[ticker] = equity_df[ticker].pct_change().fillna(0)

    data_correlation = change_df.corr()
    return data_correlation


def correlate_data_with_parameter(data, how_many_months_back, method):
    last_date = Utils.get_last_date_from_dataframe(data, "date")
    date_ref = last_date - relativedelta(months=how_many_months_back)
    data_correlation = data[pd.to_datetime(data['date']) >= date_ref].copy()

    correlation_table = pd.pivot_table(data_correlation, values='profit_net', index=['year', 'month' if method == 'month' else 'week'],
                                       columns=['strategy'], aggfunc=np.sum).fillna(0)
    watchlist = correlation_table.columns.tolist()
    equity_df = pd.DataFrame()
    for ticker in watchlist:
        equity_df[ticker] = correlation_table[ticker].cumsum()
    change_df = pd.DataFrame()
    for ticker in watchlist:
        change_df[ticker] = equity_df[ticker].pct_change().fillna(0)

    data_correlation = change_df.corr()
    return data_correlation
