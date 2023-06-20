# -*- coding: utf-8 -*-
"""
Created on Wed Jun  1 23:59:36 2022

@author: davir
"""

#Importando as bibliotecas necessárias

import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import ta
#import vectorbt as vbt


mt5.initialize()
d = mt5.terminal_info()
ativo = "WIN$"
ativo2 = "WDO$N"
diretorio = 'C:/Users/davir/Desktop/Trade/'


######## 100 dias ####################
date_from = datetime.today()
time_frame=mt5.TIMEFRAME_M5
candles=40000

nivel01 = 2.5
nivel02 = 1.5
nivel03 = 2.0
gain01 = 1.1
gain02 = 1.4
gain03 = 1.9
loss01 = 4.5
loss02 = 1.9
loss03 = 2.4


def pair_trading(date_from, time_frame, candles, nivel01, nivel02, nivel03, gain01, gain02, gain03):

    # In[1]. Coleta do OHLC dos candles de 1 minuto (D-1)
        
    #Coleta de dados do WIN:
    rates_win = mt5.copy_rates_from(ativo,time_frame, date_from,candles)
    #for rate in rates_win:
       # print(rate)
    rates_frame_win = pd.DataFrame(rates_win)
    rates_frame_win ['time']=pd.to_datetime(rates_frame_win['time'], unit='s')
    close_win = rates_frame_win['close']
    close_win.index = rates_frame_win['time']
    close_win = pd.DataFrame(close_win)
    
    #Coleta de dados do WDO:
    rates_wdo = mt5.copy_rates_from(ativo2,time_frame, date_from,candles)
    #for rate in rates_wdo:
       # print(rate)
    rates_frame_wdo = pd.DataFrame(rates_wdo)
    rates_frame_wdo ['time']=pd.to_datetime(rates_frame_wdo['time'], unit='s')
    close_wdo = rates_frame_wdo['close']
    close_wdo.index = rates_frame_wdo['time']
    close_wdo = pd.DataFrame(close_wdo)
    close_wdo = close_wdo.rename(columns={'close': 'closewdo'})
    
    # In[2]. Concatenar as séries temporais (WIN x WDO):
    
    #Criando o index comum aos dois:
    base=pd.merge(rates_frame_win['time'], rates_frame_wdo['time'], how='inner')
    base.index=base['time']
    base = pd.DataFrame(base)
    base = base.drop(columns='time')
    
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
            
    
    # In[3]. Calcular o log das variações em relação ao preço de fechamento
    
    base2['lnwin']=0.00
    base2['lnwdo']=0.00
    
    for k in range(0,len(base2.index)):
        base2['lnwin'][k]=np.log(base2['close'][k]/base2['closedaywin'][k])
        base2['lnwdo'][k]=np.log(base2['closewdo'][k]/base2['closedaywdo'][k])
    
    #Colocando o RSI
    #base2['rsiwin']=ta.momentum.rsi(close=base2['close'], window=14)
    
    
    
    
    # In[4]. Recortando o primeiro dia inteiro
    
    index_init=[]
    for i in range(0,108):
        if base2.index[i].day!=base2.index[i-1].day:
            index_init=i
    
    base2 = base2[index_init:]
       
    
    
    # In[4]. Teste de Cointegração (Teste de Johansen)
    coint = sm.tsa.coint(base2['lnwin'],base2['lnwdo'])
    print("O p-value do Teste de Cointegração entre as 2 séries temporais foi de:", coint[1])
     
    
    # In[5]. Estimar a reta da regressão linear (para prazos diferentes):
    
    #Estimando a regressão WIN x WDO Geral (De todo o período)
    Y=base2['lnwin'].values
    X=base2['lnwdo'].values
    modelo = sm.OLS(Y, sm.add_constant(X)).fit()
    print(modelo.summary())
    
    #Descobrindo o índice de cada mudança de dia: 
    index_init2=[]
    cont_day=0
    for i in range(0,len(base2)):
        if base2.index[i].day!=base2.index[i-1].day:
            index_init2.append(i)
            cont_day=cont_day+1 
    resultado=[]
    erros_teste = []
    
    #Estimando a regressão WIN x WDO a cada 100 dias (período de teste)
    for m in range(0,len(index_init2)-100):
        base3=base2[index_init2[m]:index_init2[m+100]]
        Z=base3['lnwin'].values
        W=base3['lnwdo'].values    
        modelo = sm.OLS(Z, sm.add_constant(W)).fit()
        print(modelo.summary())
      
        # Cálculo dos resíduos
        modelo_residuos = modelo.resid # Residuos do modelo WIN x WDO
    
        #Teste de estacionariedade dos resíduos
        df_model01 = sm.tsa.adfuller(modelo_residuos)
        print ('O p-value do DF para o modelo é de:', sm.tsa.adfuller(modelo_residuos)[1])
    
        #Criação do Intervalo dos Resíduos
        int_sup = modelo_residuos.mean()+2*modelo_residuos.std()
        int_inf = modelo_residuos.mean()-2*modelo_residuos.std()           
    
        #Resíduos em Desvios-Padrão
        res_std=modelo_residuos/modelo_residuos.std()
        res_day = pd.DataFrame(res_std, index=base3.index)
        
        index_init3=[]
        for i in range(0,len(res_day)):
            if res_day.index[i].day!=res_day.index[i-1].day:
                index_init3.append(i)
        
    # In[6]. Validando no dia seguinte:
        #Coletando os coeficientes da regressão:
        coef = modelo.params[1]
        
        #Pegando o último dia da série de teste
        data_final = base3.index.date[len(base3)-1:len(base3)]
        base_teste = base2[base2.index.date==data_final+timedelta(days=1)]        
        yreal = base_teste['lnwin']
        base_teste['yproj'] = base_teste['lnwdo']*coef
        base_teste['resid_valid'] = yreal-base_teste['yproj']
        base_teste['resid_valid']=base_teste['resid_valid']/modelo_residuos.std()
        erros_teste.append(base_teste['resid_valid'].values)
        base_teste['compra01']=0.00
        base_teste['compra02']=0.00
        base_teste['compra03']=0.00
        base_teste['venda01']=0.00
        base_teste['venda02']=0.00
        base_teste['venda03']=0.00
        base_teste['resultado']=0.00
        base_teste['result_fin']=0.00
        base_teste['lucro_fin']=0.00
        pos_compra=0
        pos_venda=0
        prop_win=2
        prop_wdo=1
        
                 
    
        
        
        for k in range(0,len(base_teste)):
            if base_teste['resid_valid'][k]<=-nivel01 and pos_compra==0:
                base_teste['compra01'][k]=-base_teste['close'][k]*0.2*prop_win-base_teste['closewdo'][k]*prop_wdo*10
                pos_compra=1
                
            if base_teste['resid_valid'][k]>=-gain01 and pos_compra==1:
                base_teste['lucro_fin'][k]=((base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10)+base_teste['compra01'][k-1])
                pos_compra=22
       
            if base_teste['resid_valid'][k]<=-loss01 and pos_compra==1:
                base_teste['lucro_fin'][k]=((base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10)+base_teste['compra01'][k-1])
                pos_compra=22
       
        
            ################################################################# 
       
            # if base_teste['resid_valid'][k]<=-nivel02 and pos_compra==1:
            #     base_teste['compra02'][k]=-base_teste['close'][k]*0.2*prop_win-base_teste['closewdo'][k]*prop_wdo*10
            #     pos_compra=2
            
            # if base_teste['resid_valid'][k]>=-gain02 and pos_compra==2:
            #     base_teste['lucro_fin'][k]=((base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10)+base_teste['compra02'][k-1])
            #     pos_compra=1
       
            # if base_teste['resid_valid'][k]<=-loss02 and pos_compra==2:
            #     base_teste['lucro_fin'][k]=((base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10)+base_teste['compra02'][k-1])
            #     pos_compra=1 
       
            # ################################################################# 
         
            # if base_teste['resid_valid'][k]<=-nivel03 and pos_compra==2:
            #     base_teste['compra03'][k]=-base_teste['close'][k]*0.2*prop_win-base_teste['closewdo'][k]*prop_wdo*10
            #     pos_compra=3
             
            # if base_teste['resid_valid'][k]>=-gain03 and pos_compra==3:
            #     base_teste['lucro_fin'][k]=((base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10)+base_teste['compra03'][k-1])
            #     pos_compra=2

            # if base_teste['resid_valid'][k]<=-loss03 and pos_compra==3:
            #     base_teste['lucro_fin'][k]=((base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10)+base_teste['compra03'][k-1])
            #     pos_compra=2    
            # #################################################################
            
            if base_teste['resid_valid'][k]>=nivel01 and pos_venda==0:
                base_teste['venda01'][k]=base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10
                pos_venda=1
            
            if base_teste['resid_valid'][k]<=gain01 and pos_venda==1:
                base_teste['lucro_fin'][k]=(base_teste['venda01'][k-1])-(base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10)
                pos_venda=22

            if base_teste['resid_valid'][k]>=loss01 and pos_venda==1:
                base_teste['lucro_fin'][k]=(base_teste['venda01'][k-1])-(base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10)
                pos_venda=22    
           #################################################################
    
    #         if base_teste['resid_valid'][k]>=nivel02 and pos_venda==1:
    #             base_teste['venda02'][k]=base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10
    #             pos_venda=2
                
    #         if base_teste['resid_valid'][k]<=gain02 and pos_venda==2:
    #             base_teste['lucro_fin'][k]=(base_teste['venda02'][k-1])-(base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10)
    #             pos_venda=1
               
    #         if  base_teste['resid_valid'][k] >=loss02 and pos_venda==2:
    #             base_teste['lucro_fin'][k]=(base_teste['venda02'][k-1])-(base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10)
    #             pos_venda=1
    # #                base_teste['result_fin'][k]=(base_teste['close'][k]*0.4*(pos_compra+pos_venda)+base_teste['closewdo'][k]*0.4*(pos_compra+pos_venda))
    
    #        #################################################################
      
    #         if base_teste['resid_valid'][k]>=nivel03 and pos_venda==2:
    #             base_teste['venda03'][k]=base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10
    #             pos_venda=3
            
    #         if base_teste['resid_valid'][k]<=gain03 and pos_venda==3:
    #             base_teste['lucro_fin'][k]=(base_teste['venda03'][k-1])-(base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10)
    #             pos_venda=2

    #         if base_teste['resid_valid'][k] >=loss03 and pos_venda==3:
    #             base_teste['lucro_fin'][k]=(base_teste['venda03'][k-1])-(base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10)
    #             pos_venda=2

    # #           base_teste['result_fin'][k]=(base_teste['close'][k]*0.4*(pos_compra+pos_venda)+base_teste['closewdo'][k]*0.4*(pos_compra+pos_venda))
               
    
            if base_teste['compra01'][k-1]!=0 and pos_compra>=1:
                base_teste['compra01'][k]=base_teste['compra01'][k-1]
            if base_teste['compra02'][k-1]!=0 and pos_compra>=2:
                base_teste['compra02'][k]=base_teste['compra02'][k-1]
            if base_teste['compra03'][k-1]!=0 and pos_compra==3:
                base_teste['compra03'][k]=base_teste['compra03'][k-1]
            if base_teste['venda01'][k-1]!=0 and pos_venda>=1:
                base_teste['venda01'][k]=base_teste['venda01'][k-1]
            if base_teste['venda02'][k-1]!=0 and pos_venda>=2:
                base_teste['venda02'][k]=base_teste['venda02'][k-1]
            if base_teste['venda03'][k-1]!=0 and pos_venda==3:
                base_teste['venda03'][k]=base_teste['venda03'][k-1] 
    
            
            base_teste['resultado'][k]=(base_teste['compra01'][k]+base_teste['compra02'][k]+base_teste['compra03'][k]+base_teste['venda01'][k]+base_teste['venda02'][k]+base_teste['venda03'][k])
            
            if pos_venda==1:
                base_teste['result_fin'][k]=base_teste['resultado'][k]-(base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10)
    
            # if pos_venda==2:
            #     base_teste['result_fin'][k]=base_teste['resultado'][k]-(base_teste['close'][k]*0.2*2*prop_win+base_teste['closewdo'][k]*prop_wdo*10*2)
    
            # if pos_venda==3:
            #     base_teste['result_fin'][k]=base_teste['resultado'][k]-(base_teste['close'][k]*0.2*3*prop_win+base_teste['closewdo'][k]*prop_wdo*10*3)
    
            if pos_compra==1:
                base_teste['result_fin'][k]=base_teste['resultado'][k]+(base_teste['close'][k]*0.2*prop_win+base_teste['closewdo'][k]*prop_wdo*10)
    
            # if pos_compra==2:
            #     base_teste['result_fin'][k]=base_teste['resultado'][k]+(base_teste['close'][k]*0.2*2*prop_win+base_teste['closewdo'][k]*prop_wdo*10*2)
    
            # if pos_compra==3:
            #     base_teste['result_fin'][k]=base_teste['resultado'][k]+(base_teste['close'][k]*0.2*3*prop_win+base_teste['closewdo'][k]*prop_wdo*10*3)
    
        
        if base_teste['result_fin'].sum()!=0:
            resultado.append(base_teste['lucro_fin'].sum()+base_teste['result_fin'][k])
        else:
            resultado.append(base_teste['lucro_fin'].sum())
        base_teste.to_excel('base_teste_'+str(data_final[0])+'.xlsx')       
        
        return (resultado)

resultado = pair_trading(date_from, time_frame, candles, nivel01, nivel02, nivel03, gain01, gain02, gain03)

result = pd.DataFrame(resultado) 
result.sum()
