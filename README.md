# MARTA

## Description
This repo contains code to run a flask server which allows the user to create maps predicting the delays of MARTA trains 7 days in advance. Running server.py will initalize the server, using functions from the extra.py file and the stored model in model1.pkl. 

## How to Use Server
The server will show two text boxes, one titled 'Train Line' and the other titled 'Train ID'. Below are the combinations of train lines and train IDs that are valid: 

TRAIN IDs PER LINE COLOR

red: 401, 402, 403, 404, 405

blue: 101, 102, 103, 104, 105

green: 201, 202

gold: 301, 302, 303, 304, 305

Putting in one of thse combinations will generate a map showing the location of the train and a prediction of whether the train will be delayed in 7 days time. A red circle around a station means it is delayed, while a green circle is on time. 

## Extra.py Functions
There are a number of functions in the extra.py file. These are used to generate the data, pulling from 3 different API sources, as well as initializing the map. The main function is new_data, a function that takes in a line color and train id as parameters. This function generates new data and predicts using the model, then generates a map. 

## How the Model Works
The model itself is stored in the pickle file. The model is a gradient boosting classifier which produced an accuracy of 95.4% on the testing set. The model was trained on roughly a months and a half (47 days) worth of MARTA, weather, and traffic data, amounting to around 350,000 rows of data. A lag of 7 days was used on the delays in order to generate our predictions for a week in advance. 
