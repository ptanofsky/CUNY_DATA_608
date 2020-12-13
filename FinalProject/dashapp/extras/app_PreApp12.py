import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import folium
import json
import requests


atx_zip_data = pd.read_csv('atxdata.csv')
# Convert zip code to string
atx_zip_data['Zip Code'] = atx_zip_data['Zip Code'].astype(str)
# Replace all the dashes with 0
#TODO Check if necessary
atx_zip_data = atx_zip_data.replace('-','0')

# Create list of statistics for dropdown
#Remove zip code itself from the drop down
dd_list_stats = list(atx_zip_data)
#Remove zip code itself from the drop down
dd_list_stats.remove('Zip Code')


with open('atx_zips_coords_ordered.json') as f:
    choro_geo_data = json.load(f)

markers_data = pd.read_csv('markers.csv')

#TODO consider moving to the function; not global
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

# All the Austin Zip codes under consideration
atx_zip_codes = ['78610', '78617', '78653', '78660', '78701', '78702', '78703', '78704',
                 '78705', '78721', '78722', '78723', '78724', '78725', '78726', '78727',
                 '78728', '78729', '78730', '78731', '78732', '78733', '78734', '78735',
                 '78736', '78737', '78738', '78739', '78741', '78742', '78744', '78745',
                 '78746', '78747', '78748', '78749', '78750', '78751', '78752', '78753',
                 '78754', '78756', '78757', '78758', '78759']

markers_dict = {
    "GolfCourse": "Public Golf Courses",
    "ComputerLab": "Public Computer Labs",
    "ElecCarCharging": "Electric Car Charging Stations",
    "AffordableHousing": "Affordable Housing Listings",
    "Shooting": "Officer Involved Shootings (2008-17)"
}

decade_2010_variables_dict = {
    "Total population": "B01003_001E",
    "Sex - Female": "B01001_026E",
    "Sex - Male":   "B01001_002E",
    "Income - Less than $10,000": "B19001_002E",
    "Income - $10,000 to $14,999": "B19001_003E",
    "Income - $15,000 to $19,999": "B19001_004E",
    "Income - $20,000 to $24,999": "B19001_005E",
    "Income - $25,000 to $29,999": "B19001_006E",
    "Income - $30,000 to $34,999": "B19001_007E",
    "Income - $35,000 to $39,999": "B19001_008E",
    "Income - $40,000 to $44,999": "B19001_009E",
    "Income - $45,000 to $49,999": "B19001_010E",
    "Income - $50,000 to $59,999": "B19001_011E",
    "Income - $60,000 to $74,999": "B19001_012E",
    "Income - $75,000 to $99,999": "B19001_013E",
    "Income - $100,000 to $124,999": "B19001_014E",
    "Income - $125,000 to $149,999": "B19001_015E",
    "Income - $150,000 to $199,999": "B19001_016E",
    "Income - $200,000 or more": "B19001_017E",
    "Income - Below poverty level": "B17001_002E",
    "Race - Hispanic or Latino": "B03002_001E",
    "Race - White": "B03002_003E",
    "Race - Black or African American": "B03002_004E",
    "Race - American Indian and Alaska Native": "B03002_005E",
    "Race - Asian": "B03002_006E",
    "Race - Native Hawaiian and Other Pacific Islander": "B03002_007E",
    "Race - Two or more races": "B02001_008E",
    "Education - Less than high school graduate": "B16010_002E",
    "Education - High school graduate (includes equivalency)": "B16010_015E",
    "Education - Some college or associate degree": "B16010_028E",
    "Education - Bachelor degree or higher": "B16010_041E"
}

dd_decade = list(decade_2010_variables_dict.keys())

markers_options = markers_dict.values()

years = [2011,2012,2013,2014,2015,2016,2017,2018]

# Function definitions

