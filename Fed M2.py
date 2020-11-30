import datetime as dt
import matplotlib.pyplot as plt
from matplotlib import style
import pandas as pd
import pandas_datareader.data as web
style.use('ggplot')

start = dt.datetime(2000, 1, 1)
end = dt.datetime.now()
df = web.DataReader("M2V", 'fred', start, end)
print(df.head())
df.reset_index(inplace=True)
df.set_index("D", inplace=True)
#df = df.drop("Symbol", axis=1)
df.to_csv('m2_us.csv')
df = pd.read_csv('m2_us.csv', parse_dates=True, index_col=0)

ax1 = plt.subplot2grid((6,1), (0,0), rowspan=5, colspan=1)
ax1.plot(df.index, df['M2V'])

plt.show()
