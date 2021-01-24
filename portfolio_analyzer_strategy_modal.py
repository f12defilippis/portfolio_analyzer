import dash_bootstrap_components as dbc
import dash_html_components as html
import plotly.express as px
import dash_core_components as dcc
import numpy as np
import pandas as pd
from service import CalculateDataService, GraphService, PrintTextService
import plotly.graph_objects as go
import plotly.figure_factory as ff


def render_modal(data, open_button, close_button, capital, risk, num_strategies):
    visible = open_button and not close_button
    modal = [
        dbc.Modal(
            [
                dbc.ModalHeader("Selection Analysis"),
                dbc.ModalBody(render_modal_body(data, capital, risk, num_strategies)),
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


def render_modal_body(data, capital, risk, num_strategies):

    ret = []

    if not data.empty:
        data_original_nomm = data.sort_values(by=['date', 'time'])
        CalculateDataService.calculate_values(data_original_nomm, False, capital, risk, False, False)
        data_controlled, data, data_original_nomm = CalculateDataService.get_controlled_and_uncontrolled_data(data_original_nomm, capital, risk, capital*0.1)

        # rotate portfolio
        data_rotated = CalculateDataService.rotate_portfolio(data_original_nomm, data, num_strategies, "np_avgdd")
        if not data_rotated.empty:
            data_rotated = data_rotated.sort_values(by=['date', 'time'])
            CalculateDataService.calculate_values(data_rotated, False, capital, risk, False, True)
            table_month_rotated = pd.pivot_table(data_rotated, values='profit_net', index=['year'],
                                         columns=['month'], aggfunc=np.sum).fillna(0)

        # rotate and control portfolio
        data_controlled_rotated = CalculateDataService.rotate_portfolio(data_original_nomm, data_controlled, num_strategies, "np_avgdd")
        if not data_controlled_rotated.empty:
            data_controlled_rotated = data_controlled_rotated.sort_values(by=['date', 'time'])
            CalculateDataService.calculate_values(data_controlled_rotated, True, capital, risk, False, True)
            table_month_controlled_rotated = pd.pivot_table(data_controlled_rotated, values='profit_net', index=['year'],
                                         columns=['month'], aggfunc=np.sum).fillna(0)

        # rotate portfolio
        data_rotated_corr = CalculateDataService.rotate_portfolio(data_original_nomm, data, num_strategies, "np_corr")
        if not data_rotated_corr.empty:
            data_rotated_corr = data_rotated_corr.sort_values(by=['date', 'time'])
            CalculateDataService.calculate_values(data_rotated_corr, False, capital, risk, False, True)
            table_month_rotated_corr = pd.pivot_table(data_rotated_corr, values='profit_net', index=['year'],
                                         columns=['month'], aggfunc=np.sum).fillna(0)

        # rotate and control portfolio
        data_controlled_rotated_corr = CalculateDataService.rotate_portfolio(data_original_nomm, data_controlled, num_strategies, "np_corr")
        if not data_controlled_rotated_corr.empty:
            data_controlled_rotated_corr = data_controlled_rotated_corr.sort_values(by=['date', 'time'])
            CalculateDataService.calculate_values(data_controlled_rotated_corr, True, capital, risk, False, True)
            table_month_controlled_rotated_corr = pd.pivot_table(data_controlled_rotated_corr, values='profit_net', index=['year'],
                                         columns=['month'], aggfunc=np.sum).fillna(0)



        data_merged = CalculateDataService.calculate_data_merged(data, data_controlled, data_rotated, data_controlled_rotated, capital, risk)

        data_correlated = CalculateDataService.correlate(data)
        z = data_correlated.to_numpy().tolist()
        x = data_correlated.columns.to_numpy().tolist()
        y = data_correlated.columns.to_numpy().tolist()
        z_text = data_correlated.to_numpy().round(2).tolist()

        fig_correlated = ff.create_annotated_heatmap(z, x=x, y=y, annotation_text=z_text, colorscale='Viridis')

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
                dbc.Col(PrintTextService.performance_report(data, capital, 1), width=3),
                dbc.Col(PrintTextService.performance_report(data_controlled, capital, 1), width=3),
                dbc.Col(PrintTextService.performance_report(data_rotated, capital, 1), width=3),
                dbc.Col(PrintTextService.performance_report(data_controlled_rotated, capital, 1), width=3),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='correlation_graph', figure=fig_correlated), width=12),
            ]),

        ]

    return ret