def retrieve_values_for_zip_codes(year, statistic):

    key = '09c5dae3e5eb30a5dbff1bce8d228b1c6c204d6b'
    statistic = decade_2010_variables_dict.get(statistic)
    #'B01003_001E' # Currently hard-coded to total population
    url = 'https://api.census.gov/data/' + str(year) + '/acs/acs5?get=NAME,' + statistic + '&for=zip%20code%20tabulation%20area:*&key=' + key

    myResponse = requests.get(url)

    if (myResponse.ok):
        jData = json.loads(myResponse.content)
        del jData[0]
        df = pd.DataFrame(jData, columns=['ZCTA5', 'Attr Value', 'Zip Code'])
        del df['ZCTA5']
        df = df[['Zip Code', 'Attr Value']]
        df = df[df['Zip Code'].isin(atx_zip_codes)]
        df.reset_index(drop=True, inplace=True)
        df = df.sort_values(by=['Zip Code'])

        # Convert zip code to string
        df['Zip Code'] = df['Zip Code'].astype(str)
        df['Attr Value'] = df['Attr Value'].astype(int)
    else:
        myResponse.raise_for_status()

    return df

def build_atx_map_for_single_attribute(year, statistic, markers):

    year_stat_df = retrieve_values_for_zip_codes(year, statistic)

    year_stat_df.reset_index(drop=True, inplace=True)
    year_stat_df = year_stat_df.sort_values(by=['Zip Code'])

    # GeoJSON of the zip codes for Austin, Tx
    geo_data = 'atx_zips_coords_ordered.json'

    # From https://towardsdatascience.com/using-folium-to-generate-choropleth-map-with-customised-tooltips-12e4cec42af2
    with open(geo_data) as f:
        map_datax = json.load(f)
    map_data = map_datax

    # prepare the customized text for the tooltip
    tooltip_text = []
    for idx in range(0, len(year_stat_df)):
        tooltip_text.append(year_stat_df['Zip Code'][idx] + ' ' + str(year_stat_df['Attr Value'][idx]))
    tooltip_text

    # Append a tooltip column with customized text
    for idx in range(0, len(tooltip_text)):
        map_data['features'][idx]['properties']['tooltip1'] = tooltip_text[idx]
    geo_data = map_data

    # Create a folium map object
    # ATX coordinates: 30.2672° N, 97.7431° W
    m = folium.Map(
        location=[30.2672, -97.7431],
        tiles='Stamen Toner',
        zoom_start=10)

    # Now to render the zip codes on the map as Choropleth
    choropleth = folium.Choropleth(
        geo_data=geo_data,
        name='atx choropleth',
        data=year_stat_df,
        columns=['Zip Code', 'Attr Value'],
        key_on='feature.properties.ZCTA5CE10',
        fill_color='PuBuGn',
        fill_opacity=0.8,
        line_opacity=0.2,
        legend_name=statistic
    ).add_to(m)

    # Add Markers based on the markers list

    if markers != None:

        if markers_dict.get('GolfCourse') in markers:
            golf_markers = markers_data.loc[markers_data['Category'] == 'GolfCourse']
            golf_markers.reset_index(drop=True, inplace=True)
            for idx in range(len(golf_markers)):
                folium.Marker(
                    location=[golf_markers.loc[idx, 'Lat'], golf_markers.loc[idx, 'Long']],
                    popup=golf_markers.loc[idx, 'Name'],
                    icon=folium.Icon(color='green', icon='info-sign')
                ).add_to(m)
        if markers_dict.get('ComputerLab') in markers:
            labs_markers = markers_data.loc[markers_data['Category'] == 'ComputerLab']
            labs_markers.reset_index(drop=True, inplace=True)
            for idx in range(len(labs_markers)):
                folium.Marker(
                    location=[labs_markers.loc[idx, 'Lat'], labs_markers.loc[idx, 'Long']],
                    popup=labs_markers.loc[idx, 'Name'],
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)
        if markers_dict.get('ElecCarCharging') in markers:
            elec_markers = markers_data.loc[markers_data['Category'] == 'ElecCarCharging']
            elec_markers.reset_index(drop=True, inplace=True)
            for idx in range(len(elec_markers)):
                folium.Marker(
                    location=[elec_markers.loc[idx, 'Lat'], elec_markers.loc[idx, 'Long']],
                    popup=elec_markers.loc[idx, 'Name'],
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)
        if markers_dict.get('AffordableHousing') in markers:
            house_markers = markers_data.loc[markers_data['Category'] == 'AffordableHousing']
            house_markers.reset_index(drop=True, inplace=True)
            for idx in range(len(house_markers)):
                folium.Marker(
                    location=[house_markers.loc[idx, 'Lat'], house_markers.loc[idx, 'Long']],
                    popup=house_markers.loc[idx, 'Name'],
                    icon=folium.Icon(color='lightgray', icon='info-sign')
                ).add_to(m)
        if markers_dict.get('Shooting') in markers:
            shoot_markers = markers_data.loc[markers_data['Category'] == 'Shooting']
            shoot_markers.reset_index(drop=True, inplace=True)
            for idx in range(len(shoot_markers)):
                folium.Marker(
                    location=[shoot_markers.loc[idx, 'Lat'], shoot_markers.loc[idx, 'Long']],
                    popup=shoot_markers.loc[idx, 'Name'],
                    icon=folium.Icon(color='beige', icon='info-sign')
                ).add_to(m)

    # Remember to add layer control
