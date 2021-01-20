import numpy as np
import pandas as pd
import Utils
from dateutil.relativedelta import relativedelta
from service import ManageDataService


def load_data(capital, risk):
    data_original = ManageDataService.load_all_csv_by_folder(r'Z:\ts10\strategy_reports\reports\selezione')
    data_anagrafica = pd.read_csv(r'Z:/\ts10\strategy_reports/strategy_list.txt')

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

    return data


def calculate_values(data, have_enabled, capital, risk, single_strategy, position_sizing):
    max_margin_per_position = int(capital * 0.15)

    data['max_con'] = (max_margin_per_position / data['margin'] / data['unity']).astype(int)
    data['calculated_con'] = ((capital * risk / 100) / (data['stop'] * data['unity'])).astype(int)

    data['ncon'] = np.where(data['calculated_con'] > data['max_con'], data['max_con'], data['calculated_con']) if position_sizing else 1

    if have_enabled:
        data['multiplier'] = data['enabled'].fillna(1) * data['ncon'] * data['unity']
    else:
        data['multiplier'] = data['ncon'] * data['unity']
    data['profit_net'] = (data['profit'] - data['slippage']) * data['multiplier']
    data['equity_calc'] = data['profit_net'].cumsum()
    if single_strategy:
        data['equity_calc_single_strategy'] = data['profit_net'].cumsum()
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


def rotate_portfolio(data, num_strategies):
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

            table_strategy = calculate_ranking_npavgdd(data[pd.to_datetime(data['date']) <= date_ref], date_ref)
            selected_strategies = table_strategy.iloc[1:number_of_live_strategies + 1, :].index.unique().to_numpy()
            for strategy in selected_strategies:
                selected_trade = data[data.strategy == strategy].copy()
                mask = (pd.to_datetime(selected_trade['date']) >= date_ref) & (
                            pd.to_datetime(selected_trade['date']) < date_ref_next_month)
                selected_trade = selected_trade.loc[mask]
                live_trade.append(selected_trade)

    rotated_portfolio_data = pd.concat(live_trade)
    return rotated_portfolio_data


def calculate_ranking_npavgdd(data, date_ref):
    one_year_ago = date_ref - relativedelta(months=12)
    data_filtered = data[pd.to_datetime(data['date']) > one_year_ago].copy()

    table_strategy_np = pd.pivot_table(data_filtered, values='profit_net', index=['strategy'], aggfunc=np.sum).fillna(0)
    table_strategy_dd = pd.pivot_table(data_filtered[data_filtered.drawdown < 0], values='drawdown', index=['strategy'],
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
    table_strategy['npavgdd'] = round(table_strategy.profit_net / table_strategy.drawdown * -1, 2)
    table_strategy = table_strategy.sort_values(by=['npavgdd'], ascending=False)
    return table_strategy[table_strategy.profit_net > 0]


def calculate_strategy_summary(strategy, first_trade, selected_trade):
    strategy['slippage'] = first_trade['slippage']
    strategy['stop_loss'] = first_trade['stop'] * first_trade['unity']
    strategy['oos_from'] = first_trade['oos_from']
    strategy['profit'] = selected_trade['profit_net'].sum()
    strategy['max_dd'] = selected_trade['max_drawdown'].min() * -1
    strategy['np_maxdd'] = round(strategy['profit'] / strategy['max_dd'], 2)
    strategy['num_trades'] = selected_trade['profit_net'].count()
    strategy['avg_trade'] = round(strategy['profit'] / strategy['num_trades'], 2)
    strategy['perc_profit'] = round(selected_trade[selected_trade['profit_net'] > 0].profit_net.count() / selected_trade.profit_net.count(), 2)
    strategy['worst_trade'] = selected_trade['profit_net'].min() * -1
    grouped_st = selected_trade.groupby(by=["month", "year"], dropna=False)['profit_net'].sum()
    strategy['worst_month'] = grouped_st.min() * -1
    strategy['avg_loosing_month'] = grouped_st[grouped_st < 0].mean() * -1
    today, one_month_ago, six_month_ago, one_year_ago = Utils.get_dates_from_today()
    one_month_ago_trade = selected_trade[pd.to_datetime(selected_trade['date']) >= pd.to_datetime(one_month_ago)].copy()
    six_month_ago_trade = selected_trade[pd.to_datetime(selected_trade['date']) >= pd.to_datetime(six_month_ago)].copy()
    one_year_ago_trade = selected_trade[pd.to_datetime(selected_trade['date']) >= pd.to_datetime(one_year_ago)].copy()
    strategy['profit_1m'] = one_month_ago_trade['profit_net'].sum()
    strategy['profit_6m'] = six_month_ago_trade['profit_net'].sum()
    strategy['profit_1y'] = one_year_ago_trade['profit_net'].sum()