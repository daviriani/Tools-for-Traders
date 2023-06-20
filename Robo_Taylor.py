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


# In[1]. Rodar a regressão dos últimos 100 pregões e coletar o beta e desvio-padrão (coeficiente angular)

def coeficiente(date_from, time_frame, dias):
    
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
    
    #Estimando a regressão WIN x WDO Geral (De todo o período)
    Y=base2['lnwin'].values
    X=base2['lnwdo'].values
    modelo = sm.OLS(Y, sm.add_constant(X)).fit()
    print(modelo.summary())
    coef = modelo.params[1]
    
    # Cálculo dos resíduos
    modelo_residuos = modelo.resid # Residuos do modelo WIN x WDO
    
    #Criação do Intervalo dos Resíduos
    int_sup = modelo_residuos.mean()+1*modelo_residuos.std()
    int_inf = modelo_residuos.mean()-1*modelo_residuos.std()        
    
    win_fech=base2['closedaywin'][len(base2)-1]
    wdo_fech=base2['closedaywdo'][len(base2)-1]
    
    
    return (coef, int_sup, win_fech, wdo_fech)
    
# In[2]. Coletar em tempo real as cotações de WIN e WDO e calcular o resíduo instantâneo

coef, desv_pad, win_fech, wdo_fech = coeficiente(date_from, time_frame, dias)

pos_trade=3
nivel_01=1.2
nivel_02=1.5
nivel_03=1.8
gain_02=1.3
gain_03=1.6
    





while True:
    mt5.initialize()
    rt_win = mt5.copy_rates_from(ticker_atual_win,mt5.TIMEFRAME_M1, date_from,1)
    rt_win = pd.DataFrame(rt_win)
    rt_win['time']=pd.to_datetime(rt_win['time'], unit='s')
    print ("O valor do close_win é:", rt_win['close'].iloc[-1])
    
    rt_wdo = mt5.copy_rates_from(ticker_atual_wdo,mt5.TIMEFRAME_M1, date_from,1)
    rt_wdo = pd.DataFrame(rt_wdo)
    rt_wdo['time']=pd.to_datetime(rt_wdo['time'], unit='s')
    print ("O valor do close_wdo é:", rt_wdo['close'].iloc[-1])
    
    ln_win = np.log(rt_win['close'].iloc[-1]/win_fech)
    ln_wdo = np.log(rt_wdo['close'].iloc[-1]/wdo_fech)
    
    res_inst = (ln_win-(ln_wdo*coef))/np.abs(desv_pad)
    print ("O valor do resíduo instantâneo é:", res_inst, "desvios")
    print (mt5.terminal_info())
    
    time.sleep(4) 
    
    
