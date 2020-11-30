import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import folium
import json

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')


atx_zip_data = pd.read_csv('atxdata.csv')
# Convert all data to string
atx_zip_data['Zip Code'] = atx_zip_data['Zip Code'].astype(str)
atx_zip_data = atx_zip_data.replace('-','0')

# Create list of statistics for dropdown
dd_list_stats = list(atx_zip_data)


# Color dictionary for bivariate choropleth
color_key = {'C3':'#3b4994',
             'B3':'#8c62aa',
             'A3':'#be64ac',
             'C2':'#5698b9',
             'B2':'#a5add3',
             'A2':'#dfb0d6',
             'C1':'#5ac8c8',
             'B1':'#ace4e4',
             'A1':'#e8e8e8'}

def determine_bivariate_choropleth_color(zipcode, stat1, stat2):
    # Define the labels to be used in defining the color of the 3x3 matrix
    labels_s1 = ['A', 'B', 'C']
    labels_s2 = ['1', '2', '3']

    # Define percentile for dividing by 3 (33.33)
    pct = 100 / 3

    # Create the breakpoints for the two columns, land and building
    bp_s1 = np.percentile(atx_zip_data[stat1], [pct, 100 - pct], axis=0)

    bp_s2 = np.percentile(atx_zip_data[stat2], [pct, 100 - pct], axis=0)

    # Bin the land assessments
    stat1_val = atx_zip_data.loc[atx_zip_data['Zip Code'] == zipcode, stat1].iloc[0]
    if stat1_val > 0 and stat1_val < bp_s1[0]:
        stat1_label = labels_s1[0]
    elif stat1_val >= bp_s1[0] and bp_s1[0] < bp_s1[1]:
        stat1_label = labels_s1[1]
    else:
        stat1_label = labels_s1[2]

    # Bin the building assessments
    stat2_val = atx_zip_data.loc[atx_zip_data['Zip Code'] == zipcode, stat2].iloc[0]
    if stat2_val > 0 and stat2_val < bp_s2[0]:
        stat2_label = labels_s2[0]
    elif stat2_val >= bp_s2[0] and bp_s2[0] < bp_s2[1]:
        stat2_label = labels_s2[1]
    else:
        stat2_label = labels_s2[2]

    # Concatenate the land and building labels
    color = stat1_label + stat2_label

    return color_key[color]

#-------------------------------------------------------
# Build map of Austin Texas with folium module - START
#-------------------------------------------------------

def build_atx_map(inp1, inp2):
    # GeoJSON of the zip codes for Austin, Tx
    geo_data = 'atx_zips_coords_ordered.json'

    # From https://towardsdatascience.com/using-folium-to-generate-choropleth-map-with-customised-tooltips-12e4cec42af2
    with open(geo_data) as f:
        map_datax = json.load(f)
    map_data = map_datax

    # prepare the customized text for the tooltip
    tooltip_text = []
    for idx in range(len(atx_zip_data)):
        tooltip_text.append(atx_zip_data['Zip Code'][idx]+' '+ str(atx_zip_data[inp1][idx]))
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

    choropleth = folium.GeoJson(
        geo_data,
        name='ATX Bivariate Choropleth',
        style_function=lambda feature: {
            'fillColor': determine_bivariate_choropleth_color(feature['properties']['ZCTA5CE10'], inp1, inp2),
            'color': 'black',
            'weight': 1,
            'dashArray': '5, 5',
            'fillOpacity': 0.9,
        }
    ).add_to(m)
    '''
    # Now to render the zip codes on the map as Choropleth
    choropleth = folium.Choropleth(
        geo_data=geo_data,
        name='atx choropleth',
        data=atx_zip_data,
        columns=['Zip Code', inp1],
        key_on='feature.properties.ZCTA5CE10',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=inp1
    ).add_to(m)
    '''

    # Remember to add layer control
    folium.LayerControl().add_to(m)

    # Display Region Label
#    choropleth.geojson.add_child(
    choropleth.add_child(
        folium.features.GeoJsonTooltip(fields=['tooltip1'], labels=False)
    )

    # Save map as html
    m.save('map.html')

    #srcDoc = urllib.request.urlopen('map.html').read()
    srcDoc = open('map.html', 'r', encoding='utf-8')
    source_code = srcDoc.read()
    #srcDoc = open('map.html', 'r').read()

    return source_code
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
#        html.Iframe(id = 'map', srcDoc=open('map.html', 'r').read(), width='100%', height='600')
        html.Iframe(id = 'map', width='100%', height='600')
    ])
])





@app.callback(
    Output('map', 'srcDoc'),
    Input('stat-1-selection-dd', 'value'),
    Input('stat-2-selection-dd', 'value')
)
def update_map_of_zip_codes(stat_01, stat_02):
    return build_atx_map(stat_02, stat_01)


if __name__ == '__main__':
    app.run_server(debug=True)