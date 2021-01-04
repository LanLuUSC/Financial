import datetime
import matplotlib.pyplot as plot
from matplotlib import style
import pandas
import pandas_datareader.data as web
import numpy as np
import os.path


def GetData(dataName, dataSource, indexName, startTime, endTime):
    dataFileName = dataName + ".csv"
    # if not os.path.exists(dataFileName):
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
            percentage.append(100 * (data[dataName][n] - data[dataName][index])/data[dataName][n])
        while index <= n:
            if (data.index[n] - data.index[index]).days >= 365:
                index += 1
            else:
                break
               
    incPer = pandas.DataFrame({'Percentage':percentage, 'Date' : timeSeries})
    incPer.reset_index(inplace=True)
    incPer.set_index('Date', inplace=True)
    return incPer
def CalOutputGap(gdp, gdpRowName, potentialGdp, potentialGdpRowName):

    outputGaps = []
    time = []
    for n in range(len(gdp.index)) :
        outputGap = 100 * (gdp[gdpRowName][n] - potentialGdp[potentialGdpRowName][n]) / potentialGdp[potentialGdpRowName][n]
        outputGaps.append(outputGap)
        time.append(gdp.index[n])

    result = pandas.DataFrame({'OutputGap':outputGaps, 'Date' : time})
    result.reset_index(inplace=True)
    result.set_index('Date', inplace=True)
    return result
def CalGrowthPeriod(data, dataName, threshold) :
    dataCount = len(data.index)
    if (dataCount < 2) :
        return

    UP = 1
    DOWN = -1
    UNJUDGED = 0
    curTrend = UNJUDGED
    localPeakIndex = 0
    periodStartIndex = 0
    
    result = []
    THRESHOLD = threshold
    for n in range(1, dataCount):
        curValue = data[dataName][n]
        diff = curValue - data[dataName][localPeakIndex]
        #direction has changed
        if abs(diff) > THRESHOLD and diff * curTrend <= 0:
            # if is not start index
            if (curTrend != UNJUDGED) :
                result.append((data.index[periodStartIndex], curTrend))
            curTrend = UP if diff > 0 else DOWN
            periodStartIndex = localPeakIndex        
        if curTrend * diff > 0 :
            localPeakIndex = n
    #insert last period
    if result[-1][0] != periodStartIndex :
        result.append((data.index[periodStartIndex], curTrend))
    return result
# four phases (gdp, inflation)
REFLATION = 0 #(-1, -1)
RECOVERY = 1 #(1, -1)
OVERHEAT = 2 #(1, 1)
STAGFLATION = 3 #(-1, 1)
def WhichPhase(gdpPeriod, inflationPeriod) :
    if gdpPeriod == -1 and inflationPeriod == -1:
        return REFLATION
    if gdpPeriod == 1 and inflationPeriod == -1:
        return RECOVERY
    if gdpPeriod == 1 and inflationPeriod == 1:
        return OVERHEAT
    if gdpPeriod == -1 and inflationPeriod == 1:
        return STAGFLATION
def CalPhases(gdpPeriod, inflationPeriod) :
    phases = []
    i = 0
    j = 0
    while i < len(gdpPeriod) and j < len(inflationPeriod) :
        if (gdpPeriod[i][0] < inflationPeriod[j][0]) : #gdp date is earlier
            phase = WhichPhase(gdpPeriod[i][1], inflationPeriod[j][1] * (-1))
            phases.append((gdpPeriod[i][0], phase))
            i += 1
        else :
            phase = WhichPhase(gdpPeriod[i][1] * (-1), inflationPeriod[j][1])
            phases.append((inflationPeriod[j][0], phase))
            j += 1
    while i < len(gdpPeriod):
            phase = WhichPhase(gdpPeriod[i][1], inflationPeriod[-1][1])
            phases.append((gdpPeriod[i][0], phase))
            i += 1
    while j < len(inflationPeriod):
            phase = WhichPhase(gdpPeriod[-1][1], inflationPeriod[j][1])
            phases.append((inflationPeriod[j][0], phase))
            j += 1

    return phases
def PlotBackgroundRegion(ax, peroidTupleArray, colors, labels):
    printedLabels = set()
    for n in range(1, len(peroidTupleArray)):
        label = labels[peroidTupleArray[n - 1][1]]
        ax.axvspan(peroidTupleArray[n - 1][0], peroidTupleArray[n][0], facecolor = colors[peroidTupleArray[n - 1][1]], alpha = 0.5,label = '_' if label in printedLabels else label)
        printedLabels.add(label)
    ax.axvspan(peroidTupleArray[-1][0], datetime.datetime.now(), facecolor = colors[peroidTupleArray[-1][1]], alpha = 0.5)

