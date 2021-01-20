import dash_bootstrap_components as dbc
import dash_html_components as html
import plotly.express as px
import dash_core_components as dcc
import numpy as np
import pandas as pd
from service import CalculateDataService, GraphService, PrintTextService
import plotly.graph_objects as go


def render_modal(data, open_button, close_button):
    visible = open_button and not close_button
    modal = [
        dbc.Button("Evaluate", id="open"),
        dbc.Modal(
            [
                dbc.ModalHeader("Selection Analysis"),
                dbc.ModalBody(render_modal_body(data)),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-xl", className="ml-auto")
                ),
            ],
            id="modal-selected",
            size="xl",
            is_open=visible
        ),
    ]

    return modal


def render_modal_body(data):

    ret = []

    if not data.empty:
        data = data.sort_values(by=['date', 'time'])
        CalculateDataService.calculate_values(data, False, 30000, 2.5, True, True)

        table_month = pd.pivot_table(data, values='profit_net', index=['year'],
                                     columns=['month'], aggfunc=np.sum).fillna(0)

#        fig = px.line(data, x='date', y='equity_calc')
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['date'], y=data['equity_calc'], fill='tozeroy',
                                 mode='none'  # override default markers+lines
                                 ))
        fig.add_trace(go.Scatter(x=data['date'], y=data['drawdown'], fill='tozeroy',
                                 mode='none'  # override default markers+lines
                                 ))
        fig_drawdown = px.area(data, x='date', y='drawdown')

        ret = [
            dbc.Row([
                dbc.Col(dcc.Graph(id='equity_modal_single', figure=fig), width=12),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='drawdown_modal_single', figure=fig_drawdown), width=12),
            ]),
            dbc.Row([
                dbc.Col(GraphService.draw_data_table(table_month, "month", "modal_month_datatable"), width=8),
                dbc.Col(PrintTextService.performance_report(data, 30000, 1), width=4),
            ])
        ]

    return ret
