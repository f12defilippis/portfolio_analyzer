import dash_bootstrap_components as dbc
from datetime import date
import dash_core_components as dcc

def checkbox(checkbox_id, label, checked):
    form_group = dbc.FormGroup(
        [
            dbc.Checkbox(
                id=checkbox_id, className="form-check-input", checked=checked
            ),
            dbc.Label(
                label,
                html_for=checkbox_id,
                className="form-check-label",
            ),
        ],
        check=True,
    )
    return form_group


def textfield(textfield_id, label, placeholder, value):
    text_field = dbc.FormGroup([
        dbc.Label(label),
        dbc.Input(id=textfield_id, placeholder=placeholder, type="text", bs_size="sm", value=value),
    ])
    return text_field


def datepicker(datepicker_id):
    ret = dcc.DatePickerRange(
        id=datepicker_id,
        min_date_allowed=date(1995, 8, 5),
        max_date_allowed=date(2022, 9, 19),
        initial_visible_month=date(2015, 1, 1),
        end_date=date(2017, 8, 25))
    return ret
