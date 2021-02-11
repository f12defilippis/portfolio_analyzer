# Code source: https://dash-bootstrap-components.opensource.faculty.ai/examples/simple-sidebar/
import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
from service import BootstrapElementService as bes, CalculateDataService
import portfolio_analyzer_content as pac
import portfolio_analyzer_strategylist as pasl
from dash.dependencies import Output, State, Input
import portfolio_analyzer_strategy_modal as pasm


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

#base variables
capital_start = 30000
num_strategies_start = 8
risk_start = 2.5
dd_limit = 5
oos = True
position_sizing = True
equity_control = True
strategy_rotation = True


# styling the sidebar
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# padding for the page content
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H2("Portfolio Analyzer", className="display-4"),
        html.Hr(),
        html.P(
            "Select the input options", className="lead"
        ),
        bes.textfield("txt_capital", "Starting Capital", "Indicate the starting capital here", capital_start),
        bes.textfield("txt_numstrategies", "Number of Strategies", "Indicate the number of strategies here", num_strategies_start),
        bes.textfield("txt_risk", "Risk", "Indicate the risk here", risk_start),
        bes.textfield("txt_dd", "Drawdown Limit", "Indicate the drawdown limit here", dd_limit),
        bes.datepicker("date_from"),
        bes.checkbox("check_oos", "Only OOS", oos),
        bes.checkbox("check_possiz", "Position Sizing", position_sizing),
        bes.checkbox("check_equcon", "Equity Control", equity_control),
        bes.checkbox("check_strrot", "Strategy Rotation", strategy_rotation),
        html.Hr(),
        dbc.Button("Generate", id="btn_generate", color="primary", block=True),
    ],
    style=SIDEBAR_STYLE,
)

#content = html.Div(id="page-content", children=pac.render_page(capital, num_strategies, risk, dd_limit, oos, position_sizing, equity_control, strategy_rotation, ""), style=CONTENT_STYLE)
content = html.Div(id="page-content", children=pasl.render_page(capital_start, risk_start, num_strategies_start), style=CONTENT_STYLE)


app.layout = html.Div([
    dcc.Location(id="url"),
    sidebar,
    content
])


# @app.callback(
#     Output("page-content", "children"),
#     [Input("url", "pathname")]
# )
# def render_page_content(pathname):
#     if pathname == "/":
#         return pac.render_page(capital, num_strategies, risk, dd_limit, oos, position_sizing, equity_control, strategy_rotation)
#     # If the user tries to reach a different page, return a 404 message
#     return dbc.Jumbotron(
#         [
#             html.H1("404: Not found", className="text-danger"),
#             html.Hr(),
#             html.P(f"The pathname {pathname} was not recognised..."),
#         ]
#     )

# @app.callback(
#     Output("page-content", "children"),
#     [Input("btn_generate", "n_clicks")],
#     [State('txt_capital', 'value')],
#     [State('txt_numstrategies', 'value')],
#     [State('txt_risk', 'value')],
#     [State('check_oos', 'checked')],
# )
# def render_page_content_button(pathname, capital_value, numstrategies_value, risk_value, oos_value):
#     return pac.render_page(int(capital_value), int(numstrategies_value), float(risk_value), dd_limit, oos_value, position_sizing, equity_control, strategy_rotation)





@app.callback(
    Output("div_modal", "children"),
    [Input("open", "n_clicks"), Input("close-xl", "n_clicks")],
    [State("strategy_list_table", "data")],
    [State("strategy_list_table", "selected_rows")],
    [State('check_oos', 'checked')],
    [State('txt_capital', 'value')],
    [State('txt_risk', 'value')],
    [State('txt_numstrategies', 'value')],
)
def get_model_data(n1, n2, datatable, selected_row_ids, oos, capital, risk, num_strategies):

    data = CalculateDataService.load_data(int(capital), float(risk))
    data_selected = []
    for i in selected_row_ids:
        single_data = data[data['strategy'] == datatable[i]['name']]
        data_selected.append(single_data)

    ret_data = pd.DataFrame()
    if len(data_selected) > 0:
        ret_data = pd.concat(data_selected)

    if len(data_selected) > 0 and oos:
        ret_data = ret_data[ret_data['oosis'] == 'oos']

    return pasm.render_modal(ret_data, n1 is not None and n1 > 0, n2 is not None and n2 > 0, int(capital), float(risk), int(num_strategies))



if __name__=='__main__':
    app.run_server(debug=True, port=3000)
