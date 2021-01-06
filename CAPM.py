import datetime
import matplotlib.pyplot as plot
from matplotlib import style
import pandas
import pandas_datareader.data as web
import pandas_datareader.famafrench as famaReader
import numpy as np
import os.path
import statsmodels.api as sm
import statsmodels.formula.api as smf



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
def GetFamaFrenchData(dataName, indexName, startTime, endTime):
# dataName can be:
# F-F_Research_Data_Factors
# F-F_Research_Data_Factors_weekly
# F-F_Research_Data_Factors_daily
# F-F_Research_Data_5_Factors_2x3
# F-F_Research_Data_5_Factors_2x3_daily
    dataFileName = dataName + ".csv"

    rawData = famaReader.FamaFrenchReader(dataName, startTime, endTime).read()
    data = pandas.DataFrame(rawData[0]) 
    dataFileName = dataName + "_fama_french.csv"
    data.to_csv(dataFileName)
    return data
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
def UsePolynominalFit(X, Y):
    df = pandas.concat([X,Y], axis = 1)
    df.columnx = ['X', 'Y']
    print(df.head())
    formulaString = 'Y ~ X + I(X**2) + I(X**3) + I(X**4) + I(X**5)'
    results = smf.ols(formula= formulaString , data = df).fit()
    print(results.summary())

startTime = datetime.datetime(2015, 1, 1)
endTime = datetime.datetime.now()
MARKET_SYMBOL = '%5EGSPC'
STOCK_SYMBOL = 'TSLA'
market = GetData(MARKET_SYMBOL, "yahoo", "Date", startTime, endTime)
stock = GetData(STOCK_SYMBOL, "yahoo", "Date", startTime, endTime)
prices = pandas.concat([market['Close'], stock['Close']], axis = 1)
prices.columns = [MARKET_SYMBOL, STOCK_SYMBOL]
prices = prices.dropna() # this makes sure when we calculate returns X and Y will have same row numbers
# print(prices.tail())
farmaFrench = GetFamaFrenchData("F-F_Research_Data_Factors_daily", "Date", startTime, endTime)
# print(farmaFrench.head())
all_data = pandas.merge(prices,farmaFrench, how = 'inner', left_index= True, right_index= True)
# print(all_data.head())
X = CalDailyReturns(all_data, MARKET_SYMBOL)[MARKET_SYMBOL]
# print(X.tail())
Y = CalDailyReturns(all_data, STOCK_SYMBOL)[STOCK_SYMBOL]

#print(Y.head())
X1 = sm.add_constant(X)
model = sm.OLS(Y, X1)
results = model.fit()
print(results.summary())

#all_data = all_data.rename(columns = {MARKET_SYMBOL : 'X', STOCK_SYMBOL : 'Y'})
# print(all_data.head())
data_final = pandas.concat([X,Y], axis = 1)
data_final.columnx = ['X', 'Y']
data_final = pandas.merge(data_final,farmaFrench, how = 'inner', left_index= True, right_index= True)
# print(data_final.head())
farmaFrenchFormulaString ='Y ~ X+ SMB + HML'
farmaFrenchResults = smf.ols(formula= farmaFrenchFormulaString , data = data_final).fit()
print(farmaFrenchResults.summary())


#UsePolynominalFit(X, Y) # use polynominal to do CAPM, looks not good
#test previous results
# Z = CalReturns(prices, 7)[MARKET_SYMBOL]
# #print(Z.head())
# W = CalReturns(prices, 7)[STOCK_SYMBOL]
# Z1 = sm.add_constant(Z)
# testModel = sm.OLS(W, Z1)
# testResults = testModel.fit()
# print(testResults.summary())