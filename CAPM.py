import datetime
import matplotlib.pyplot as plot
from matplotlib import style
import pandas
import pandas_datareader.data as web
import numpy as np
import os.path
import statsmodels.api as sm


def GetData(dataName, dataSource, indexName, startTime, endTime):
    dataFileName = dataName + ".csv"

    rawData = web.DataReader(dataName, dataSource, startTime, endTime)
    # print(rawData.head())
    rawData.reset_index(inplace=True)
    rawData.set_index(indexName, inplace=True)
    #df = df.drop("Symbol", axis=1)
    rawData.to_csv(dataFileName)

    returnData = pandas.read_csv(dataFileName, parse_dates=True, index_col=0)
    return returnData
def CalGdpIncreasePercentage(gdp):
    # gdpIncPer = pandas.DataFrame(columns=['Percentage'])
    timeSeries = []
    percentage = []
    prevGDP = 0.0
    curGDP = 0.0
    for n in range(len(gdp.index)):
        if len(timeSeries) == 0 and (gdp.index[n] - gdp.index[0]).days >= 365 :
            timeSeries.append(gdp.index[n])
            percentage.append(0.0)
            prevGDP = curGDP
            curGDP = 0.0
        elif len(timeSeries) > 0 and (gdp.index[n] - timeSeries[-1]).days >= 365 :
            percentage.append((curGDP - prevGDP) * 100/ prevGDP)
            timeSeries.append(gdp.index[n])
            prevGDP = curGDP
            curGDP = 0.0
        curGDP += gdp['GDP'][n]        
    gdpIncPer = pandas.DataFrame({'Percentage':percentage, 'Date' : timeSeries})
    gdpIncPer.reset_index(inplace=True)
    gdpIncPer.set_index('Date', inplace=True)
    return gdpIncPer
def CalSamePeriodLastYearIncreaseRatio(data, dataName):
    timeSeries = []
    percentage = []
    index = 0
    for n in range(len(data.index)):
        dayDiff = (data.index[n] - data.index[index]).days
        if dayDiff >= 365 and dayDiff <= 455:
            timeSeries.append(data.index[index])
            percentage.append(100 * (data[dataName][n] - data[dataName][index])/data[dataName][index])
        while index <= n:
            if (data.index[n] - data.index[index]).days >= 365:
                index += 1
            else:
                break
               
    incPer = pandas.DataFrame({'Percentage':percentage, 'Date' : timeSeries})
    incPer.reset_index(inplace=True)
    incPer.set_index('Date', inplace=True)
    return incPer
def CalMonthlyReturns(data, dataName):
    timeSeries = []
    returns = []
    index = 0
    for n in range(len(data.index)):
        dayDiff = (data.index[n] - data.index[index]).days
        if dayDiff >= 30:
            timeSeries.append(data.index[n])
            returns.append(100 * (data[dataName][n] - data[dataName][index])/data[dataName][index])
            index = n
               
    result = pandas.DataFrame({dataName:returns, 'Date' : timeSeries})
    result.reset_index(inplace=True)
    result.set_index('Date', inplace=True)
    return result
def CalWeeklyReturns(data, dataName):
    timeSeries = []
    returns = []
    index = 0
    for n in range(len(data.index)):
        dayDiff = (data.index[n] - data.index[index]).days
        if dayDiff >= 7:
            timeSeries.append(data.index[n])
            returns.append(100 * (data[dataName][n] - data[dataName][index])/data[dataName][index])
            index = n
        # while index <= n:
        #     if (data.index[n] - data.index[index]).days >= 7:
        #         index += 1
        #     else:
        #         break
               
    result = pandas.DataFrame({dataName:returns, 'Date' : timeSeries})
    result.reset_index(inplace=True)
    result.set_index('Date', inplace=True)
    return result
def CalDailyReturns(data, dataName):
    return CalReturns(data, 1)
def CalReturns(data, period):# another way to calculate returns, used to check if previous calculations are correct
    return data.pct_change(periods=period).dropna()

startTime = datetime.datetime(2015, 1, 1)
endTime = datetime.datetime.now()
MARKET_SYMBOL = '%5EGSPC'
STOCK_SYMBOL = 'FXAIX'
market = GetData(MARKET_SYMBOL, "yahoo", "Date", startTime, endTime)
stock = GetData(STOCK_SYMBOL, "yahoo", "Date", startTime, endTime)
prices = pandas.concat([market['Close'], stock['Close']], axis = 1)
prices.columns = [MARKET_SYMBOL, STOCK_SYMBOL]
prices = prices.dropna() # this makes sure when we calculate returns X and Y will have same row numbers
print(prices.tail())

X = CalMonthlyReturns(prices, MARKET_SYMBOL)[MARKET_SYMBOL]
print(X.tail())
Y = CalMonthlyReturns(prices, STOCK_SYMBOL)[STOCK_SYMBOL]
#print(Y.head())
X1 = sm.add_constant(X)
model = sm.OLS(Y, X1)
results = model.fit()
print(results.summary())

#test previous results
# Z = CalReturns(prices, 7)[MARKET_SYMBOL]
# #print(Z.head())
# W = CalReturns(prices, 7)[STOCK_SYMBOL]
# Z1 = sm.add_constant(Z)
# testModel = sm.OLS(W, Z1)
# testResults = testModel.fit()
# print(testResults.summary())