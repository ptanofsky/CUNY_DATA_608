# Assignment 4 attempt
# Based on below
# Interactive Visuazliations Part II
# Update graphics in Hover

# Group the data by borough, species, health, steward
# Variables
# boroname = {Manhattan, Staten Island, Brooklyn, Queens, Bronx}
# spc_common ... long list
# health = {Good, Fair, Poor, NaN}
# steward = {None, 1or2, 3or4, 4orMore, NaN}

# Question 1: What proportion of trees are in good, fair, or poor health according to the ‘health’ variable?

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Output, Input
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# df = pd.read_csv('https://plotly.github.io/datasets/country_indicators.csv')

# Query for list of Borough Names
soql_url_boros = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?' + \
                  '$select=distinct(boroname)')

df_boros = pd.read_json(soql_url_boros)
df_boros = df_boros.sort_values('boroname_1', ascending=True)


# Query for list of Tree Names
soql_url_trees = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?' + \
                  '$select=distinct(spc_common)')

df_trees = pd.read_json(soql_url_trees)

df_trees['spc_common_1'].fillna(value='Species Missing', inplace=True)
df_trees = df_trees.sort_values('spc_common_1', ascending=True)

# Query for initial dataset based on American beech and Bronx
soql_url = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?' +\
        '$select=boroname,spc_common, health, steward, count(tree_id)' +\
        '&$where=spc_common=\'American beech\' and boroname=\'Bronx\'' +\
        '&$group=boroname,spc_common, health, steward').replace(' ', '%20')
df = pd.read_json(soql_url)

# Set indicators for the boroughs
indicators_boros = df_boros['boroname_1']

# Set indicators for the trees
indicators_trees = df_trees['spc_common_1']

app.layout = html.Div([
    html.H1(children='Assignment 4'),
    html.H3(children='Author: Philip Tanofsky'),
    html.H5(children='DATA 608, Fall 2020'),
    html.H5(children='October 18, 2020'),
    html.Div([

        html.Div([
            html.H6(children='Select a Borough'),
            dcc.Dropdown(
                id='boro-selection-dd',
                options=[{'label': i, 'value': i} for i in indicators_boros],
                value='Bronx',
                clearable=False
            )
        ],
        style={'width': '49%', 'display': 'inline-block'}),

        html.Div([
            html.H6(children='Select a Tree Species'),
            dcc.Dropdown(
                id='tree-selection-dd',
                options=[{'label': i, 'value': i} for i in indicators_trees],
                value='American beech',
                clearable=False
            )
        ], style={'width': '49%', 'float': 'right', 'display': 'inline-block'})
    ], style={
        'borderBottom': 'thin lightgrey solid',
        'backgroundColor': 'rgb(250, 250, 250)',
        'padding': '10px 5px'
    }),

    html.Div([
        html.H3(children='Question 1'),
        html.Div(children='''
        What proportion of trees are in good, fair, or poor health according to the ‘health’ variable?
        '''),
        html.Div([
            dcc.Graph(
                id='tree-health-graph'
            )
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
    ]),

    html.Div([
        html.H3(children='Question 2'),
        html.Div(children='''
        Are stewards having an impact on the health of trees?
        '''),
        html.Div([
            dcc.Graph(
                id='tree-health-steward-graph'
            )
        ], style={'width': '90%', 'display': 'inline-block', 'padding': '0 20'}),
    ])
])

@app.callback(
    Output('tree-health-graph', 'figure'),
    Output('tree-health-steward-graph', 'figure'),
    [Input('boro-selection-dd', 'value'),
     Input('tree-selection-dd', 'value')])
def update_health_graph(boro_name, tree_name):

    soql_url = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?' +\
                '$select=boroname,spc_common, health, steward, count(tree_id)' +\
                '&$where=spc_common=\'' + tree_name + '\'' +\
                ' and boroname=\'' + boro_name + '\'' +\
                '&$group=boroname,spc_common, health, steward').replace(' ', '%20')
    dff = pd.read_json(soql_url)

    # Calculate total trees
    total_trees = dff['count_tree_id'].sum()

    fig1 = px.bar(dff, x=dff['health'], y=dff['count_tree_id'] / total_trees * 100)
    fig1.update_traces(hovertemplate =
                       '<i>Steward</i>: %{text}'+
                       '<br><b>Health</b>: %{x}<br>'+
                       '<b>Count Pct</b>: %{y}<br>',
                       text=dff['steward'])

    fig1.update_xaxes(title='Health')
    fig1.update_yaxes(title='Percentage')
    fig1.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
                      xaxis={'categoryorder':'array', 'categoryarray':['Good','Fair','Poor']})

    fig2 = px.bar(dff, x="health", y=dff['count_tree_id'] / total_trees * 100, barmode="group",
                  facet_col="steward",
                  category_orders={"steward": ["None", "1or2", "3or4", "4orMore"]})
    fig2.update_xaxes(title='Health')
    fig2.update_yaxes(title='Count')
    fig2.update_layout(xaxis={'categoryorder':'array', 'categoryarray':['Good','Fair','Poor']})

    return fig1, fig2

if __name__ == '__main__':
    app.run_server(debug=True)










