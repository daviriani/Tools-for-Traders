# -*- coding: utf-8 -*-
"""
Created on Mon Nov 29 20:31:06 2021

@author: davir
"""

#Long e Short com ações - IBOVESPA

import numpy as np
import pandas as pd
import statsmodels
import statsmodels.api as sm
import datetime
from statsmodels.tsa.stattools import coint, adfuller
import pandas_datareader as pdr

import matplotlib.pyplot as plt
import seaborn as sns; sns.set(style="whitegrid")


def generate_data(params):
    mu = params[0]
    sigma = params[1]
    return np.random.normal(mu, sigma)

# Set the parameters and the number of datapoints
params = (0, 1)
T = 100

A = pd.Series(index=range(T))
A.name = 'A'

for t in range(T):
    A[t] = generate_data(params)

T = 100

B = pd.Series(index=range(T))
B.name = 'B'

for t in range(T):
    # Now the parameters are dependent on time
    # Specifically, the mean of the series changes over time
    params = (t * 0.1, 1)
    B[t] = generate_data(params)
    
fig, (ax1, ax2) = plt.subplots(nrows =1, ncols =2, figsize=(16,6))

ax1.plot(A)
ax2.plot(B)
ax1.legend(['Series A'])
ax2.legend(['Series B'])
ax1.set_title('Stationary')
ax2.set_title('Non-Stationary')


mean = np.mean(B)

plt.figure(figsize=(12,6))
plt.plot(B)
plt.hlines(mean, 0, len(B), linestyles='dashed', colors = 'r')
plt.xlabel('Time')
plt.xlim([0, 99])
plt.ylabel('Value')
plt.legend(['Series B', 'Mean'])


# In[004] ## Teste de Estacionariedade ## 


def stationarity_test(X, cutoff=0.01):
    # H_0 in adfuller is unit root exists (non-stationary)
    # We must observe significant p-value to convince ourselves that the series is stationary
    pvalue = adfuller(X)[1]
    if pvalue < cutoff:
        print('p-value = ' + str(pvalue) + ' The series ' + X.name +' is likely stationary.')
    else:
        print('p-value = ' + str(pvalue) + ' The series ' + X.name +' is likely non-stationary.')
        

stationarity_test(A)
stationarity_test(B)


# In[004] ## Coletando os dados ## 

# Generate daily returns

Xreturns = np.random.normal(0, 1, 100)

# sum up and shift the prices up

X = pd.Series(np.cumsum(
    Xreturns), name='X') + 50
X.plot(figsize=(15,7))

noise = np.random.normal(0, 1, 100)
Y = X + 5 + noise
Y.name = 'Y'

pd.concat([X, Y], axis=1).plot(figsize=(15, 7))

plt.show()


# In[004] ## Plotando o gráfico das diferenças ## 


plt.figure(figsize=(12,6))
(Y - X).plot() # Plot the spread
plt.axhline((Y - X).mean(), color='red', linestyle='--') # Add the mean
plt.xlabel('Time')
plt.xlim(0,99)
plt.legend(['Price Spread', 'Mean']);


# In[004] ## Fazendo a cointegração ##

score, pvalue, _ = coint(X,Y)
print(pvalue)



# In[004] ## Procurando pares cointegrados ##

def find_cointegrated_pairs(data):
    n = data.shape[1]
    score_matrix = np.zeros((n, n))
    pvalue_matrix = np.ones((n, n))
    keys = data.keys()
    pairs = []
    for i in range(n):
        for j in range(i+1, n):
            S1 = data[keys[i]]
            S2 = data[keys[j]]
            result = coint(S1, S2)
            score = result[0]
            pvalue = result[1]
            score_matrix[i, j] = score
            pvalue_matrix[i, j] = pvalue
            if pvalue < 0.05:
                pairs.append((keys[i], keys[j]))
    return score_matrix, pvalue_matrix, pairs




start = datetime.datetime(2020, 1, 1)
end = datetime.datetime(2022, 1, 1)

