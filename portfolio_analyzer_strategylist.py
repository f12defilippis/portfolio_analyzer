import dash_bootstrap_components as dbc
import dash_html_components as html
from service import CalculateDataService
import pandas as pd
from dash_table import FormatTemplate
import dash_table
import portfolio_analyzer_strategy_modal as pasm


def render_page(capital, risk, num_strategies):
    data = CalculateDataService.load_data(capital, risk)
    sl = data['strategy'].unique()
    all_strategies = []
    for s in sl:
        selected_trade = data[data.strategy == s].copy()
        CalculateDataService.calculate_values(selected_trade, False, capital, risk, True, False)
        strategy = pd.DataFrame()
        first_trade = selected_trade.iloc[1:2, :]
        strategy['name'] = first_trade['strategy']
        strategy['symbol'] = first_trade['d1_symbol']
        strategy['class'] = first_trade['strategy_type']
        CalculateDataService.calculate_strategy_summary(strategy, first_trade, selected_trade)

        all_strategies.append(strategy)

    strategy_list = pd.concat(all_strategies)
    money = FormatTemplate.money(2)
    # percentage = FormatTemplate.percentage(2)

    columns = [
        dict(id='name', name='Strategy'),
        dict(id='symbol', name='Symbol'),
        dict(id='class', name='Class'),
        dict(id='slippage', name='Slippage', type='numeric', format=money),
        dict(id='stop_loss', name='Stop Loss', type='numeric', format=money),
        dict(id='oos_from', name='OOS From'),
        dict(id='profit', name='Profit', type='numeric', format=money),
        dict(id='max_dd', name='Max Drawdown', type='numeric', format=money),
        dict(id='np_maxdd', name='NP / Max DD', type='numeric'),
        dict(id='num_trades', name='Trades', type='numeric'),
        dict(id='avg_trade', name='Avg Trade', type='numeric'),
        # dict(id='perc_profit', name='% Profitable', type='numeric', format=percentage),
        dict(id='worst_trade', name='Worst Trade', type='numeric', format=money),
        dict(id='worst_month', name='Worst Month', type='numeric', format=money),
        dict(id='avg_loosing_month', name='Avg Loosing Month', type='numeric', format=money),
        dict(id='profit_1m', name='Profit 1 Month', type='numeric', format=money),
        dict(id='profit_6m', name='Profit 6 Month', type='numeric', format=money),
        dict(id='profit_1y', name='Profit 1 Year', type='numeric', format=money),
    ]

    layout = dash_table.DataTable(
        id='strategy_list_table',
        columns=columns,
        data=strategy_list.to_dict('records'),
        sort_action='native',
        row_selectable='multi',
        selected_rows=[],
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_data_conditional=(
                [
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ] +
                [
                    {
                        'if': {
                            'filter_query': '{profit_1m} <= 0',
                            'column_id': 'profit_1m'
                        },
                        'backgroundColor': '#FF4136',
                        'color': 'white'
                    }
                ] +
                [
                    {
                        'if': {
                            'filter_query': '{profit_1m} > 0',
                            'column_id': 'profit_1m'
                        },
                        'backgroundColor': '#3D9970',
                        'color': 'white'
                    }
                ] +
                [
                    {
                        'if': {
                            'filter_query': '{profit_6m} <= 0',
                            'column_id': 'profit_6m'
                        },
                        'backgroundColor': '#FF4136',
                        'color': 'white'
                    }
                ] +
                [
                    {
                        'if': {
                            'filter_query': '{profit_6m} > 0',
                            'column_id': 'profit_6m'
                        },
                        'backgroundColor': '#3D9970',
                        'color': 'white'
                    }
                ] +
                [
                    {
                        'if': {
                            'filter_query': '{profit_1y} <= 0',
                            'column_id': 'profit_1y'
                        },
                        'backgroundColor': '#FF4136',
                        'color': 'white'
                    }
                ] +
                [
                    {
                        'if': {
                            'filter_query': '{profit_1y} > 0',
                            'column_id': 'profit_1y'
                        },
                        'backgroundColor': '#3D9970',
                        'color': 'white'
                    }
                ]
        )
    )

    div_modal = html.Div(
        id="div_modal",
        children=pasm.render_modal(pd.DataFrame(), False, True, capital, risk, num_strategies)
    )

    ret = html.Div([
        dbc.Row([
            dbc.Col(layout, width=12),
        ]),
        dbc.Row([
            dbc.Col(dbc.Button("Simulate Portfolio", id="open", color="primary"), width=12),
        ], style={'margin-top': '15px'}),
        div_modal
        # dbc.Row({
        #     dbc.Col(div_modal, width=12),
        # })
    ])

    return ret
