import dash
import dash_core_components as dcc
import dash_html_components as html


def performance_report(data, capital, margin_used):
    return html.P([
        'Performance Report: ', html.Br(),
        'Num Strategies: ', data['strategy'].nunique(), html.Br(),
        'Net Profit: ', data['profit_net'].sum(), '$', html.Br(),
        'Gross Profit: ', data[data['profit_net'] > 0].profit_net.sum(), '$', html.Br(),
        'Gross Loss: ', data[data['profit_net'] < 0].profit_net.sum() * -1, '$', html.Br(),
        'Profit Factor: ',
        round(data[data['profit_net'] > 0].profit_net.sum() / data[data['profit_net'] < 0].profit_net.sum() * -1, 2),
        html.Br(),
        'Number of Trades: ', data[data['profit_net'] != 0]['profit_net'].count(), html.Br(),
        'Perc. Profitable: ',
                        round(data[data['profit_net'] > 0].profit_net.count() / data[data['profit_net'] != 0].profit_net.count(), 2) * 100,
        '%', html.Br(),
        'Avg Trade: ', round(data['profit_net'].sum() / data[data['profit_net'] != 0].profit_net.count(), 2), '$', html.Br(),
        'Slippage Paid: ', data['slippage_paid'].sum(), '$', html.Br(),
        'Slippage Avg: ', round(data['slippage_paid'].sum() / data[data['profit_net'] != 0].profit_net.count(), 2), '$', html.Br(),
        'Max Drawdown: ', data.max_drawdown.min() * -1, '$', html.Br(),
        'Avg Drawdown: ', round(data[data.drawdown < 0].drawdown.mean() * -1, 2), '$', html.Br(),
        'Max Margin Used: ', margin_used, '$', html.Br(),
        'Capital Needed: ', margin_used + (data.max_drawdown.min() * -1) * 2, '$', html.Br(),
        'Net Profit / Max Drawdown: ', round(data['profit_net'].sum() / data.max_drawdown.min() * -1, 2), html.Br(),
        'Net Profit / Avg Drawdown: ',
        round(data['profit_net'].sum() / data[data.drawdown < 0].drawdown.mean() * -1, 2), html.Br(),
        'Max Drawdown / Capital: ', round(data.max_drawdown.min() * -1 / capital, 2) * 100, '%', html.Br(),
        'Max Rolling Drawdown / Equity: ', round(data.ddOnCapital.min() * -1, 2), '%', html.Br(),
        'Max Drawdown / Capital Needed: ',
                        round(data.max_drawdown.min() * -1 / (margin_used + (data.max_drawdown.min() * -1) * 2),
                              2) * 100, '%', html.Br(),
        'Capital / Capital Needed: ', round(capital / (margin_used + (data.max_drawdown.min() * -1) * 2) * 100, 2), '%'
    ])


def print_basic_data(strategy_name, data_onestrategy):
    return html.P([
        strategy_name, ' Num. Op.', data_onestrategy[data_onestrategy.profit_net != 0].strategy.count(),
        'NP:', data_onestrategy['profit_net'].sum(),
        'Max DD: ', data_onestrategy.max_drawdown.min() * -1,
        'NP/Max DD: ', round(data_onestrategy['profit_net'].sum() / data_onestrategy.max_drawdown.min() * -1, 2)
    ])
