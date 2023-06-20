# -*- coding: utf-8 -*-
"""
Created on Fri Nov  4 12:20:08 2022

@author: vinig
"""

import time
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import ta
import plotly.express as px
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler



mt5.initialize()
d = mt5.terminal_info()
ativo = "WIN$"
ativo2 = "WDO$N"
diretorio = 'C:/Users/davir/Desktop/Trade/'
date_from = datetime.today()
time_frame=mt5.TIMEFRAME_M5
dias=12000
ticker_atual_win="WINZ22"
ticker_atual_wdo="WDOZ22"



#Coleta de dados do WIN:
rates_win = mt5.copy_rates_from(ativo,time_frame, date_from,dias)
rates_frame_win = pd.DataFrame(rates_win)
rates_frame_win ['time']=pd.to_datetime(rates_frame_win['time'], unit='s')
close_win = rates_frame_win['close']
close_win.index = rates_frame_win['time']
close_win = pd.DataFrame(close_win)

#Coleta de dados do WDO:
rates_wdo = mt5.copy_rates_from(ativo2,time_frame, date_from,dias)
rates_frame_wdo = pd.DataFrame(rates_wdo)
rates_frame_wdo ['time']=pd.to_datetime(rates_frame_wdo['time'], unit='s')
close_wdo = rates_frame_wdo['close']
close_wdo.index = rates_frame_wdo['time']
close_wdo = pd.DataFrame(close_wdo)
close_wdo = close_wdo.rename(columns={'close': 'closewdo'})

#Criando o index comum aos dois:
base=pd.merge(rates_frame_win['time'], rates_frame_wdo['time'], how='inner')
base.index=base['time']
base = pd.DataFrame(base)
base = base.drop(columns='time')

#Calculando a variação em relação ao fechamento do último dia
base2 = pd.concat([close_win, close_wdo], axis=1,).dropna()
base2['closedaywin']=0.0
base2['closedaywdo']=0.0

for i in range(0,len(base2.index)):
    if base2.index[i].day != base2.index[i-1].day:
        base2['closedaywin'][i]=base2['close'][i-1]
    else:
        base2['closedaywin'][i]=base2['closedaywin'][i-1]
        
for i in range(0,len(base2.index)):
    if base2.index[i].day != base2.index[i-1].day:
        base2['closedaywdo'][i]=base2['closewdo'][i-1]
    else:
        base2['closedaywdo'][i]=base2['closedaywdo'][i-1]

#Calculando o log da variação
base2['lnwin']=0.00
base2['lnwdo']=0.00

for k in range(0,len(base2.index)):
    base2['lnwin'][k]=np.log(base2['close'][k]/base2['closedaywin'][k])
    base2['lnwdo'][k]=np.log(base2['closewdo'][k]/base2['closedaywdo'][k])            

#Recortando o primeiro dia inteiro    
index_init=[]
for i in range(0,108):
    if base2.index[i].day!=base2.index[i-1].day:
        index_init=i

base2 = base2[index_init:]



#Definindo os previsores (X):
win_x = base2['lnwin'].values.reshape(-1,1)
wdo_y = base2['lnwdo'].values    
    
#Criando a rede neural:
regressor_rna_win = MLPRegressor()
regressor_rna_win.fit(win_x, wdo_y)

#Calculando o score da Rede Neural:
regressor_rna_win.score(win_x, wdo_y)

#Gerando o gráfico
grafico = px.scatter(x=win_x.ravel(), y=wdo_y.ravel())
grafico.add_scatter(x = win_x.ravel(), y= regressor_rna_win.predict(win_x), name='Rede Neural')
grafico.show()

regressor_rna_win.predict([[0.0156]])

error = wdo_y-regressor_rna_win.predict(win_x)
error_scale = StandardScaler()
error = error_scale.fit_transform(error.reshape(-1,1))



