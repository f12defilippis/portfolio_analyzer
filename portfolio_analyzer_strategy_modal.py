import dash_bootstrap_components as dbc
import dash_html_components as html
import plotly.express as px
import dash_core_components as dcc
import numpy as np
import pandas as pd
from service import CalculateDataService, GraphService, PrintTextService, ManageDataService
import plotly.graph_objects as go
import plotly.figure_factory as ff


def render_modal(data, open_button, close_button, capital, risk, num_strategies):
    visible = open_button and not close_button
    modal = [
        dbc.Modal(
            [
                dbc.ModalHeader("Selection Analysis"),
                dbc.ModalBody(render_modal_body(data, capital, risk, num_strategies) if visible else "Not visible"),
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
        data_controlled, data, data_original_nomm, table_month, table_month_controlled = CalculateDataService.get_controlled_and_uncontrolled_data(
            data_original_nomm, capital, risk, capital * 0.1)

        # rotate portfolio
        data_rotated, table_month_rotated = ManageDataService.get_rotated_data(data_original_nomm, data, num_strategies, capital, risk, "np_avgdd")
        data_controlled_rotated, table_month_controlled_rotated = ManageDataService.get_rotated_data(data_original_nomm, data_controlled, num_strategies, capital, risk, "np_avgdd")
        data_rotated_corr, table_month_rotated_corr = ManageDataService.get_rotated_data(data_original_nomm, data, num_strategies, capital, risk, "np_corr")
        data_controlled_rotated_corr, table_month_controlled_rotated_corr = ManageDataService.get_rotated_data(data_original_nomm, data_controlled, num_strategies, capital, risk, "np_corr")

        # get merged summary
        data_merged, data_merged_summary = ManageDataService.get_summary(data, data_controlled, data_rotated,
                                                                 data_controlled_rotated, data_rotated_corr,
                                                                 data_controlled_rotated_corr, capital, risk)

        columns = GraphService.get_columns_for_summary()
        summary_table = GraphService.draw_summary_table(columns, data_merged_summary, "table_summary")

        months_to_try = [3, 6, 9, 12]
        all_fig_corr_month = []
        all_fig_corr_week = []

        for m in months_to_try:
            data_correlated = CalculateDataService.correlate_data_with_parameter(data, m, 'month')
            fig_correlated = ff.create_annotated_heatmap(data_correlated.to_numpy().tolist(),
                                                         x=data_correlated.columns.to_numpy().tolist(),
                                                         y=data_correlated.columns.to_numpy().tolist(),
                                                         annotation_text=data_correlated.to_numpy().round(2).tolist(),
                                                         colorscale='Viridis')
            all_fig_corr_month.append(fig_correlated)

        for m in months_to_try:
            data_correlated = CalculateDataService.correlate_data_with_parameter(data, m, 'week')
            fig_correlated = ff.create_annotated_heatmap(data_correlated.to_numpy().tolist(),
                                                         x=data_correlated.columns.to_numpy().tolist(),
                                                         y=data_correlated.columns.to_numpy().tolist(),
                                                         annotation_text=data_correlated.to_numpy().round(2).tolist(),
                                                         colorscale='Viridis')
            all_fig_corr_week.append(fig_correlated)



        fig_controlled_rotated_corr, fig_controlled_rotated_corr_drawdown = GraphService.draw_equity_and_drawdown(data_controlled_rotated_corr if len(data_controlled_rotated_corr) > 0 else data_controlled)

        fig_merged = px.line(data_merged, x='date', y='equity_calc', color='type')

        ret = [
            dbc.Row([
                dbc.Col(dcc.Graph(id='equity_modal_single', figure=fig_controlled_rotated_corr), width=12),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='drawdown_modal_single', figure=fig_controlled_rotated_corr_drawdown), width=12),
            ]),
            dbc.Row([
                dbc.Col(GraphService.draw_data_table(table_month, "month", "modal_month_datatable"), width=12),
            ]),
            dbc.Row([
                dbc.Col(
                    GraphService.draw_data_table(table_month_controlled, "month", "modal_month_datatable_controlled"),
                    width=12),
            ]),
            dbc.Row([
                dbc.Col(GraphService.draw_data_table(table_month_rotated, "month", "modal_month_datatable_rotated"),
                        width=12),
            ]),
            dbc.Row([
                dbc.Col(GraphService.draw_data_table(table_month_controlled_rotated, "month",
                                                     "modal_month_datatable_controlled_rotated"), width=12),
            ]),
            dbc.Row([
                dbc.Col(GraphService.draw_data_table(table_month_rotated_corr, "month",
                                                     "modal_month_datatable_rotated_corr"),
                        width=12),
            ]),
            dbc.Row([
                dbc.Col(GraphService.draw_data_table(table_month_controlled_rotated_corr, "month",
                                                     "modal_month_datatable_controlled_rotated_corr"), width=12),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='equity_merged', figure=fig_merged), width=12),
            ]),
            dbc.Row([
                dbc.Col(summary_table, width=12),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='correlation_graph0', figure=all_fig_corr_month[0]), width=12),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='correlation_graph1', figure=all_fig_corr_month[1]), width=12),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='correlation_graph2', figure=all_fig_corr_month[2]), width=12),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='correlation_graph3', figure=all_fig_corr_month[3]), width=12),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='correlation_graph0w', figure=all_fig_corr_week[0]), width=12)
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='correlation_graph1w', figure=all_fig_corr_week[1]), width=12),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='correlation_graph2w', figure=all_fig_corr_week[2]), width=12),
            ]),
            dbc.Row([
                dbc.Col(dcc.Graph(id='correlation_graph3w', figure=all_fig_corr_week[3]), width=12),
            ]),

        ]

    return ret
