# -*- coding: utf-8 -*-
"""
Created on Fri Dec  4 17:56:52 2020

@author: davir
"""

from pandas_datareader import data as pdr
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve, classification_report,accuracy_score, confusion_matrix, auc
from statsmodels.tsa.stattools import adfuller as adf
from statsmodels.graphics.tsaplots import plot_acf,plot_pacf
from arch import arch_model
from statsmodels.stats.diagnostic import acorr_ljungbox
from datetime import datetime,timedelta
import investpy


def volat(OpenD0, data):
    #Verificando se os retornos são não-estacionários:    
    returns = np.log(data['Close']/data['Open'])
    p_value = adf(returns)[1]
#    print("O p-valor foi:",p_value,".O Teste de Dicky Fuller menor que 0.05 significa que rejeitamos a hipótese nula que os retornos são não-estacionários.")

#    fig = plot_pacf(returns**2, lags = 20, zero = False)
    model2 = arch_model(returns, p = 1, q = 1, dist = 't').fit(disp='off')
    model2.summary()
    
    
    rolling = []
    window = 200
    for i in range(window):
        train_data = returns[:-(window-i)]
        model = arch_model(train_data, p = 2, q = 2).fit(disp='off')
        pred = model.forecast(horizon = 1)
        rolling.append(np.sqrt(pred.variance.values)[-1,:][0])
    rolling = pd.Series(rolling , index = returns.index[-window:])
#    plt.plot(returns[-window:])
#    plt.plot(rolling)
#    plt.legend(['Returns','Volatility'])
#    plt.title('Rolling Window Forecast')



    std_resid = model.resid/model.conditional_volatility
#    fig, ax = plt.subplots(nrows = 2, ncols = 0)
#    ax[0] = plt.plot(std_resid, color = 'r')
#    plt.title('Standardised Residuals')
#    ax[1] = plot_acf(std_resid, lags = 20)
#    plt.savefig('test5.png', bbox_inches='tight')
        
    
    lb_test = acorr_ljungbox(std_resid, lags = 20)
    #lb_test[1]
    
    
    
    future_index = pd.date_range(start = (data.index[-1]+timedelta(1)).strftime("%Y-%m-%d"), periods = 1, freq = 'D')
    predict = model.forecast(horizon = 1)
    pred_vol = np.sqrt(predict.variance.values[-1:][0])
    pred_vol = pd.Series(pred_vol,index = future_index)
#    plt.plot(pred_vol, marker = 'o', markerfacecolor = 'r', linestyle = '--', markeredgecolor = 'k', markersize = 6)
#    plt.title("Next seven day volatility forecast")
#    plt.grid(True)
#    plt.savefig('test6.png', bbox_inches='tight')
    
    return [OpenD0*(1-pred_vol[0]),OpenD0*(1+pred_vol[0])]




cod_empresa='PETR4'
today = datetime.today()
end2= today.strftime("%d/%m/%Y")
data01 = investpy.get_stock_historical_data(stock=cod_empresa, country='Brazil', from_date='01/01/2020', to_date=end2)
volatil_result = pd.DataFrame(index=data01.index.strftime("%Y-%m-%d"), columns=['OpenD0','MinReal','MaxReal','MinProj','MaxProj','Acertou'])
index_inic= 1473
volatil_result = volatil_result[0:index_inic]

for k in volatil_result.index:
    volatil_result['OpenD0'][k]=data01['Open'][k]
    index_inic=index_inic+1
    end = datetime.strptime(k, '%Y-%m-%d')
    end = end.strftime("%d/%m/%Y")
    data = data01[:index_inic]

    #Fill the NA values
    data=data[:-1]
    data = data.dropna()
    
    v_min, v_max = volat(volatil_result['OpenD0'][k], data)
    volatil_result['MinReal'][k]=data01['Low'][k]
    volatil_result['MaxReal'][k]=data01['High'][k]
    volatil_result['MinProj'][k]=v_min
    volatil_result['MaxProj'][k]=v_max
    print (k)
    
    

# diretorio = './'
# resumo = pd.ExcelWriter(diretorio+cod_empresa+'resumo.xlsx')
# volatil_result.to_excel(resumo, 'Resumo')
# resumo.save()
