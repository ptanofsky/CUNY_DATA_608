# Dash App with state

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        dcc.Input(id="input-1", type="text", value="Montreal"),
        dcc.Input(id="input-2", type="text", value="Canada"),
        html.Div(id="number-output"),
    ]
)

@app.callback(
    Output("number-output", "children"),
    [Input("input-1", "value"), Input("input-2", "value")],
)
def update_output(input1, input2):
    return u'Input 1 is "{}" and Input 2 is "{}"'.format(input1, input2)

if __name__ == '__main__':
    app.run_server(debug=True)