#    folium.LayerControl().add_to(m)

    # Display Region Label
    #    choropleth.geojson.add_child(
    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(fields=['tooltip1'], labels=False)
    )

    # Save map as html
    m.save('map.html')

    srcDoc = open('map.html', 'r', encoding='utf-8')
    source_code = srcDoc.read()

    return source_code


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

def build_atx_map(inp1, inp2, markers):
    # GeoJSON of the zip codes for Austin, Tx
    geo_data = 'atx_zips_coords_ordered.json'

    # From https://towardsdatascience.com/using-folium-to-generate-choropleth-map-with-customised-tooltips-12e4cec42af2
    with open(geo_data) as f:
        map_datax = json.load(f)
    map_data = map_datax

    # prepare the customized text for the tooltip
    tooltip_text = []
    for idx in range(len(atx_zip_data)):
        tooltip_text.append('<b>Zip code:</b> ' + atx_zip_data['Zip Code'][idx] +
                            '<br>' + inp1 + ': ' + str(atx_zip_data[inp1][idx]) +
                            '<br>' + inp2 + ': ' + str(atx_zip_data[inp2][idx]))

    #tooltip_text

    # Append a tooltip column with customized text
    for idx in range(len(tooltip_text)):
        map_data['features'][idx]['properties']['tooltip1'] = tooltip_text[idx]
    geo_data = map_data

    # Create a folium map object
    # ATX coordinates: 30.2672, -97.7431
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

    # Add Markers based on the markers list
    if markers != None:
        if markers_dict.get('GolfCourse') in markers:
            golf_markers = markers_data.loc[markers_data['Category'] == 'GolfCourse']
            golf_markers.reset_index(drop=True, inplace=True)
            for idx in range(len(golf_markers)):
                folium.Marker(
                    location=[golf_markers.loc[idx, 'Lat'], golf_markers.loc[idx, 'Long']],
                    popup=golf_markers.loc[idx, 'Name'],
                    icon=folium.Icon(color='green', icon='info-sign')
                ).add_to(m)
        if markers_dict.get('ComputerLab') in markers:
            labs_markers = markers_data.loc[markers_data['Category'] == 'ComputerLab']
            labs_markers.reset_index(drop=True, inplace=True)
            for idx in range(len(labs_markers)):
                folium.Marker(
                    location=[labs_markers.loc[idx, 'Lat'], labs_markers.loc[idx, 'Long']],
                    popup=labs_markers.loc[idx, 'Name'],
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)
        if markers_dict.get('ElecCarCharging') in markers:
            elec_markers = markers_data.loc[markers_data['Category'] == 'ElecCarCharging']
            elec_markers.reset_index(drop=True, inplace=True)
            for idx in range(len(elec_markers)):
                folium.Marker(
                    location=[elec_markers.loc[idx, 'Lat'], elec_markers.loc[idx, 'Long']],
                    popup=elec_markers.loc[idx, 'Name'],
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)
        if markers_dict.get('AffordableHousing') in markers:
            house_markers = markers_data.loc[markers_data['Category'] == 'AffordableHousing']
            house_markers.reset_index(drop=True, inplace=True)
            for idx in range(len(house_markers)):
                folium.Marker(
                    location=[house_markers.loc[idx, 'Lat'], house_markers.loc[idx, 'Long']],
                    popup=house_markers.loc[idx, 'Name'],
                    icon=folium.Icon(color='lightgray', icon='info-sign')
                ).add_to(m)
        if markers_dict.get('Shooting') in markers:
            shoot_markers = markers_data.loc[markers_data['Category'] == 'Shooting']
            shoot_markers.reset_index(drop=True, inplace=True)
            for idx in range(len(shoot_markers)):
                folium.Marker(
                    location=[shoot_markers.loc[idx, 'Lat'], shoot_markers.loc[idx, 'Long']],
                    popup=shoot_markers.loc[idx, 'Name'],
                    icon=folium.Icon(color='beige', icon='info-sign')
                ).add_to(m)

    # Remember to add layer control
    #folium.LayerControl().add_to(m)

    # Display zip code Label
    choropleth.add_child(
        folium.features.GeoJsonTooltip(fields=['tooltip1'], labels=False)
    )

    # Save map as html
    m.save('map.html')

    srcDoc = open('map.html', 'r', encoding='utf-8')
    source_code = srcDoc.read()

    return source_code

