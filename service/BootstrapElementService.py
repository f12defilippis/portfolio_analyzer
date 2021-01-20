import dash_bootstrap_components as dbc


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
