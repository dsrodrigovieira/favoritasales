import pandas as pd
import pickle
import os
from flask                       import Flask, request, Response, send_file
from favorita.Favorita           import Favorita
from visualization.Visualization import Visualization

# loading model
model = pickle.load( open('./models/model_favorita.pkl', 'rb') )

app = Flask(__name__)

@app.route( '/predict', methods=['POST'] )
def favorita_predict():
    
    json_data = request.get_json()
    
    if json_data: #there's data

        raw_data = pd.DataFrame(json_data)

        # instantiate rossmann class
        pipeline = Favorita()
        
        # data cleaning
        data_cleaned = pipeline.data_cleaning(raw_data)

        # feature engineering
        data_transformed = pipeline.feature_engineering(data_cleaned)

        # data preparation
        data_prediction = pipeline.data_preparation(data_transformed)

        # prediction
        data_predicted = pipeline.prediction(model, raw_data, data_prediction)

        return data_predicted
        
    else:
        return Response('{}',status=200,mimetype='application/json')    

@app.route( '/viz', methods=['POST'] )
def favorita_visualization():

    raw_json = request.get_json()

    if raw_json:

        raw_data = pd.DataFrame(raw_json)
    
        pipeline = Visualization()

        plot_data = pipeline.data_transformation(raw_data)

        pipeline.plots(plot_data)

        return send_file('./plots.png', mimetype='image/png')

    else:
        return Response('{}',status=200,mimetype='application/json') 

if __name__ == '__main__':
    port = os.environ.get('PORT', 5000)
    app.run(host='0.0.0.0', port=port)