### ORDENS DE COMPRA #############################################

    
    if (pos_trade == 0 and res_inst <= -nivel_01):
         
        # prepare the buy request structure
        symbol = ticker_atual_win
        symbol_info = mt5.symbol_info(symbol)
         
        lot = 2.0
        point = mt5.symbol_info(symbol).point
        price = mt5.symbol_info_tick(symbol).ask
        deviation = 20
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY,
            "price": price,
            "sl": price - 2800 * point,
            "tp": price + 2800 * point,
            "deviation": deviation,
            "magic": 234000,
            "comment": "Abert_Compra_01",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
         
        # send a trading request
        result = mt5.order_send(request)
        # check the execution result
        print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
        print("2. Ordem enviada com sucesso, ", result)
        print("Posição Aberta: POSITION_TICKET={}".format(result.order))
        
        pos_ordem_win_1=result.order
        
        #Ordem do WDO: #############################################################################

         
        lot = 1.0
        symbol = ticker_atual_wdo
        point = mt5.symbol_info(symbol).point
        price = mt5.symbol_info_tick(symbol).ask
        deviation = 20
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY,
            "price": price,
            "sl": price - 80,
            "tp": price + 80,
            "deviation": deviation,
            "magic": 234000,
            "comment": "Abert_Compra_01",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
         
        # send a trading request
        result = mt5.order_send(request)
        # check the execution result
        print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
        print("2. Ordem enviada com sucesso, ", result)
        print("Posição Aberta: POSITION_TICKET={}".format(result.order))

        pos_trade = 1
        pos_ordem_wdo_1 = result.order
        
        
    if (pos_trade == 1 and mt5.positions_get(symbol=ticker_atual_win)[0][5] == 0 and res_inst <= -nivel_02):
        ## Abrir segunda ordem de compra (2 WIN e 1 WDO)
        
    
        # prepare the buy request structure
        symbol = ticker_atual_win
        symbol_info = mt5.symbol_info(symbol)
         
        lot = 2.0
        point = mt5.symbol_info(symbol).point
        price = mt5.symbol_info_tick(symbol).ask
        deviation = 20
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY,
            "price": price,
            "sl": price - 2800 * point,
            "tp": price + 2800 * point,
            "deviation": deviation,
            "magic": 234000,
            "comment": "Abert_Compra_02",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
         
        # send a trading request
        result = mt5.order_send(request)
        # check the execution result
        print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
        print("2. Ordem enviada com sucesso, ", result)
        print("Posição Aberta: POSITION_TICKET={}".format(result.order))
        
        pos_ordem_win_2=result.order
        
        #Ordem do WDO: #############################################################################
 
         
        lot = 1.0
        symbol = ticker_atual_wdo
        point = mt5.symbol_info(symbol).point
        price = mt5.symbol_info_tick(symbol).ask
        deviation = 20
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY,
            "price": price,
            "sl": price - 80,
            "tp": price + 80,
            "deviation": deviation,
            "magic": 234000,
            "comment": "Abert_Compra_02",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
         
        # send a trading request
        result = mt5.order_send(request)
        # check the execution result
        print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
        print("2. Ordem enviada com sucesso, ", result)
        print("Posição Aberta: POSITION_TICKET={}".format(result.order))
    

        pos_ordem_wdo_2 = result.order
        
        pos_trade = 2
        
      
    if (pos_trade == 2):
        
        if (mt5.positions_get(symbol=ticker_atual_win)[0][5] == 0 and res_inst >= -gain_02):
            symbol = ticker_atual_win
            point = mt5.symbol_info(symbol).point
            price = mt5.symbol_info_tick(symbol).ask
            deviation = 20
          
            request={
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": ticker_atual_win,
                "volume": 2.0,
                "type": mt5.ORDER_TYPE_SELL,
                "position": pos_ordem_win_2,
                "price": price,
                "sl": price - 2800 * point,
                "tp": price + 2800 * point,
                "deviation": deviation,
                "magic": 234000,
                "comment": "Fech_Compra_02",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
                }
            # send a trading request
            result=mt5.order_send(request)
         
            symbol = ticker_atual_wdo
            point = mt5.symbol_info(symbol).point
            price = mt5.symbol_info_tick(symbol).ask
            deviation = 20
            request={
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": ticker_atual_wdo,
                "volume": 1.0,
                "type": mt5.ORDER_TYPE_SELL,
                "position": pos_ordem_wdo_2,
                "price": price,
                "sl": price - 80,
                "tp": price + 80,
                "deviation": deviation,
                "magic": 234000,
                "comment": "Fech_Compra_02",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
                }
            # send a trading request
            result=mt5.order_send(request)
         
            # check the execution result
            print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
            print("2. Ordem enviada com sucesso, ", result)
            print("Posição Encerrada: POSITION_TICKET={}".format(result.order))  
            pos_trade=1

       
        elif (pos_trade == 2 and res_inst <= -nivel_03):
            ## Abrir terceira ordem de compra (2 WIN e 1 WDO)
            
            #Ordem do WIN: #############################################################################
            # establish connection to the MetaTrader 5 terminal
            if not mt5.initialize():
                print("initialize() failed, error code =",mt5.last_error())
                quit()
             
            # prepare the buy request structure
            symbol = ticker_atual_win
            symbol_info = mt5.symbol_info(symbol)
             
            lot = 2.0
            point = mt5.symbol_info(symbol).point
            price = mt5.symbol_info_tick(symbol).ask
            deviation = 20
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": mt5.ORDER_TYPE_BUY,
                "price": price,
                "sl": price - 2800 * point,
                "tp": price + 2800 * point,
                "deviation": deviation,
                "magic": 234000,
                "comment": "Abert_Compra_03",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
             
            # send a trading request
            result = mt5.order_send(request)
            # check the execution result
            print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
            print("2. Ordem enviada com sucesso, ", result)
            print("Posição Aberta: POSITION_TICKET={}".format(result.order))
            
            pos_ordem_win_3=result.order
            
            #Ordem do WDO: #############################################################################
            # establish connection to the MetaTrader 5 terminal
            if not mt5.initialize():
                print("initialize() failed, error code =",mt5.last_error())
                quit()
             
            lot = 1.0
            symbol = ticker_atual_wdo
            point = mt5.symbol_info(symbol).point
            price = mt5.symbol_info_tick(symbol).ask
            deviation = 20
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": mt5.ORDER_TYPE_BUY,
                "price": price,
                "sl": price - 80,
                "tp": price + 80,
                "deviation": deviation,
                "magic": 234000,
                "comment": "Abert_Compra_03",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
             
            # send a trading request
            result = mt5.order_send(request)
            # check the execution result
            print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
            print("2. Ordem enviada com sucesso, ", result)
            print("Posição Aberta: POSITION_TICKET={}".format(result.order))
        
    
            pos_ordem_wdo_3 = result.order
            
            pos_trade=3
            
            
            
    if (pos_trade == 3):
        if (mt5.positions_get(symbol=ticker_atual_win)[0][5] == 0 and res_inst >= -gain_03):
              symbol = ticker_atual_win
              point = mt5.symbol_info(symbol).point
              price = mt5.symbol_info_tick(symbol).ask
              deviation = 20
              request={
                  "action": mt5.TRADE_ACTION_DEAL,
                  "symbol": ticker_atual_win,
                  "volume": 2.0,
                  "type": mt5.ORDER_TYPE_SELL,
                  "position": pos_ordem_win_3,
                  "price": price,
                  "deviation": deviation,
                  "magic": 234000,
                  "comment": "Fech_Compra_03",
                  "type_time": mt5.ORDER_TIME_GTC,
                  "type_filling": mt5.ORDER_FILLING_RETURN,
              }
              # send a trading request
              result=mt5.order_send(request)
              
              symbol = ticker_atual_wdo
              point = mt5.symbol_info(symbol).point
              price = mt5.symbol_info_tick(symbol).ask
              deviation = 20
              request={
                  "action": mt5.TRADE_ACTION_DEAL,
                  "symbol": ticker_atual_wdo,
                  "volume": 1.0,
                  "type": mt5.ORDER_TYPE_SELL,
                  "position": pos_ordem_wdo_3,
                  "price": price,
                  "deviation": deviation,
                  "magic": 234000,
                  "comment": "Fech_Compra_03",
                  "type_time": mt5.ORDER_TIME_GTC,
                  "type_filling": mt5.ORDER_FILLING_RETURN,
              }
              # send a trading request
              result=mt5.order_send(request)
              
              # check the execution result
              print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
              print("2. Ordem enviada com sucesso, ", result)
              print("Posição Encerrada: POSITION_TICKET={}".format(result.order))  
              pos_trade=2

          
      
