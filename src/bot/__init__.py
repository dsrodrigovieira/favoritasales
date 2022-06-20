from flask import Response, request, Flask
import pandas as pd
import requests
import json
import os

TOKEN = ''
REPLY_OPTIONS = ('See details','Search other store', 'Leave')

def get_message():
    url = 'https://api.telegram.org/bot{}/getUpdates'.format(TOKEN)
    r = requests.post( url, data={'offset': '-1' })

    return r.json()

def parse_message( message ):    

    chat_id = message['message']['chat']['id']
    text = message['message']['text']

    text = text.replace('/','')

    try:
        text = int(text)

    except ValueError:
        if REPLY_OPTIONS.__contains__(text):
            text
        elif text != 'start':
            text = 'error'
        else: text

    return chat_id, text

def load_dataset( store_id ):  

    df_test_raw   = pd.read_csv('data/test.csv')
    df_stores_raw = pd.read_csv('data/stores.csv')
    df_oil_raw    = pd.read_csv('data/oil.csv')
    
    data = pd.merge(df_test_raw, df_oil_raw, how='left', on='date')
    data = pd.merge(data, df_stores_raw, how='left', on='store_nbr')
    data = data.rename(columns={'type':'store_type','cluster':'store_cluster'})

    # choose store for prediction
    data = data[data['store_nbr']==store_id]

    if data.empty:
        data = 'error'
    else:
        # convert Dataframe to json
        data = json.dumps(data.to_dict(orient='records'))

    return data

def predict( data ):
    
    # API call
    url = 'https://favoritasales.herokuapp.com/predict'
    header = {'Content-type': 'application/json'}

    r = requests.post(url, data=data, headers=header)

    return pd.DataFrame(r.json(), columns=r.json()[0].keys())

def plots( data ):    
    # API call
    url = 'https://favoritasales.herokuapp.com/viz'
    header = {'Content-type': 'application/json'}

    r = requests.post(url, data=data, headers=header)

    file = open('data/plots.png', 'wb')
    file.write(r.content)
    file.close()

    return None

def send_message( text, chat_id ): 
    payload = { 'chat_id': chat_id, 'text': text }    

    url = 'https://api.telegram.org/bot{}/sendMessage'.format(TOKEN)
    r = requests.post( url, data=payload )

    return None

def send_photo( chat_id ):
    payload = {
        'chat_id': chat_id,        
        'caption': "Here's detailed info"
    }

    file = {
        'photo': open('data/plots.png', 'rb')
    }

    url = 'https://api.telegram.org/bot{}/sendPhoto'.format(TOKEN)
    r = requests.post( url, data=payload, files=file )

    return None

def reply_message( chat_id ):
    # try:
    header = {'Content-type': 'application/json'}
    
    payload = {'chat_id': chat_id, 'text': 'Select an option below',
                'reply_markup': { 'keyboard':
                                [[{'text':REPLY_OPTIONS[0]}],
                                    [{'text':REPLY_OPTIONS[1]}],
                                    [{'text':REPLY_OPTIONS[2]}]],
                                    'resize_keyboard': True,
                                    'one_time_keyboard':True }}

    data = json.dumps(payload)

    url = 'https://api.telegram.org/bot{}/sendMessage'.format(TOKEN)
    r = requests.post( url, headers=header, data=data)

    return r.json()

def reply_image( chat_id ):
    # try:
    header = {'Content-type': 'application/json'}
    
    payload = {'chat_id': chat_id, 'text': 'Select an option below',
                'reply_markup': { 'keyboard':
                                [[{'text':REPLY_OPTIONS[1]}],
                                    [{'text':REPLY_OPTIONS[2]}]],
                                    'resize_keyboard': True,
                                    'one_time_keyboard':True }}

    data = json.dumps(payload)

    url = 'https://api.telegram.org/bot{}/sendMessage'.format(TOKEN)
    r = requests.post( url, headers=header, data=data)

    return r.json()

# API initialize
app = Flask( __name__ )
@app.route('/',methods=['GET','POST'])

def index():  

    if request.method == 'POST':

        message = request.get_json() 
        
        chat_id, store_id = parse_message(message)

        if str(store_id).isnumeric():
            # loading data
            data = load_dataset(store_id)
            if data != 'error':
                send_message('Loading data...', chat_id)
                # prediction
                pred = predict(data)
                pred.to_csv('data/pred.csv',index=False)                
                # calculation
                _pred = pred[['store_nbr','prediction']].groupby('store_nbr').sum().reset_index()
                # send message
                msg = 'Store number {} will sell US${:,.2f} in the next 2 weeks'.format(_pred['store_nbr'].values[0], _pred['prediction'].values[0]) 
                send_message(msg, chat_id)
                reply_message(chat_id)
                return Response('OK', status=200)
            else:
                send_message('An error ocurred. Please try other store.',chat_id)
                return Response('OK', status=200)
        else:
            if store_id == 'start':
                send_message('Send store ID', chat_id )  
                return Response('OK', status=200)  
            if store_id == REPLY_OPTIONS[0]:
                data = json.dumps(pd.read_csv('data/pred.csv').to_dict(orient='records'))
                plots(data)
                send_message('Sending image...', chat_id )
                send_photo(chat_id)
                reply_image(chat_id)
                return Response('OK', status=200)
            if store_id == REPLY_OPTIONS[1]:
                send_message('Send store ID', chat_id )
                return Response('OK', status=200)
            if store_id == REPLY_OPTIONS[2]:
                send_message('Thanks for using this application!', chat_id ) 
                return Response('OK', status=200)             
            else:
                send_message('Are you sure this is a store ID?', chat_id )
            return Response('OK', status=200)    
    else:
        send_message('<h1>Favorita Telegram BOT</h1>', chat_id )
        return Response('OK', status=200)

if __name__ == '__main__':
    port = os.environ.get('PORT',5000)
    app.run(host='0.0.0.0', port=port)
