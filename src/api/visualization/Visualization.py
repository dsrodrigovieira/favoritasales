import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

px = 1/plt.rcParams['figure.dpi']

class Visualization ( object ):
    
    def __init__(self):

        self.data_lineplot = pd.DataFrame()
        self.data_barplot = pd.DataFrame()
        self.data_store = pd.DataFrame()


    def data_transformation ( self, data ):

        data['date'] = pd.to_datetime(pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d'))

        df_lineplot = data[['store_nbr','date','prediction']].groupby(['store_nbr','date']).sum().reset_index()
        df_lineplot['month']      = df_lineplot['date'].dt.month_name()
        df_lineplot['day']        = df_lineplot['date'].dt.day
        df_lineplot['month_day']  = df_lineplot.apply(lambda x: x['month'][:3]+', '+str(x['day'])+'th', axis=1)
        df_lineplot['prediction'] = df_lineplot['prediction'] / 1000

        df_barplot = data[['store_nbr','family','prediction']].groupby(['store_nbr','family']).sum().sort_values('prediction',ascending=False).reset_index()

        self.store = data['store_nbr'].unique()[0]

        return df_lineplot, df_barplot
    
    def plots( self, data ):        
        
        top10 = data[1].head(10)
        bot10 = data[1].tail(10)
        
        plt.figure(figsize=(1667*px,2000*px), tight_layout=True)
        sns.set_context("poster")
        sns.set_style("darkgrid")

        plt.subplot(3,1,2)
        g1 = sns.barplot(data=top10, x='prediction', y='family', palette="Blues_r")
        g1.set_title('Sales predictions @Store#{} - Top 10 families'.format(self.store))
        g1.set_xlabel('')
        g1.set_ylabel('')

        plt.subplot(3,1,3)
        g2 = sns.barplot(data=bot10, x='prediction', y='family', palette='Reds')
        g2.set_title('Sales predictions @Store#{} - Bottom 10 families'.format(self.store))
        g2.set_xlabel('')
        g2.set_ylabel('')

        plt.subplot(3,1,1)
        g3 = sns.lineplot(data=data[0], x='month_day', y='prediction')
        g3.set_title('Sales predictions for the next 2 weeks @Store#{}'.format(self.store))
        g3.set_xlabel('')
        g3.set_ylabel('Sales $k')

        plt.xticks(rotation=45)

        plt.savefig('./plots.png');

        return None