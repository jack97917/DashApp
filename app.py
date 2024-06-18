
import dash
import dash_leaflet as dl
import dash_html_components as html
import dash_core_components as dcc
import dash_table
import pandas as pd
from OSGridConverter import grid2latlong
import matplotlib.colors as mcolors
import matplotlib.cm as cm
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import json
import dash_leaflet as dl
import gunicorn


# Create the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server


# Create the layout
app.layout = html.Div([
    html.H3("Severn Trent Water EDM Storm Overflow Returns 2023", style={"textAlign": "center"}),
    
if __name__ == '__main__':
    app.run_server(debug=True)
