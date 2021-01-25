import plotly.express as px
import dash_table
from dash_table import FormatTemplate
import plotly.graph_objects as go


def draw_equity(table):
    fig = px.line(table, x="date", y=table.columns,
                  hover_data={"date": "|%B %d, %Y"},
                  title='custom tick labels', width=1200, height=800)
    fig.update_xaxes(rangeslider_visible=True)
    return fig


def draw_data_table(table, row_index_name, id_table):
    table = table.reset_index()
    for i in table.columns:
        if i != row_index_name:
            table[i] = table[i].round(2)

    datatable = dash_table.DataTable(
        id=id_table,
        columns=[{"name": str(i), "id": str(i)} for i in table.columns],
        style_data_conditional=[
                                   {
                                       'if': {
                                           'filter_query': '{{{col}}} >= 0'.format(col=col),
                                           'column_id': str(col)
                                       },
                                       'backgroundColor': '#3D9970',
                                       'color': 'white'
                                   } for col in table.iloc[:, 1:].columns
                               ] +
                               [
                                   {
                                       'if': {
                                           'filter_query': '{{{col}}} < 0'.format(col=col),
                                           'column_id': str(col)
                                       },
                                       'backgroundColor': '#FF4136',
                                       'color': 'white'
                                   } for col in table.iloc[:, 1:].columns
                               ],
        data=table.to_dict('records'),
    )

    return datatable


def draw_summary_table(columns, data_list, id_table):
    layout = dash_table.DataTable(
        id=id_table,
        columns=columns,
        data=data_list.to_dict('records'),
        sort_action='native',
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_cell={
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'maxWidth': 0,
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
                ]+
                [
                    {
                        'if': {
                            'filter_query': '{profit_3m} <= 0',
                            'column_id': 'profit_3m'
                        },
                        'backgroundColor': '#FF4136',
                        'color': 'white'
                    }
                ] +
                [
                    {
                        'if': {
                            'filter_query': '{profit_3m} > 0',
                            'column_id': 'profit_3m'
                        },
                        'backgroundColor': '#3D9970',
                        'color': 'white'
                    }
                ] +
                [
                    {
                        'if': {
                            'filter_query': '{profit_9m} <= 0',
                            'column_id': 'profit_9m'
                        },
                        'backgroundColor': '#FF4136',
                        'color': 'white'
                    }
                ] +
                [
                    {
                        'if': {
                            'filter_query': '{profit_9m} > 0',
                            'column_id': 'profit_9m'
                        },
                        'backgroundColor': '#3D9970',
                        'color': 'white'
                    }
                ]
        )
    )
    return layout


def get_columns_for_summary():
    money = FormatTemplate.money(2)
    columns = [
        dict(id='type', name='Type'),
        dict(id='profit', name='Profit', type='numeric', format=money),
        dict(id='max_dd', name='Max Drawdown', type='numeric', format=money),
        dict(id='np_maxdd', name='NP / Max DD', type='numeric'),
        dict(id='num_trades', name='Trades', type='numeric'),
        dict(id='avg_trade', name='Avg Trade', type='numeric'),
        dict(id='worst_trade', name='Worst Trade', type='numeric', format=money),
        dict(id='worst_month', name='Worst Month', type='numeric', format=money),
        dict(id='profit_1m', name='Profit 1 Month', type='numeric', format=money),
        dict(id='profit_3m', name='Profit 3 Month', type='numeric', format=money),
        dict(id='profit_6m', name='Profit 6 Month', type='numeric', format=money),
        dict(id='profit_9m', name='Profit 9 Month', type='numeric', format=money),
        dict(id='profit_1y', name='Profit 1 Year', type='numeric', format=money),
    ]
    return columns


def draw_equity_and_drawdown(data):
    my_layout = go.Layout({"title": "Equity",
                           "showlegend": False})

    fig = go.Figure(layout=my_layout)
    fig.add_trace(
        go.Scatter(x=data['date'], y=data['equity_calc'],
                   fill='tozeroy',
                   mode='none'  # override default markers+lines
                   ))
    fig.add_trace(
        go.Scatter(x=data['date'], y=data['drawdown'],
                   fill='tozeroy',
                   mode='none'  # override default markers+lines
                   ))
    fig_drawdown = px.area(data, x='date', y='drawdown')

    return fig, fig_drawdown