#-----------------------------------------------------------------------------------------------------------------------
# App layout
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

small_multiple_choropleths = []

# Remove the legend labels to line up all the graphs
# list of keys
keys = dd_list_stats
values = [''] * len(dd_list_stats)
labels_dict = dict(zip(keys, values))


for idx in range(len(dd_list_stats)):

    range_color_low = atx_zip_data[dd_list_stats[idx]].min()
    range_color_high = atx_zip_data[dd_list_stats[idx]].max()

    sm_ch_fig = px.choropleth(
        atx_zip_data, geojson=choro_geo_data, color=dd_list_stats[idx],
        color_continuous_scale="dense",
        locations="Zip Code", featureidkey="properties.ZCTA5CE10",
        projection="mercator",
        range_color=[range_color_low, range_color_high],
        labels = labels_dict
    )
    sm_ch_fig.update_geos(fitbounds="locations", visible=False)
    sm_ch_fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    small_multiple_choropleths.append(sm_ch_fig)

# Tab1
tab1 = html.Div([
    html.Div([
        # Dropdown 1
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
        # Dropdown 2
        html.Div([
            html.H6(children='Select a Statistic'),
            dcc.Dropdown(
                id='stat-2-selection-dd',
                options=[{'label': i, 'value': i} for i in dd_list_stats],
                value='Age - 18 years and over',
                clearable=False
            )
        ], style={'width': '49%', 'float': 'right', 'display': 'inline-block'})
    ], style={
        'borderBottom': 'thin lightgrey solid',
        'backgroundColor': 'rgb(250, 250, 250)',
        'padding': '10px 5px'
    }),
    html.Div([
        html.P("Markers Selection:"),
        dcc.Checklist(
            id='markers-tab1',
            options=[{'value': x, 'label': x}
                     for x in markers_options],
            #          value=markers_options[0],
            labelStyle={'display': 'inline-block'}
        ),
    ]),

    # Bivariate choropleth matp
    html.Div([
        html.Iframe(id='map', width='100%', height='600')
    ], style={'width': '98%', 'display': 'inline-block'}),

    # Scatterplot
    html.Div([
        html.Div([
            html.Button('Show Scatterplot', id='scat_show', disabled=True),
            html.Button('Hide Scatterplot', id='scat_hide', disabled=False)
        ]),
        html.Div([
            dcc.Graph(
                id='stat-1-graph'
            )
        ], style={'display': 'inline-block'}, id='scat_plot')
    ], style={'width': '85%'}),

    # Div for small multiples of the chorpleths
    html.Div([
        html.Table([
            html.Tbody([
                html.Tr([
                    html.Td([
                        html.P(dd_list_stats[0]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[0]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),
                    html.Td([
                        html.P(dd_list_stats[3]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[3]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),
                    html.Td([
                        html.P(dd_list_stats[4]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[4]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),

                ],
                style={'width': '100%', 'display': 'inline-block'}),
                html.Tr([
                    html.Td([
                        html.P(dd_list_stats[5]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[5]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),
                    html.Td([
                        html.P(dd_list_stats[7]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[7]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),
                    html.Td([
                        html.P(dd_list_stats[9]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[9]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),

                ],
                style={'width': '100%', 'display': 'inline-block'}),
                html.Tr([
                    html.Td([
                        html.P(dd_list_stats[10]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[10]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),
                    html.Td([
                        html.P(dd_list_stats[11]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[11]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),
                    html.Td([
                        html.P(dd_list_stats[12]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[12]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),

                ],
                style={'width': '100%', 'display': 'inline-block'}),
                html.Tr([
                    html.Td([
                        html.P(dd_list_stats[13]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[13]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),
                    html.Td([
                        html.P(dd_list_stats[14]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[14]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),
                    html.Td([
                        html.P(dd_list_stats[15]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[15]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),

                ],
                style={'width': '100%', 'display': 'inline-block'}),
                html.Tr([
                    html.Td([
                        html.P(dd_list_stats[23]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[23]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),
                    html.Td([
                        html.P(dd_list_stats[24]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[24]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),
                    html.Td([
                        html.P(dd_list_stats[25]),
                        dcc.Graph(
                            figure=small_multiple_choropleths[25]
                        )
                    ],
                    style={'width': '33.3%', 'display': 'inline-block', 'margin': '0', 'padding': '0',
                           'border': 'none'}),

                ],
                style={'width': '100%', 'display': 'inline-block'}),
            ],
            style={'width': '100%', 'display': 'inline-block'}),
        ],
        style={'width': '100%', 'display': 'inline-block', 'padding': '100px'}),
    ],
    style={'width': '100%', 'display': 'inline-block', 'align': 'center'}),
])


# Tab2
tab2 = html.Div([
    html.H1('Tab 2 here'),
    html.Div([
        html.H6(children='Select a Statistic'),
        dcc.Dropdown(
            id='tab-2-selection-dd',
            options=[{'label': i, 'value': i} for i in dd_decade],
            value='Total population',
            clearable=False
        )
    ],
    style={'width': '49%', 'display': 'inline-block'}),
    html.Div([
        html.Button('Play Animation', id='animation-play-btn', disabled=False),
        html.Button('Pause Animation', id='animation-pause-btn', disabled=True),
        dcc.Interval(id='auto-stepper',
                     interval=8 * 1000, # in milliseconds
                     n_intervals=0,
                     disabled=False
        ),
        dcc.Slider(
            id='year-slider',
            min=min(years),
            max=max(years),
            value=max(years),
            marks={str(year): str(year) for year in list(set(years))},
            step=None
        ),
    ]),
    html.Div([
        html.P("Markers Selection:"),
        dcc.Checklist(
            id='markers',
            options=[{'value': x, 'label': x}
                     for x in markers_options],
            #          value=markers_options[0],
            labelStyle={'display': 'inline-block'}
        ),
    ]),
    # Single variate choropleth map
    html.Div([
        html.Iframe(id='map2', width='100%', height='600')
    ]),
])

app.layout = html.Div([
    html.H1(children='Final Project'),
    html.H3(children='Author: Philip Tanofsky'),
    html.H5(children='DATA 608, Fall 2020'),
    html.H5(children='November 27, 2020'),

    # Help from: https://stackoverflow.com/questions/58897646/issues-with-assigning-callback-to-component-in-multi-tab-dash-application
    dcc.Tabs(id="tabs-example", value='tab-1-value', children=[
        dcc.Tab(id="tab-1", label='Austin: Bivariate Choropleth', value='tab-1-value'),
        dcc.Tab(id="tab-2", label='Austin: 2010s', value='tab-2-value'),
    ]),
    html.Div(id='tabs-content-example',
             children=tab1)
])


@app.callback(Output('tabs-content-example', 'children'),
             Input('tabs-example', 'value'))
def render_content(tab):
    if tab == 'tab-1-value':
        return tab1
    elif tab == 'tab-2-value':
        return tab2


@app.callback(
    Output('map', 'srcDoc'),
    Output('stat-1-graph', 'figure'),
    Input('stat-1-selection-dd', 'value'),
    Input('stat-2-selection-dd', 'value'),
    Input('markers-tab1', 'value')
)
def update_map_of_zip_codes(stat_01, stat_02, markers):
    fig1 = px.scatter(atx_zip_data, x=stat_01, y=stat_02)
    return build_atx_map(stat_01, stat_02, markers), fig1

@app.callback(
    Output('map2', 'srcDoc'),
    Input('year-slider', 'value'),
    Input('tab-2-selection-dd', 'value'),
    Input('markers', 'value')
)
def update_map_of_zip_codes_single_attribute(year, stat_01, markers):
    return build_atx_map_for_single_attribute(year, stat_01, markers)

@app.callback(
    Output('year-slider', 'value'),
    Input('auto-stepper', 'n_intervals')
)
def on_click(n_intervals):
    if n_intervals is None:
        return years[0]
    else:
        index = (n_intervals + 1) % len(years)
    return years[index]

@app.callback(
    Output('auto-stepper', 'disabled'),
    Output('animation-play-btn', 'disabled'),
    Output('animation-pause-btn', 'disabled'),
    Input('animation-play-btn', 'n_clicks'),
    Input('animation-pause-btn', 'n_clicks'),
)
def play_pause_slider(play_btn, pause_btn):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    set_slider_disabled = False
    set_play_button_disabled = False
    set_pause_button_disabled = False

    if 'animation-play-btn' in changed_id:
        set_slider_disabled = False
        set_play_button_disabled = True
        set_pause_button_disabled = False
    elif 'animation-pause-btn' in changed_id:
        set_slider_disabled = True
        set_play_button_disabled = False
        set_pause_button_disabled = True
    return set_slider_disabled, set_play_button_disabled, set_pause_button_disabled


@app.callback(
    Output('scat_plot', component_property='style'),
    Output('scat_show', 'disabled'),
    Output('scat_hide', 'disabled'),
    Input('scat_show', 'n_clicks'),
    Input('scat_hide', 'n_clicks'),
)
def hide_show_scatterplot(show_btn, hide_btn):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    scat_plot_hidden = {'display':'inline-block'}
    scat_show_disabled = False
    scat_hide_disabled = False

    if 'scat_show' in changed_id:
        scat_plot_hidden = {'display': 'inline-block'}
        scat_show_disabled = True
        scat_hide_disabled = False
    elif 'scat_hide' in changed_id:
        scat_plot_hidden = {'display':'none'}
        scat_show_disabled = False
        scat_hide_disabled = True
    return scat_plot_hidden, scat_show_disabled, scat_hide_disabled

if __name__ == '__main__':
    app.run_server(debug=True)