
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

#import EDM dataset
data= pd.read_excel(r'C:\Users\jack.hickson\OneDrive - Aqua Consultants Limited\Documents\SevernTrent\STW EDM Return Map\src\data\EDM 2023 Storm Overflow Annual Return - all water and sewerage companies.xlsx', sheet_name='Severn Trent 2023', skiprows=1)



# Create DataFrame
EDM_df = pd.DataFrame(data)

# Convert GridRef to LatLong and add to DataFrame
def convert_grid_to_latlong(grid_ref):
    try:
        latlong = grid2latlong(grid_ref)
        return latlong.latitude, latlong.longitude
    except Exception as e:
        return None, None
    

# Apply the function to the DataFrame and create new columns for latitude and longitude
EDM_df[['Latitude', 'Longitude']] = EDM_df['Outlet Discharge NGR\n(EA Consents Database)'].apply(
    lambda x: pd.Series(convert_grid_to_latlong(x)))

selected_columns = ['Site Name\n(EA Consents Database)', 'Activity Reference on Permit', 'Storm Discharge Asset Type', 'Outlet Discharge NGR\n(EA Consents Database)', 'Total Duration (hrs) all spills prior to processing through 12-24h count method',	'EDM Operation -\n% of reporting period EDM operational', 'Unique ID']
EDM_df_trim = EDM_df[selected_columns]
new_column_names = {'Site Name\n(EA Consents Database)': 'Site Name', 'Outlet Discharge NGR\n(EA Consents Database)': 'Outlet Discharge NGR', 'Total Duration (hrs) all spills prior to processing through 12-24h count method': 'Total Duration (hrs)', 'EDM Operation -\n% of reporting period EDM operational':'EDM Operation (%)'}
EDM_df_trim = EDM_df_trim.rename(columns=new_column_names)

# Function to map percentage to color
def percentage_to_color(percentage):
    if percentage == 100:
        return '#F506D1'  # Pink color for 100%
    else:
        norm = mcolors.Normalize(vmin=0, vmax=99)  # Normalize between 0 and 99
        cmap = cm.get_cmap('RdYlGn')  # Choose a colormap (Red to Yellow to Green)
        rgba_color = cmap(norm(percentage))
        return mcolors.to_hex(rgba_color)

# Function to normalize radius
def normalize(value, min_value, max_value, min_radius=1, max_radius=15, power=0.7):
    normalized = (value - min_value) / (max_value - min_value)
    adjusted = normalized ** power  # Apply a power transformation
    radius = min_radius + (adjusted * (max_radius - min_radius))
    return radius

# Create markers
min_value = EDM_df['Total Duration (hrs) all spills prior to processing through 12-24h count method'].min()
max_value = EDM_df['Total Duration (hrs) all spills prior to processing through 12-24h count method'].max()


markers = [
    dl.CircleMarker(
        center=[row['Latitude'], row['Longitude']],
        radius=normalize(row['Total Duration (hrs) all spills prior to processing through 12-24h count method'], min_value, max_value),
        color=percentage_to_color(row['EDM Operation -\n% of reporting period EDM operational']),
        fill=True,
        fillColor=percentage_to_color(row['EDM Operation -\n% of reporting period EDM operational']),
        fillOpacity=0.7,
        children=[
            dl.Tooltip(f"{row['Site Name\n(EA Consents Database)']} - {row['EDM Operation -\n% of reporting period EDM operational']}% EDM Operational"),
            dl.Popup([
                html.Div([
                    html.B(f"Site Name: {row['Site Name\n(EA Consents Database)']}"),
                    html.Br(),
                    f"EDM Operation: {row['EDM Operation -\n% of reporting period EDM operational']}%",
                    html.Br(),
                    f"Total Duration: {row['Total Duration (hrs) all spills prior to processing through 12-24h count method']} hrs"
                ])
            ])
        ]
    ) for _, row in EDM_df.iterrows()
]


## Load json file function
def load_geojson(filepath):
  with open(filepath, 'r', encoding='utf-8') as file:
    geojson_data = json.load(file)
  return geojson_data

# Create the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# Create the layout
app.layout = html.Div([
    html.H3("Severn Trent Water EDM Storm Overflow Returns 2023", style={"textAlign": "center"}),
    dl.Map(
        children=[
           dl.LayersControl(
                [
            dl.BaseLayer(dl.TileLayer(url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", id="CartoDB Dark Matter"), name="CartoDB Dark Matter", checked=True),
            dl.BaseLayer(dl.TileLayer(url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", id="ESRI Satellite"), name="ESRI Satellite", checked=True),
            dl.BaseLayer(dl.TileLayer(url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", id="opentopo"), name="OpenTopoMap", checked=True),
            dl.BaseLayer(dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", id="osm"), name="Open Street Map", checked=True),
            ## Have used mapshaper simplified topo_geojson . converted online but can used it in python direct if needs be
            dl.Overlay(dl.LayerGroup([dl.GeoJSON(id="catchments", data=load_geojson(r'C:\Users\jack.hickson\OneDrive - Aqua Consultants Limited\Documents\SevernTrent\STW_Catchments_Region_2023\simple_topo_geojson.json'), options=dict(style=dict(color="red", fillOpacity=0.2)))]), name="Catchments", checked=True),
            dl.Overlay(dl.LayerGroup(markers, id="event_monitoring_duration"), name="Event Monitoring Duration", checked=True),
       ],
                position='topleft')],

        style={'width': '100%', 'height': '600px'},
        center=[52.4973492, -1.8636315],
        zoom=7
    ),
    html.Div([
        dcc.Input(id='search-input', type='text', placeholder='Search Site Name'),
        dash_table.DataTable(
            id='datatable',
            columns=[{"name": i, "id": i} for i in EDM_df_trim.columns],
            data=EDM_df_trim.to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
            style_data={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
            page_size=100,  # Number of rows per page
            
        ),
        html.Iframe(srcDoc=open(r"C:\Users\jack.hickson\OneDrive - Aqua Consultants Limited\Documents\SevernTrent\EDM Dash\legend.html").read(), style={"width": "300px", "height": "400px", "border": "none", "position": "absolute", "right": "10px", "top": "10px", "zIndex": "9999",})
    ])
])

@app.callback(
    Output('datatable', 'data'),
    [Input('search-input', 'value')]
)

#'''def update_table(search_value):
    # Filter your dataframe based on the search value
#    filtered_data = EDM_df_trim[EDM_df_trim['Site Name'].astype(str).str.contains(str(search_value), case=False)]
#    return filtered_data.to_dict('records')'''

def update_table(search_value):
  # Filter your dataframe based on the search value
  if not search_value:  # Check if search_value is empty (None or empty string)
    filtered_data = EDM_df_trim.copy()  # Return all rows if search is empty
  else:
    filtered_data = EDM_df_trim[EDM_df_trim['Site Name'].astype(str).str.contains(str(search_value), case=False)]
  return filtered_data.to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=True)