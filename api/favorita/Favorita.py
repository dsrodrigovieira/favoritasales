import pickle
import pandas as pd
import numpy as np
import datetime

class Favorita ( object ):
    
    def __init__( self ):
        self.home                 = '/PATH/'
        self.onpromotion_scaler   = pickle.load(open('../parameters/onpromotion_std.pkl','rb'))
        self.store_nbr_scaler     = pickle.load(open('../parameters/store_nbr_scaler.pkl','rb'))
        self.store_cluster_scaler = pickle.load(open('../parameters/store_cluster_scaler.pkl','rb'))
        self.oil_scaler           = pickle.load(open('../parameters/dcoilwtico_scaler.pkl','rb'))
        self.city_encoding        = pickle.load(open('../parameters/city_encoding.pkl','rb'))
        self.state_encoding       = pickle.load(open('../parameters/state_encoding.pkl','rb'))
        self.store_type_encoding  = pickle.load(open('../parameters/store_type_encoding.pkl','rb'))
        self.family_encoding      = pickle.load(open('../parameters/family_encoding.pkl','rb'))   
        self.predictions          = pd.DataFrame()     
        
    def data_cleaning( self, data ):
            # 
        return data
    
    def feature_engineering( self, data ):
        data['date'] = pd.to_datetime(data['date'])

        # setando colunas de datas
        data['day']          = data['date'].dt.day
        data['day_of_year']  = data['date'].dt.dayofyear
        data['month']        = data['date'].dt.month
        data['year']         = data['date'].dt.year
        data['week_of_year'] = data['date'].dt.weekofyear
        data['day_of_week']  = data['date'].dt.dayofweek #The day of the week with Monday=0, Sunday=6.

        # finais de semana e feriados não há registro de cotação. utilizando a média da semana para preencher esses NAs
        aux = data[['date','dcoilwtico']].copy()
        aux = aux.drop_duplicates(subset='date').reset_index(drop=True)
        aux['year_week'] = aux['date'].dt.strftime('%Y-%U')
        aux2 = aux[['year_week','dcoilwtico']].groupby('year_week').mean().reset_index()
        #excepcionalmente, a virada de 2015/2016 nao segue o padrao das demais pois a semana fica quebrada
        aux2.loc[aux2['year_week'] == '2016-00', 'dcoilwtico'] = aux2.loc[aux2['year_week'] == '2015-52', 'dcoilwtico'].values
        aux = pd.merge(aux, aux2, how='left', on='year_week')
        aux = aux.drop(columns=['dcoilwtico_x','year_week']).rename(columns={'dcoilwtico_y':'dcoilwtico'})
        data = pd.merge(data,aux, how='left', on='date')
        data['dcoilwtico_x'] = data[['dcoilwtico_x','dcoilwtico_y']].apply(lambda x: x['dcoilwtico_y'] if pd.isna(x['dcoilwtico_x']) else x['dcoilwtico_x'], axis = 1 )

        # removendo colunas extras criadas para tratamento dos NAs
        data = data.drop('dcoilwtico_y', axis=1).rename(columns={'dcoilwtico_x':'dcoilwtico'})
        
        return data
    
    def data_preparation( self, data ):

        cols = ['store_nbr', 'family', 'store_type', 'store_cluster',
                'year', 'city', 'state', 'day_sin', 'day_cos', 'onpromotion', 'dcoilwtico',
                'day_of_week_sin', 'day_of_week_cos', 'month_sin', 'month_cos',
                'week_of_year_sin', 'week_of_year_cos']

        # onpromotion
        data['onpromotion']   = self.onpromotion_scaler.transform(data[['onpromotion']].values)
        # store_nbr
        data['store_nbr']     = self.store_nbr_scaler.transform(data[['store_nbr']].values)
        # store_cluster
        data['store_cluster'] = self.store_cluster_scaler.transform(data[['store_cluster']].values)
        # oil
        data['dcoilwtico']    = self.oil_scaler.transform(data[['dcoilwtico']].values)
        # family
        data['family']        = self.family_encoding.transform(data[['family']].values)
        # city
        data['city']          = data['city'].apply(lambda x: self.city_encoding[x])
        # state
        data['state']         = data['state'].apply(lambda x: self.state_encoding[x])
        # store_type
        data['store_type']    = data['store_type'].apply(lambda x: self.store_type_encoding[x])        

        # day
        data['day_sin']          = data['day'].apply(lambda x: np.sin( x * ( 2 * np.pi / 30 ) ) )
        data['day_cos']          = data['day'].apply(lambda x: np.cos( x * ( 2 * np.pi / 30 ) ) )

        # day_of_week
        data['day_of_week_sin']  = data['day_of_week'].apply(lambda x: np.sin( x * ( 2 * np.pi / 7 ) ) )
        data['day_of_week_cos']  = data['day_of_week'].apply(lambda x: np.cos( x * ( 2 * np.pi / 7 ) ) )

        # day_of_year
        data['day_of_year_sin']  = data['day_of_year'].apply(lambda x: np.sin( x * ( 2 * np.pi / 365 ) ) )
        data['day_of_year_cos']  = data['day_of_year'].apply(lambda x: np.cos( x * ( 2 * np.pi / 365 ) ) )

        # month
        data['month_sin']        = data['month'].apply(lambda x: np.sin( x * ( 2 * np.pi / 12 ) ) )
        data['month_cos']        = data['month'].apply(lambda x: np.cos( x * ( 2 * np.pi / 12 ) ) )

        # week_of_year
        data['week_of_year_sin'] = data['week_of_year'].apply(lambda x: np.sin( x * ( 2 * np.pi / 52 ) ) )
        data['week_of_year_cos'] = data['week_of_year'].apply(lambda x: np.cos( x * ( 2 * np.pi / 52 ) ) )
        
        return data[cols]
    
    def prediction( self, model, original_data, test_data ):
        # prediction
        pred = model.predict(test_data)
        
        # join pred into the original data
        original_data['prediction'] = np.expm1(pred)

        original_data.to_csv('./df.csv',index=False)
        
        return original_data.to_json(orient='records', date_format='iso')

    