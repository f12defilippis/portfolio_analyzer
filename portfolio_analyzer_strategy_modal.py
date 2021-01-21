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
        data_controlled, data = CalculateDataService.get_controlled_and_uncontrolled_data(data, 30000, 2.5, 3000)

        # rotate portfolio
        data_rotated = CalculateDataService.rotate_portfolio(data, 6)
        if not data_rotated.empty:
            data_rotated = data_rotated.sort_values(by=['date', 'time'])
            CalculateDataService.calculate_values(data_rotated, False, 30000, 2.5, False, True)
            table_month_rotated = pd.pivot_table(data_rotated, values='profit_net', index=['year'],
                                         columns=['month'], aggfunc=np.sum).fillna(0)

        # rotate and control portfolio
        data_controlled_rotated = CalculateDataService.rotate_portfolio(data_controlled, 6)
        if not data_controlled_rotated.empty:
            data_controlled_rotated = data_controlled_rotated.sort_values(by=['date', 'time'])
            CalculateDataService.calculate_values(data_controlled_rotated, True, 30000, 2.5, False, True)
            table_month_controlled_rotated = pd.pivot_table(data_controlled_rotated, values='profit_net', index=['year'],
                                         columns=['month'], aggfunc=np.sum).fillna(0)

        data_merged = CalculateDataService.calculate_data_merged(data, data_controlled, data_rotated, data_controlled_rotated)


        table_month = pd.pivot_table(data, values='profit_net', index=['year'],
                                     columns=['month'], aggfunc=np.sum).fillna(0)

        table_month_controlled = pd.pivot_table(data_controlled, values='profit_net', index=['year'],
                                     columns=['month'], aggfunc=np.sum).fillna(0)




#        fig = px.line(data, x='date', y='equity_calc')
        my_layout = go.Layout({"title": "Equity",
                               "showlegend": False})
        fig = go.Figure(layout=my_layout)
        fig.add_trace(go.Scatter(x=data['date'], y=data['equity_calc'], fill='tozeroy',
                                 mode='none'  # override default markers+lines
                                 ))
        fig.add_trace(go.Scatter(x=data['date'], y=data['drawdown'], fill='tozeroy',
                                 mode='none'  # override default markers+lines
                                 ))
        fig_drawdown = px.area(data, x='date', y='drawdown')


        fig_controlled = go.Figure(layout=my_layout)
        fig_controlled.add_trace(go.Scatter(x=data_controlled['date'], y=data_controlled['equity_calc'], fill='tozeroy',
                                 mode='none'  # override default markers+lines
                                 ))
        fig_controlled.add_trace(go.Scatter(x=data_controlled['date'], y=data_controlled['drawdown'], fill='tozeroy',
                                 mode='none'  # override default markers+lines
                                 ))
        fig_controlled_drawdown = px.area(data_controlled, x='date', y='drawdown')


        fig_rotated = go.Figure(layout=my_layout)
        fig_rotated.add_trace(go.Scatter(x=data_rotated['date'], y=data_rotated['equity_calc'], fill='tozeroy',
                                 mode='none'  # override default markers+lines
                                 ))
        fig_rotated.add_trace(go.Scatter(x=data_rotated['date'], y=data_rotated['drawdown'], fill='tozeroy',
                                 mode='none'  # override default markers+lines
                                 ))
        fig_rotated_drawdown = px.area(data_rotated, x='date', y='drawdown')

        fig_merged = px.line(data_merged, x='date', y='equity_calc', color='type')

        ret = [
            dbc.Row([
                dbc.Col(dcc.Graph(id='equity_modal_single', figure=fig), width=4),
                dbc.Col(dcc.Graph(id='equity_modal_single_controlled', figure=fig_controlled), width=4),
                dbc.Col(dcc.Graph(id='equity_modal_single_rotated', figure=fig_rotated), width=4),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='drawdown_modal_single', figure=fig_drawdown), width=6),
                dbc.Col(dcc.Graph(id='drawdown_modal_single_controlled', figure=fig_controlled_drawdown), width=6),
            ]),
            dbc.Row([
                dbc.Col(GraphService.draw_data_table(table_month, "month", "modal_month_datatable"), width=12),
            ]),
            dbc.Row([
                dbc.Col(GraphService.draw_data_table(table_month_controlled, "month", "modal_month_datatable_controlled"), width=12),
            ]),
            dbc.Row([
                dbc.Col(GraphService.draw_data_table(table_month_rotated, "month", "modal_month_datatable_rotated"), width=12),
            ]),
            dbc.Row([
                dbc.Col(GraphService.draw_data_table(table_month_controlled_rotated, "month", "modal_month_datatable_controlled_rotated"), width=12),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='equity_merged', figure=fig_merged), width=12),
            ]),
            dbc.Row([
                dbc.Col(PrintTextService.performance_report(data, 30000, 1), width=3),
                dbc.Col(PrintTextService.performance_report(data_controlled, 30000, 1), width=3),
                dbc.Col(PrintTextService.performance_report(data_rotated, 30000, 1), width=3),
                dbc.Col(PrintTextService.performance_report(data_controlled_rotated, 30000, 1), width=3),
            ]),

        ]

    return ret
