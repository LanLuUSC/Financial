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
from abc import ABCMeta, abstractmethod
from datetime import date

class Strategy(metaclass=ABCMeta):
    class Balance:
        def __init__(self, date, stockShare, stockValue, base, cash, y):
            self.Date = date
            self.CurrentStockShare = stockShare
            self.CurrentStockValue = stockValue
            self.BaseTotal = base
            self.CurrentCash = cash
            self.Yield = y

        def ConvertToDict(self):
            return {
                "Date" : self.Date,
                "CurrentStockShare" : self.CurrentStockShare,
                "CurrentStockValue" : self.CurrentStockValue,
                "BaseTotal" : self.BaseTotal,
                "CurrentCash" : self.CurrentCash,
                "Yield" : self.Yield
            }

    def __init__(self, startDate, withdrawAmount, startStockShare = 0, startStockValue = 0, startBase = 0, startCash = 0, startYield = 0):
        self.AccountBook = []
        self.AutomaticWithdrawAmountPerPeriod = withdrawAmount
        initialBalance = self.Balance(startDate - datetime.timedelta(days = -1), startStockShare, startStockValue, startBase, startCash, startYield)
        self.AccountBook.append(initialBalance)

    @abstractmethod
    def Exec(self, date, stockIndex):
        pass
class BaselineInvestment(Strategy):#invest one time at beginning, get startStockShare and hold it forever
    def __init__(self, startDate, withdrawAmount, startStockShare, startStockValue, startBase, startCash=0, startYield=0):
        super().__init__(startDate, 0, startStockShare=startStockShare, startStockValue=startStockValue, startBase=startBase, startCash=startCash, startYield=startYield)

    def Exec(self, date: datetime, stockIndex: float):
        prevBalance = self.AccountBook[-1]
        currentBalance = Strategy.Balance(date, prevBalance.CurrentStockShare, prevBalance.CurrentStockShare * stockIndex, prevBalance.BaseTotal, 0, 100 * stockIndex * prevBalance.CurrentStockShare / prevBalance.BaseTotal - 100 if prevBalance.BaseTotal != 0 else 0)
        self.AccountBook.append(currentBalance)
class BasicAutomaticInvestment(Strategy):
    def Exec(self, date : datetime, stockIndex : float):
        prevBalance = self.AccountBook[-1]
        currentBalance = Strategy.Balance(date, prevBalance.CurrentStockShare + self.AutomaticWithdrawAmountPerPeriod/stockIndex, prevBalance.CurrentStockShare * stockIndex + self.AutomaticWithdrawAmountPerPeriod, prevBalance.BaseTotal + self.AutomaticWithdrawAmountPerPeriod, 0, 100 * stockIndex * prevBalance.CurrentStockShare / prevBalance.BaseTotal - 100 if prevBalance.BaseTotal != 0 else 0)
        self.AccountBook.append(currentBalance)
class Simulator(metaclass=ABCMeta):
    @abstractmethod
    def Simulate(self, dataName, marketData : pandas.DataFrame, startTime : datetime, endTime : datetime, strategy : Strategy):
        pass 

    
# automatically invest every paycheck period(Friday)
class EveryPaycheckSimulator(Simulator):
    def Simulate(self, dataName, marketData : pandas.DataFrame, startTime : datetime, endTime : datetime, strategy : Strategy):
        date = startTime
        while (date.weekday() != 5):# find first firday
            date = date  + datetime.timedelta(days = 1)
        while date <= endTime:
            actuallInvestDate = date
            while actuallInvestDate < endTime and (actuallInvestDate not in marketData.index) :
                actuallInvestDate = actuallInvestDate + datetime.timedelta(days = 1)
            if actuallInvestDate in marketData.index:
                strategy.Exec(actuallInvestDate, marketData['Close'][actuallInvestDate])
            date = date + datetime.timedelta(days = 14) # always invest on every other friday
class PrintResults():
    @staticmethod
    def CreateStrategyData(strategy: Strategy) -> pandas.DataFrame:
        strategyData = pandas.DataFrame.from_records([balance.ConvertToDict() for balance in strategy.AccountBook])
        return strategyData
    @staticmethod
    def Print(data : pandas.DataFrame):
        style.use('ggplot')
        ax1 = plot.subplot2grid((7,1), (0,0), rowspan=3, colspan=1)
        ax1.plot(data['Date'], data['CurrentStockValue'])
        ax1.legend(['CurrentStockValue']) 
        ax2 = plot.subplot2grid((7,1), (3,0), rowspan=3, colspan=1)
        ax2.plot(data['Date'], data['Yield'])
        ax2.legend(['Yield']) 
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


startTime = datetime.datetime(2000, 1, 1)
endTime = datetime.datetime.now()
MARKET_SYMBOL = '^GSPC'
market = GetData(MARKET_SYMBOL, "yahoo", "Date", startTime, endTime)
# print(stock.head())
#simulate
basicAutomaticInvestmentStrategy = BasicAutomaticInvestment(startTime, 500)
paycheckSimulator = EveryPaycheckSimulator()
paycheckSimulator.Simulate(MARKET_SYMBOL, market, startTime, endTime, basicAutomaticInvestmentStrategy)
basicAutomaticInvestmentStrategyData = PrintResults.CreateStrategyData(basicAutomaticInvestmentStrategy)
basicAutomaticInvestmentStrategyData.to_csv("basic_invest.csv")

baselineInvestmentStrategy = BaselineInvestment(market.index[0], 0, 1, market['Close'][0], market['Close'][0])
paycheckSimulator.Simulate(MARKET_SYMBOL, market, startTime, endTime, baselineInvestmentStrategy)
baselineInvestmentStrategyData = PrintResults.CreateStrategyData(baselineInvestmentStrategy)
baselineInvestmentStrategyData.to_csv("baseline_invest.csv")

#start to plot
style.use('ggplot')
fig, ax = plot.subplots(nrows=3,ncols=1)
plot.subplot(3,1,1)
plot.plot(market.index, market['Close'],'r', label='SP500')
plot.legend()

plot.subplot(3,1,2)
plot.plot(basicAutomaticInvestmentStrategyData['Date'], basicAutomaticInvestmentStrategyData['CurrentStockValue'],'r', label='basicAutomaticInvestmentStrategyData')

plot.legend()

plot.subplot(3,1,3)
plot.plot(baselineInvestmentStrategyData['Date'], baselineInvestmentStrategyData['Yield'], 'g', label = 'Baseline Yield')
plot.plot(basicAutomaticInvestmentStrategyData['Date'], basicAutomaticInvestmentStrategyData['Yield'], 'b', label='Basic Auto Yield')
plot.legend()

# PrintResults.Print(PrintResults.CreateStrategyData(basicAutomaticInvestmentStrategy))
plot.show()