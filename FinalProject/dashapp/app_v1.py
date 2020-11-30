import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px

import pandas as pd
import folium
import json

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')


atx_zip_data = pd.read_csv('atxdata.csv')
# Convert all data to string
atx_zip_data['Zip Code'] = atx_zip_data['Zip Code'].astype(str)

geo_data = 'atx_zips_coords_ordered.json'

# Create list of statistics for dropdown
dd_list_stats = list(atx_zip_data)

#-------------------------------------------------------
# Build map of Austin Texas with folium module - START
#-------------------------------------------------------

# From https://towardsdatascience.com/using-folium-to-generate-choropleth-map-with-customised-tooltips-12e4cec42af2
with open(geo_data) as f:
    map_datax = json.load(f)
map_data = map_datax

# prepare the customized text
tooltip_text = []
for idx in range(len(atx_zip_data)):
    tooltip_text.append(atx_zip_data['Zip Code'][idx]+' '+ str(atx_zip_data['Total population'][idx]))
tooltip_text

# Append a tooltip column with customized text
for idx in range(len(tooltip_text)):
    map_data['features'][idx]['properties']['tooltip1'] = tooltip_text[idx]
geo_data = map_data

# Create a folium map object
# ATX coordinates: 30.2672° N, 97.7431° W
m = folium.Map(
        location=[30.2672, -97.7431],
        tiles='Stamen Toner',
        zoom_start=10)
# Now to render the zip codes on the map with just GeoJson
'''
folium.GeoJson(
    'atx_zips_coords.json',
    name='geojson'
).add_to(m)
'''
# Now to render the zip codes on the map as Choropleth
choropleth = folium.Choropleth(
    geo_data=geo_data,
    name='atx choropleth',
    data=atx_zip_data,
    columns=['Zip Code', 'Total population'],
    key_on='feature.properties.ZCTA5CE10',
    fill_color='YlGn',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Total Population'
).add_to(m)

# Remember to add layer control
folium.LayerControl().add_to(m)

# Display Region Label
choropleth.geojson.add_child(
    folium.features.GeoJsonTooltip(fields=['tooltip1'], labels=False)
)

# Save map as html
m.save('map.html')
#-------------------------------------------------------
# Build map of Austin Texas with folium module - END
#-------------------------------------------------------


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1(children='Final Project'),
    html.H3(children='Author: Philip Tanofsky'),
    html.H5(children='DATA 608, Fall 2020'),
    html.H5(children='November 27, 2020'),

    html.Div([
        html.H5(children='html div'),
        dcc.Graph(id='graph-with-slider'),
        dcc.Slider(
            id='year-slider',
            min=df['year'].min(),
            max=df['year'].max(),
            value=df['year'].min(),
            marks={str(year): str(year) for year in df['year'].unique()},
            step=None
        )
    ]),

    # Dropdowns
    html.Div([

        html.Div([
            html.H6(children='Select a Statistic'),
            dcc.Dropdown(
                id='stat-1-selection-dd',
                options=[{'label': i, 'value': i} for i in dd_list_stats],
                value='Total population',
                clearable=False
            )
        ],
        style={'width': '49%', 'display': 'inline-block'}),

        html.Div([
            html.H6(children='Select a Statistic'),
            dcc.Dropdown(
                id='stat-2-selection-dd',
                options=[{'label': i, 'value': i} for i in dd_list_stats],
                value='Female',
                clearable=False
            )
        ], style={'width': '49%', 'float': 'right', 'display': 'inline-block'})
    ], style={
        'borderBottom': 'thin lightgrey solid',
        'backgroundColor': 'rgb(250, 250, 250)',
        'padding': '10px 5px'
    }),

    html.Div([
        html.Iframe(id = 'map', srcDoc=open('map.html', 'r').read(), width='100%', height='600')
    ])
])


@app.callback(
    Output('graph-with-slider', 'figure'),
    Input('year-slider', 'value'))
def update_figure(selected_year):
    filtered_df = df[df.year == selected_year]

    fig = px.scatter(filtered_df, x="gdpPercap", y="lifeExp",
                     size="pop", color="continent", hover_name="country",
                     log_x=True, size_max=55)
    fig.update_layout(transition_duration=500)
    return fig


@app.callback(
    Output('map', 'children'),
    Input('stat-1-selection-dd', 'value'),
    Input('stat-2-selection-dd', 'value')
)
def update_map_of_zip_codes(stat_01, stat_02):

    return 0


if __name__ == '__main__':
    app.run_server(debug=True)