###### ORDENS DE VENDA ################


    if (pos_trade == 0 and res_inst >= nivel_01):
          ## Abrir ordem de venda (2 WIN e 1 WDO)
          
          #Ordem do WIN: #############################################################################
          # establish connection to the MetaTrader 5 terminal
          if not mt5.initialize():
              print("initialize() failed, error code =",mt5.last_error())
              quit()
           
          # prepare the buy request structure
          symbol = ticker_atual_win
          symbol_info = mt5.symbol_info(symbol)
           
          lot = 2.0
          point = mt5.symbol_info(symbol).point
          price = mt5.symbol_info_tick(symbol).ask
          deviation = 20
          request = {
              "action": mt5.TRADE_ACTION_DEAL,
              "symbol": symbol,
              "volume": lot,
              "type": mt5.ORDER_TYPE_SELL,
              "price": price,
              "sl": price + 2800 * point,
              "tp": price - 2800 * point,
              "deviation": deviation,
              "magic": 234000,
              "comment": "Abert_Venda_01",
              "type_time": mt5.ORDER_TIME_GTC,
              "type_filling": mt5.ORDER_FILLING_FOK,
          }
           
          # send a trading request
          result = mt5.order_send(request)
          # check the execution result
          print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
          print("2. Ordem enviada com sucesso, ", result)
          print("Posição Aberta: POSITION_TICKET={}".format(result.order))
          
          pos_ordem_win_1=result.order
          
          #Ordem do WDO: #############################################################################
          # establish connection to the MetaTrader 5 terminal
          if not mt5.initialize():
              print("initialize() failed, error code =",mt5.last_error())
              quit()
           
          lot = 1.0
          symbol = ticker_atual_wdo
          point = mt5.symbol_info(symbol).point
          price = mt5.symbol_info_tick(symbol).ask
          deviation = 20
          request = {
              "action": mt5.TRADE_ACTION_DEAL,
              "symbol": symbol,
              "volume": lot,
              "type": mt5.ORDER_TYPE_SELL,
              "price": price,
              "sl": price + 80,
              "tp": price - 80,
              "deviation": deviation,
              "magic": 234000,
              "comment": "Abert_Venda_01",
              "type_time": mt5.ORDER_TIME_GTC,
              "type_filling": mt5.ORDER_FILLING_FOK,
          }
           
          # send a trading request
          result = mt5.order_send(request)
          # check the execution result
          print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
          print("2. Ordem enviada com sucesso, ", result)
          print("Posição Aberta: POSITION_TICKET={}".format(result.order))
    
          pos_trade = 1
          pos_ordem_wdo_1 = result.order
          
      
      
    if (pos_trade == 1 and mt5.positions_get(symbol=ticker_atual_win)[0][5] == 1 and res_inst >= nivel_02):
          ## Abrir segunda ordem de venda (2 WIN e 1 WDO)
          
          #Ordem do WIN: #############################################################################
          # establish connection to the MetaTrader 5 terminal
          if not mt5.initialize():
              print("initialize() failed, error code =",mt5.last_error())
              quit()
           
          # prepare the buy request structure
          symbol = ticker_atual_win
          symbol_info = mt5.symbol_info(symbol)
           
          lot = 2.0
          point = mt5.symbol_info(symbol).point
          price = mt5.symbol_info_tick(symbol).ask
          deviation = 20
          request = {
              "action": mt5.TRADE_ACTION_DEAL,
              "symbol": symbol,
              "volume": lot,
              "type": mt5.ORDER_TYPE_SELL,
              "price": price,
              "sl": price + 2800 * point,
              "tp": price - 2800 * point,
              "deviation": deviation,
              "magic": 234000,
              "comment": "Abert_Venda_02",
              "type_time": mt5.ORDER_TIME_GTC,
              "type_filling": mt5.ORDER_FILLING_FOK,
          }
           
          # send a trading request
          result = mt5.order_send(request)
          # check the execution result
          print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
          print("2. Ordem enviada com sucesso, ", result)
          print("Posição Aberta: POSITION_TICKET={}".format(result.order))
          
          pos_ordem_win_2=result.order
          
          #Ordem do WDO: #############################################################################
          # establish connection to the MetaTrader 5 terminal
          if not mt5.initialize():
              print("initialize() failed, error code =",mt5.last_error())
              quit()
           
          lot = 1.0
          symbol = ticker_atual_wdo
          point = mt5.symbol_info(symbol).point
          price = mt5.symbol_info_tick(symbol).ask
          deviation = 20
          request = {
              "action": mt5.TRADE_ACTION_DEAL,
              "symbol": symbol,
              "volume": lot,
              "type": mt5.ORDER_TYPE_SELL,
              "price": price,
              "sl": price + 80,
              "tp": price - 80,
              "deviation": deviation,
              "magic": 234000,
              "comment": "Abert_Venda_02",
              "type_time": mt5.ORDER_TIME_GTC,
              "type_filling": mt5.ORDER_FILLING_FOK,
          }
           
          # send a trading request
          result = mt5.order_send(request)
          # check the execution result
          print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
          print("2. Ordem enviada com sucesso, ", result)
          print("Posição Aberta: POSITION_TICKET={}".format(result.order))
      
    
          pos_ordem_wdo_2 = result.order
          
          pos_trade = 2


    if (pos_trade == 2):
        if (mt5.positions_get(symbol=ticker_atual_win)[0][5] == 1 and res_inst <= gain_02):
             symbol = ticker_atual_win
             point = mt5.symbol_info(symbol).point
             price = mt5.symbol_info_tick(symbol).ask
             deviation = 20
              
             request={
                 "action": mt5.TRADE_ACTION_DEAL,
                 "symbol": ticker_atual_win,
                 "volume": 2.0,
                 "type": mt5.ORDER_TYPE_BUY,
                 "position": pos_ordem_win_2,
                 "price": price,
                 "deviation": deviation,
                 "magic": 234000,
                 "comment": "Fech_Venda_02",
                 "type_time": mt5.ORDER_TIME_GTC,
                 "type_filling": mt5.ORDER_FILLING_RETURN,
             }
             # send a trading request
             result=mt5.order_send(request)
             
             symbol = ticker_atual_wdo
             point = mt5.symbol_info(symbol).point
             price = mt5.symbol_info_tick(symbol).ask
             deviation = 20
             request={
                 "action": mt5.TRADE_ACTION_DEAL,
                 "symbol": ticker_atual_wdo,
                 "volume": 1.0,
                 "type": mt5.ORDER_TYPE_BUY,
                 "position": pos_ordem_wdo_2,
                 "price": price,
                 "deviation": deviation,
                 "magic": 234000,
                 "comment": "Fech_Venda_02",
                 "type_time": mt5.ORDER_TIME_GTC,
                 "type_filling": mt5.ORDER_FILLING_RETURN,
             }
             # send a trading request
             result=mt5.order_send(request)
             
             # check the execution result
            # check the execution result
             print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
             print("2. Ordem enviada com sucesso, ", result)
             print("Posição Encerrada: POSITION_TICKET={}".format(result.order))  
             pos_trade=1

               
        elif (pos_trade == 2 and res_inst >= nivel_03):
                  ## Abrir segunda ordem de compra (2 WIN e 1 WDO)
                  
                  #Ordem do WIN: #############################################################################
                  # establish connection to the MetaTrader 5 terminal
                  if not mt5.initialize():
                      print("initialize() failed, error code =",mt5.last_error())
                      quit()
                   
                  # prepare the buy request structure
                  symbol = ticker_atual_win
                  symbol_info = mt5.symbol_info(symbol)
                   
                  lot = 2.0
                  point = mt5.symbol_info(symbol).point
                  price = mt5.symbol_info_tick(symbol).ask
                  deviation = 20
                  request = {
                      "action": mt5.TRADE_ACTION_DEAL,
                      "symbol": symbol,
                      "volume": lot,
                      "type": mt5.ORDER_TYPE_SELL,
                      "price": price,
                      "sl": price + 2800 * point,
                      "tp": price - 2800 * point,
                      "deviation": deviation,
                      "magic": 234000,
                      "comment": "Abert_Venda_03",
                      "type_time": mt5.ORDER_TIME_GTC,
                      "type_filling": mt5.ORDER_FILLING_FOK,
                  }
                   
                  # send a trading request
                  result = mt5.order_send(request)
                  # check the execution result
                  print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
                  print("2. Ordem enviada com sucesso, ", result)
                  print("Posição Aberta: POSITION_TICKET={}".format(result.order))
                  
                  pos_ordem_win_3=result.order
                  
                  #Ordem do WDO: #############################################################################
                  # establish connection to the MetaTrader 5 terminal
                  if not mt5.initialize():
                      print("initialize() failed, error code =",mt5.last_error())
                      quit()
                   
                  lot = 1.0
                  symbol = ticker_atual_wdo
                  point = mt5.symbol_info(symbol).point
                  price = mt5.symbol_info_tick(symbol).ask
                  deviation = 20
                  request = {
                      "action": mt5.TRADE_ACTION_DEAL,
                      "symbol": symbol,
                      "volume": lot,
                      "type": mt5.ORDER_TYPE_SELL,
                      "price": price,
                      "sl": price + 80,
                      "tp": price - 80,
                      "deviation": deviation,
                      "magic": 234000,
                      "comment": "Abert_Venda_03",
                      "type_time": mt5.ORDER_TIME_GTC,
                      "type_filling": mt5.ORDER_FILLING_FOK,
                  }
                   
                  # send a trading request
                  result = mt5.order_send(request)
                  # check the execution result
                  print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
                  print("2. Ordem enviada com sucesso, ", result)
                  print("Posição Aberta: POSITION_TICKET={}".format(result.order))
              
            
                  pos_ordem_wdo_3 = result.order
                  
                  pos_trade = 3

    if (pos_trade == 3):
        if (mt5.positions_get(symbol=ticker_atual_win)[0][5] == 1 and res_inst <= gain_03):
            symbol = ticker_atual_win
            point = mt5.symbol_info(symbol).point
            price = mt5.symbol_info_tick(symbol).ask
            deviation = 20
            request={
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": ticker_atual_win,
            "volume": 2.0,
            "type": mt5.ORDER_TYPE_BUY,
            "position": pos_ordem_win_3,
            "price": price,
            "deviation": deviation,
            "magic": 234000,
            "comment": "Fech_Venda_03",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
            }
            # send a trading request
            result=mt5.order_send(request)
            
            symbol = ticker_atual_wdo
            point = mt5.symbol_info(symbol).point
            price = mt5.symbol_info_tick(symbol).ask
            deviation = 20
            request={
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": ticker_atual_wdo,
                "volume": 1.0,
                "type": mt5.ORDER_TYPE_BUY,
                "position": pos_ordem_wdo_3,
                "price": price,
                "deviation": deviation,
                "magic": 234000,
                "comment": "Fech_Venda_03",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }
            # send a trading request
            result=mt5.order_send(request)
            
            # check the execution result
            print("1. Ordem enviada(): com {} {} lotes {} com desvio de ={} points".format(symbol,lot,price,deviation));
            print("2. Ordem enviada com sucesso, ", result)
            print("Posição Encerrada: POSITION_TICKET={}".format(result.order))  
            pos_trade=2

    

mt5.shutdown()

    
#O que falta para colocar pra rodar?

#Ler posição atual antes de ligar
#As cotações estão travando.... tentar outra fonte de dados
#Colocar horário de funcionamento (início e término)??
#Garantir pelo menos pagar a corretagem no trade?
#Travar as posições máximas (contra bugs)
#Estender o backtest para 10 anos
#Testar as redes neurais







