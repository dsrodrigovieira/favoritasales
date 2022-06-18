from flask import Flask, request, Response, send_file
from favorita.Favorita import Favorita
from favorita.Visualization import Visualization
import pandas as pd
import pickle

# loading model
model = pickle.load( open('../models/model_favorita.pkl', 'rb') )

app = Flask(__name__)

@app.route( '/favorita/predict', methods=['POST'] )
def favorita_predict():

    print('start')
    
    test_json = request.get_json()
    print('get_json')
    
    if test_json: #there's data

        test_raw = pd.DataFrame(test_json)

        # instantiate rossmann class
        pipeline = Favorita()
        
        # data cleaning
        data_cleaned = pipeline.data_cleaning(test_raw)
        print('data_cleaned')

        # feature engineering
        data_transformed = pipeline.feature_engineering(data_cleaned)
        print('data_transformed')

        # data preparation
        data_prediction = pipeline.data_preparation(data_transformed)
        print('data_prediction')

        # prediction
        data_predicted = pipeline.prediction(model, test_raw, data_prediction)
        print('data_predicted')

        return data_predicted
        
    else:
        return Response('{}',status=200,mimetype='application/json')    

@app.route( '/favorita/viz', methods=['POST'] )
def favorita_visualization():

    raw_data_json = request.get_json()

    if raw_data_json:

        data_json = pd.DataFrame(raw_data_json)
    
        pipeline = Visualization()

        pipeline.data_transformation(data_json)

        pipeline.plots()

        return send_file('./plots.png', mimetype='image/png')

    else:
        return Response('{}',status=200,mimetype='application/json')      

if __name__ == '__main__':
    app.run('0.0.0.0')