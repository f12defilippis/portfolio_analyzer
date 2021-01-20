import dash_bootstrap_components as dbc
import dash_html_components as html
import plotly.express as px
import dash_core_components as dcc



from service import CalculateDataService


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
        fig = px.line(data, x='date', y='equity_calc')

        ret = [
            dbc.Row([
                dbc.Col(dcc.Graph(id='equity_modal_single', figure=fig), width=12),
            ])
        ]

    return ret
