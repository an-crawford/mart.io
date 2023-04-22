import pandas as pd
import requests
import json
from datetime import datetime
import networkx as nx
import numpy as np
import folium
import pickle

model7 = pickle.load(open('model1.pkl', 'rb'))
def weather():
    weatherresponse = requests.get("http://api.weatherapi.com/v1/current.json?key=4ac0fd68834c49aea39174241230702&q=Atlanta&aqi=no")

    weatherdata = json.loads(weatherresponse.text)
    weatherdata['current']['condition'] = weatherdata['current']['condition']['text']
    weathertable = pd.DataFrame(weatherdata['current'], index=[0])
    weathertable = weathertable[['last_updated', 'temp_f', 'condition', 'wind_mph', 'wind_degree', 'wind_dir', 'pressure_mb','precip_in', 'humidity', 'cloud','feelslike_f','vis_miles', 'uv', 'gust_mph']]

    return weathertable

def traffic():
    url_one = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=33.714718%2C-84.241063&destinations=33.764995%2C-84.493572&departure_time=now&key"
    url_two = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=33.694841%2C-84.404754&destinations=33.891597%2C-84.259319&departure_time=now&key="
    payload={}
    headers = {}
    response_one = requests.request("GET", url_one, headers=headers, data=payload)
    response_two = requests.request("GET", url_two, headers=headers, data=payload)
    import re
    from datetime import datetime
    #print(response_two.text)
    response_one_json= response_one.json()
    r12 = response_one_json['rows'][0]
    r13 = r12['elements'][0]
    new_val = r13['duration_in_traffic']['text']
    response_two_json = response_two.json()
    r22 = response_two_json['rows'][0]
    r32 = r22['elements'][0]
    new_val2 = r32['duration_in_traffic']['text']
    #new_vals = new_val, new_val2
    new_val = re.findall(r'\d+', new_val)
    new_val2 = re.findall(r'\d+', new_val2)
    now =datetime.now()
    dt = now.strftime("%m/%d/%Y, %H:%M:%S")
    return new_val[0], new_val2[0], dt

def rail():
    import warnings
    warnings.filterwarnings("ignore")
    railresponse = requests.get("https://developerservices.itsmarta.com:18096/railrealtimearrivals?apiKey=e2a5883f-81b4-4965-bd26-95dde75d5adc", verify = False)

    raildata = json.loads(railresponse.text)
    railtable = pd.DataFrame(raildata['RailArrivals'])
    for i in range(len(railtable)):
        railtable['EVENT_TIME'].iloc[i] = datetime.strptime(railtable['EVENT_TIME'].iloc[i], '%Y-%m-%dT%H:%M:%SZ')
        railtable['NEXT_ARR'].iloc[i] = datetime.strptime(railtable['NEXT_ARR'].iloc[i], '%Y-%m-%dT%H:%M:%SZ')
        railtable['RESPONSETIMESTAMP'].iloc[i] = datetime.strptime(railtable['RESPONSETIMESTAMP'].iloc[i], '%Y-%m-%dT%H:%M:%SZ')

    railtable['DELAYSECONDS'] = railtable['DELAY'].str.extract('(\d+)').astype(float)
    railtable['Latitude'] = railtable['VEHICLELONGITUDE']
    railtable['Longitude'] = railtable['VEHICLELATITUDE']
    railtable = railtable.drop(columns = ['VEHICLELATITUDE', 'VEHICLELONGITUDE'], axis =1)
    #railtable.to_csv('railtable.csv')
    return railtable

class Stops:
    def __init__(self, id, code, name, lat, lon):
        self.id = id
        self.code = code
        self.name = name
        #self.line = line
        #self.type = type
        self.lat = float(lat)
        self.lon = float(lon)

    def get_name(self):
        return self.name
    
    #def get_line(self):
        #return self.line
    
    #def get_type(self):
        #return self.type
    
    def get_location(self):
        return (self.lat, self.lon)


def create_stations(filename):
    df = pd.read_csv(filename)
    stops = {} # can also do a list and append each instance to it stops.append(Stops(row['stop_id'], row['stop_code'], row['stop_name'], row["stop_lat"], row["stop_lon"]))
    for index, row in df.iterrows():
        row['stop_name'] = row['stop_name'].lower().replace(" ", "_")
        instance_name = row['stop_name'].lower().replace(" ", "_")
        instance_content = Stops(row['stop_id'], row['stop_code'], row['stop_name'], row["stop_lat"], row["stop_lon"])
        setattr(instance_content, instance_name, instance_content) # creates a new instance variable on the Team object, using the value of instance_name as the variable name.
        stops[instance_name] = instance_content
    return stops
x_cols = ['temp_f', 'condition', 'wind_mph', 'wind_degree', 'wind_dir', 'pressure_mb', 
       'precip_in', 'humidity', 'cloud', 'feelslike_f', 'gust_mph', 'I-20 Travel Time', 'I-85 Travel Time',
       'STATION', 'LINE', 'TRAIN_ID']

