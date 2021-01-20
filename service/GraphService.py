import plotly.express as px
import dash_table


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
                                   } for col in table.columns
                               ] +
                               [
                                   {
                                       'if': {
                                           'filter_query': '{{{col}}} < 0'.format(col=col),
                                           'column_id': str(col)
                                       },
                                       'backgroundColor': '#FF4136',
                                       'color': 'white'
                                   } for col in table.columns
                               ],
        data=table.to_dict('records'),
    )
    return datatable
