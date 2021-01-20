import dash_bootstrap_components as dbc
import dash_html_components as html
from service import ManageDataService, CalculateDataService, PrintTextService, GraphService
import pandas as pd
import plotly.express as px
import numpy as np
import dash_core_components as dcc


def render_page(capital, num_strategies, risk, dd_limit, oos, position_sizing, equity_control, strategy_rotation):

    data = CalculateDataService.load_data(capital, risk)

    if oos:
        data = data[data['oosis'] == 'oos']
    strategy_list = data.strategy.unique()
    all_operations = []
    all_operations_uncontrolled = []
    for strategy in strategy_list:
        name = strategy.replace("\\", "").replace("/", "")
        data_onestrategy = data[data['oosis'] == 'oos'].copy() if oos else data.copy()
        data_onestrategy = data_onestrategy[data_onestrategy['strategy'] == strategy].copy()
        CalculateDataService.calculate_values(data_onestrategy, False, capital, risk, True, True)
        all_operations_uncontrolled.append(data_onestrategy.copy())
        CalculateDataService.calculate_equity_control(data_onestrategy, dd_limit)
        CalculateDataService.calculate_values(data_onestrategy, True, capital, risk, True, True)
        all_operations.append(data_onestrategy)

    data_controlled = pd.concat(all_operations)
    data_controlled = data_controlled.sort_values(by=['date', 'time'])
    data = pd.concat(all_operations_uncontrolled)
    data = data.sort_values(by=['date', 'time'])
    CalculateDataService.calculate_values(data_controlled, True, capital, risk, False, True)
    CalculateDataService.calculate_values(data, False, capital, risk, False, True)

    rotated_portfolio_data = CalculateDataService.rotate_portfolio(data, num_strategies).sort_values(by=['date', 'time'])
    rotated_portfolio_data_controlled = CalculateDataService.rotate_portfolio(data_controlled, num_strategies).sort_values(
        by=['date', 'time'])
    CalculateDataService.calculate_values(rotated_portfolio_data, False, capital, risk, False, True)
    CalculateDataService.calculate_values(rotated_portfolio_data_controlled, True, capital, risk, False, True)

    data["type"] = "Original"
    data_controlled["type"] = "Controlled"
    rotated_portfolio_data["type"] = "Rotated"
    rotated_portfolio_data_controlled["type"] = "ControlledRotated"
    data_original_syncdate = data[
        pd.to_datetime(data['date']) >= pd.to_datetime(rotated_portfolio_data.date.array[0])].copy()
    data_controlled_syncdate = data_controlled[
        pd.to_datetime(data_controlled['date']) >= pd.to_datetime(rotated_portfolio_data.date.array[0])].copy()
    CalculateDataService.calculate_values(data_controlled_syncdate, True, capital, risk, False, True)
    CalculateDataService.calculate_values(data_original_syncdate, False, capital, risk, False, True)

    frames = [data_original_syncdate, data_controlled_syncdate, rotated_portfolio_data,
              rotated_portfolio_data_controlled]

    data_merged = pd.concat(frames)

    data.to_csv(r'Z:/\ts10\strategy_reports/data_uncontrolled.csv', index=True)

    table = pd.pivot_table(data, values='profit_net', index=['date', 'time'],
                           columns=['strategy'], aggfunc=np.sum).fillna(0).cumsum()

    table = table.reset_index().drop(columns=['time'])

    fig = px.line(data, x='date', y='equity_calc_single_strategy', color='strategy')
    fig2 = px.line(data, x='date', y='equity_calc')
    fig3 = px.line(data_controlled, x='date', y='equity_calc_single_strategy', color='strategy')
    fig4 = px.line(data_controlled, x='date', y='equity_calc')
    fig6 = px.line(rotated_portfolio_data, x='date', y='equity_calc')
    fig7 = px.line(rotated_portfolio_data_controlled, x='date', y='equity_calc')
    fig_merged = px.line(data_merged, x='date', y='equity_calc', color='type')

    table_month = pd.pivot_table(data, values='profit_net', index=['year'],
                                 columns=['month'], aggfunc=np.sum).fillna(0)
    table_strategy = pd.pivot_table(data, values='profit_net', index=['strategy'],
                                    columns=['year'], aggfunc=np.sum).fillna(0)

    table_month_controlled = pd.pivot_table(data_controlled, values='profit_net', index=['year'],
                                            columns=['month'], aggfunc=np.sum).fillna(0)
    table_strategy_controlled = pd.pivot_table(data_controlled, values='profit_net', index=['strategy'],
                                               columns=['year'], aggfunc=np.sum).fillna(0)

    data_correlation = data[data.year >= 2020].copy()
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

    fig_corr = px.imshow(data_correlation,
                         labels=dict(x="Day of Week", y="Time of Day", color="Productivity"),
                         x=data_correlation.columns,
                         y=data_correlation.index)
    fig_corr.update_xaxes(side="top")

    content = [
                html.H1('Equities Uncontrolled',
                        style={'textAlign': 'center'}),
                dbc.Row([
                    dbc.Col(dcc.Graph(id='equities_uncontrolled', figure=fig), width=12),
                ]),
                dbc.Row([
                    dbc.Col(dcc.Graph(id='equity_uncontrolled', figure=fig2), width=12),
                ]),
                dbc.Row([
                    dbc.Col(GraphService.draw_data_table(table_month, 'year', 'monthly_return_uncontrolled'), width=6),
                    dbc.Col(GraphService.draw_data_table(table_strategy, 'strategy', 'strategy_return_uncontrolled'), width=6),
                ]),
                html.H1('Equities Controlled',
                        style={'textAlign': 'center'}),
                dbc.Row([
                    dbc.Col(dcc.Graph(id='equities_controlled', figure=fig3), width=12),
                ]),
                dbc.Row([
                    dbc.Col(dcc.Graph(id='equity_controlled', figure=fig4), width=12),
                ]),
                dbc.Row([
                    dbc.Col(GraphService.draw_data_table(table_month_controlled, 'year', 'monthly_return_controlled'), width=8),
                    dbc.Col(GraphService.draw_data_table(table_strategy_controlled, 'strategy', 'strategy_return_controlled'), width=4),
                ]),
                dbc.Row([
                    dbc.Col(dcc.Graph(id='all_equities', figure=fig_merged), width=12),
                ]),
                dbc.Row([
                    dbc.Col(PrintTextService.performance_report(data_original_syncdate, capital, 1), width=3),
                    dbc.Col(PrintTextService.performance_report(data_controlled_syncdate, capital, 1), width=3),
                    dbc.Col(PrintTextService.performance_report(rotated_portfolio_data, capital, 1), width=3),
                    dbc.Col(
                        PrintTextService.performance_report(rotated_portfolio_data_controlled, capital, 1), width=3),
                ]),
                dbc.Row([
                    dbc.Col(dcc.Graph(id='correlation_graph', figure=fig_corr), width=12),
                ]),

    ]
    return content