def new_data(line = 'red', train = '404'):
    df_traffic = pd.DataFrame( columns = ['I-20 Travel Time', 'I-85 Travel Time', 'Date/Time'])
    df_weather = pd.DataFrame(columns = ['last_updated', 'temp_f', 'condition', 'wind_mph', 'wind_degree', 'wind_dir', 'pressure_mb','precip_in', 'humidity', 'cloud','feelslike_f','vis_miles', 'uv', 'gust_mph'])
    df_traffic.loc[len(df_traffic.index)] = list(traffic())
    df_weather.loc[len(df_weather.index)] = list(weather().loc[0])
    df_traffic['Date/Time']=pd.to_datetime(df_traffic['Date/Time'], errors='coerce')
    df_traffic['dt'] = df_traffic['Date/Time']
    df_weather['last_updated'] = pd.to_datetime(df_weather['last_updated'])
    df_weather['last_update'] = df_weather['last_updated']
    comb = df_weather.merge(df_traffic, left_index=True, right_index=True)
    comb = comb.set_index('dt')
    rails = rail()
    rails = rails.sort_values(by = 'EVENT_TIME').set_index('EVENT_TIME')
    rails.index = pd.to_datetime(rails.index, errors = 'coerce')
    data = pd.merge_asof(rails, comb, left_on = 'EVENT_TIME', right_on= 'dt',direction = 'nearest',tolerance =pd.Timedelta('10 min')).dropna()
    X = data[x_cols]
    pred = pd.Series(model7.predict(X))
    predgreen = pd.Series(model7.predict_proba(X)[:,0])
    predred = pd.Series(model7.predict_proba(X)[:,1])
    XP = X.merge(pred.rename('Predicted'), left_index=True, right_index=True)
    XP = XP.merge(predgreen.rename('Proba Green'), left_index = True, right_index = True)
    XP = XP.merge(predred.rename('Proba Red'), left_index = True, right_index = True)
    XP = XP[['STATION', 'LINE', 'TRAIN_ID', 'Predicted', 'Proba Green', 'Proba Red']].drop_duplicates()
    XP['Color'] = np.where(XP['Predicted'] == 1, 'Red', 'Green')
    #XP2 = XP.loc[(XP['TRAIN_ID']==train) & (XP['LINE']==line)].drop(columns = ['TRAIN_ID', 'LINE', 'Predicted'], axis =1)
    XP2 = XP.loc[XP['TRAIN_ID']==train].drop(columns = ['TRAIN_ID', 'LINE', 'Predicted'], axis =1)
    XP2['STATION'] = XP2['STATION'].str.lower().str.replace(' ', '_') 
    XP2['Color'] = XP2['Color'].str.lower()
    XP3 = XP2.set_index('STATION')
    XP5 = XP3.copy()
    XP3 = XP3.drop(columns = ['Proba Green', 'Proba Red'], axis =1)
    XP5 = XP5[['Proba Green', 'Proba Red']]
    #print(XP5.loc)
    print(pred.value_counts())
    nodes = create_stations("data/MARTA_Stops.csv")
    edges = pd.read_csv("data/MARTA_edges.csv")
    #print(list(XP3.index))
    
    for k in list(nodes.keys()):
        if k not in list(XP3.index):
            del nodes[k]
    #display(nodes)
    #display(edges)
    edges = edges.loc[(edges['source'].isin(list(XP3.index))) & (edges['dest'].isin(list(XP3.index)))]
    G = nx.from_pandas_edgelist(edges, 'source', 'dest', edge_attr=['duration', 'line'])
    weights = {edge: duration for edge, duration in nx.get_edge_attributes(G, 'duration').items()}
    color = {edge: line for edge, line in nx.get_edge_attributes(G, 'line').items()}
    #display(edges)
    # pos = {}
    # for node in nodes:
    #     pos[node] = (nodes[node].lon, nodes[node].lat)

    # plt.figure(figsize=(10, 10))
    # nx.draw_networkx(G, pos=pos, with_labels=True, width=list(weights.values()))

    m = folium.Map(location=[33.7490, -84.3880], zoom_start=12, tiles = "CartoDB Positron") # set the initial location and zoom level of the map
    #print(list(G.edges()))
    for edge in G.edges():
        u, v = edge
        folium.PolyLine(locations=[(nodes[u].lat, nodes[u].lon), (nodes[v].lat, nodes[v].lon)],
                        weight=weights[edge]**(1/2)*2, color = line, zindex = 1).add_to(m) # add edges as polylines with weight proportional to duration
        
    for node in list(XP3.index):
        XP4 = XP3.loc[node].to_json()
        XP4 = XP4[10:]
        color = XP4[:-2]
        s= pd.Series(XP5.loc[node]).to_string()
        folium.CircleMarker(location=[nodes[node].lat, nodes[node].lon], popup=(node+ ' '+ s), radius= 5, color = color, fill_color = color, fill_opacity = .8).add_to(m) # add markers for each node
    #XP4 = XP3.loc['airport_station'].to_json()
    #XP4 = XP4[9:]
    #print(XP4[:-1])
    m.save('map.html')
    return m

new_data('blue', '102')