startTime = datetime.datetime(1985, 1, 1)
endTime = datetime.datetime.now()
gdp = GetData("GDP", "fred", "DATE", startTime, endTime)
gdpIncrePercentage = CalGdpIncreasePercentage(gdp)
gdpPeriod = CalGrowthPeriod(gdpIncrePercentage, 'Percentage', 0.5)
# gdpIncreGoldenRule = GetData('CPGDPAI', 'fred', 'DATE', startTime, endTime)
# rawGDP = GetData('GDPC1', 'fred', 'DATE', startTime, endTime)
# rawPotentialGDP = GetData('GDPPOT', 'fred', 'DATE', startTime, endTime)
# outputGap = CalOutputGap(rawGDP, 'GDPC1', rawPotentialGDP, 'GDPPOT')
# gdpPeriod = CalGrowthPeriod(outputGap, 'OutputGap', 2)
# inflation = GetData('FPCPITOTLZGUSA', 'fred', 'DATE', startTime, endTime)
# inflationPeriod = CalGrowthPeriod(inflation, 'FPCPITOTLZGUSA', 0.5)
cpi = GetData('CUUS0000SA0', 'fred', 'DATE', startTime, endTime)
cpiIncPer = CalSamePeriodLastYearIncreaseRatio(cpi, 'CUUS0000SA0')
inflationPeriod = CalGrowthPeriod(cpiIncPer, 'Percentage', 1.5)
economicPhases = CalPhases(gdpPeriod, inflationPeriod)
iron = GetData('PIORECRUSDM', 'fred', 'DATE', startTime, endTime)
# print(outputGap.head())
# sp500 = GetData("%5EGSPC", "yahoo", "Date", startTime, endTime)
# sp500Per = CalSamePeriodLastYearIncreaseRatio(sp500, 'Close')
# oil = GetData('DCOILWTICO', 'fred', 'DATE', startTime, endTime)
# oilPer = CalSamePeriodLastYearIncreaseRatio(oil, 'DCOILWTICO')
#df['100ma'] = df['Adj Close'].rolling(window=100, min_periods=0).mean()
# print(sp500.head())


style.use('ggplot')
ax1 = plot.subplot2grid((7,1), (0,0), rowspan=3, colspan=1)
# ax1.bar(outputGap.index, outputGap['Percentage'], width = 100)
ax1.plot(iron.index, iron['PIORECRUSDM'])
# ax1.legend(['OutputGap'])
PlotBackgroundRegion(ax1,economicPhases,['b', 'g', 'r', 'y', 'm', 'c'],['1 REFLATION','2 RECOVERY','3 OVERHEAT','4 STAGFLATION'])
ax1.legend()

ax2 = plot.subplot2grid((7,1), (3,0), rowspan=2, colspan=1, sharex = ax1)
ax2.plot(cpiIncPer.index, cpiIncPer['Percentage'])
# ax1.plot(inflation.index, inflation['FPCPITOTLZGUSA'])
ax2.legend(['CPI'])
PlotBackgroundRegion(ax2, inflationPeriod, ['b', 'g', 'r'], ['','UP', 'DOWN'])

ax3 = plot.subplot2grid((7,1), (5,0), rowspan=2, colspan=1, sharex = ax1)
# ax3.plot(outputGap.index, outputGap['OutputGap'])
ax3.plot(gdp.index, gdp['GDP'])
# ax1.plot(inflation.index, inflation['FPCPITOTLZGUSA'])
ax3.legend(['GDP'])
PlotBackgroundRegion(ax3, gdpPeriod, ['b', 'g', 'r'], ['','UP', 'DOWN'])

# ax2 = plot.subplot2grid((7,1), (6,0), rowspan=1, colspan=1, sharex = ax1)
# ax2.plot(sp500Per.index, sp500Per['Percentage'])
# ax2.legend(['Sp500'])
# ax3 = plot.subplot2grid((7,1), (4,0), rowspan=2, colspan=1, sharex = ax1)
# ax3.plot(oilPer.index, oilPer['Percentage'])
# ax3.legend(['West Texas Crude Oil'])

# ax2.bar(df.index, df['Volume'])

plot.show()