tickers = ['VALE3.SA','PETR4.SA','ITUB4.SA','PETR3.SA','BBDC4.SA','B3SA3.SA','ABEV3.SA','BBAS3.SA','ELET3.SA','RENT3.SA','ITSA4.SA','WEGE3.SA','JBSS3.SA','SUZB3.SA','BPAC11.SA','HAPV3.SA','EQTL3.SA','GGBR4.SA','LREN3.SA','RDOR3.SA','BBDC3.SA','RADL3.SA','CSAN3.SA','RAIL3.SA','ENEV3.SA','PRIO3.SA','VBBR3.SA','BBSE3.SA','CMIG4.SA','VIVT3.SA','BRFS3.SA','HYPE3.SA','KLBN11.SA','SBSP3.SA','TOTS3.SA','CCRO3.SA','UGPA3.SA','ASAI3.SA','NTCO3.SA','MGLU3.SA','ELET6.SA','CPLE6.SA','AMER3.SA','ENGI11.SA','SANB11.SA','EGIE3.SA','CSNA3.SA','EMBR3.SA','TIMS3.SA','TAEE11.SA','BRKM5.SA','CRFB3.SA','RRRP3.SA','BRML3.SA','GOAU4.SA','SULA11.SA','MULT3.SA','CPFE3.SA','CIEL3.SA','SOMA3.SA','BRAP4.SA','AZUL4.SA','ENBR3.SA','VIIA3.SA','MRFG3.SA','USIM5.SA','FLRY3.SA','COGN3.SA','CMIN3.SA','SLCE3.SA','LWSA3.SA','CYRE3.SA','BEEF3.SA','ALPA4.SA','YDUQ3.SA','IGTI11.SA','PETZ3.SA','DXCO3.SA','PCAR3.SA','MRVE3.SA','QUAL3.SA','IRBR3.SA','BPAN4.SA','ECOR3.SA','CVCB3.SA','JHSF3.SA','EZTC3.SA','GOLL4.SA','POSI3.SA','CASH3.SA',
]


df = pdr.get_data_yahoo(tickers, start, end)['Close']
df = df.fillna(0)
df.tail()


# Heatmap to show the p-values of the cointegration test between each pair of
# stocks. Only show the value in the upper-diagonal of the heatmap
scores, pvalues, pairs = find_cointegrated_pairs(df)
import seaborn
fig, ax = plt.subplots(figsize=(10,10))
plt.tick_params(axis='both', which='major', labelsize=8)
seaborn.heatmap(pvalues, xticklabels=tickers, yticklabels=tickers, cmap='RdYlGn_r' 
                , mask = (pvalues >= 0.05)
                )
print(pairs)



# In[004] ## Spread entre 02 ativos ##

S1 = df['QUAL3.SA']
S2 = df['EZTC3.SA']

score, pvalue, _ = coint(S1, S2)
pvalue

S1 = sm.add_constant(S1)
results = sm.OLS(S2, S1).fit()
S1 = S1['QUAL3.SA']
b = results.params['QUAL3.SA']

spread = S2 - b * S1
spread.plot(figsize=(12,6))
plt.axhline(spread.mean(), color='black')
plt.xlim('2020-01-01', '2022-01-01')
plt.legend(['Spread']);


# In[005] ## Ratio entre 02 ativos ##


ratio = S1/S2
ratio.plot(figsize=(12,6))
plt.axhline(ratio.mean(), color='black')
plt.xlim('2021-01-01', '2022-01-01')
plt.legend(['Price Ratio']);


# In[006] ## ZScore entre 02 ativos ##

def zscore(series):
    return (series - series.mean()) / np.std(series)


zscore(ratio).plot(figsize=(12,6))
plt.axhline(zscore(ratio).mean())
plt.axhline(1.0, color='red')
plt.axhline(-1.0, color='green')
plt.xlim('2018-01-01', '2022-01-01')
plt.show()


