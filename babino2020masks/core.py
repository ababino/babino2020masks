# AUTOGENERATED! DO NOT EDIT! File to edit: 00_core.ipynb (unless otherwise specified).

__all__ = ['GAMMA', 'NYSAPI', 'NEW_YORK_EVENTS', 'plot_data_and_fit']

# Cell
import os
import pandas as pd
import requests
from fastcore.all import *
import seaborn as sns
from matplotlib import pyplot as plt

# Cell
sns.set_style("whitegrid")
sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 2.5})

# Cell
GAMMA = 1/7.5

# Cell
class NYSAPI:
    def __init__(self, usecols=['test_date', 'total_number_of_tests', 'new_positives']):
        self.url_base = "https://health.data.ny.gov/resource/xdss-u53e.csv/"
        self.usecols = usecols
        self.pretty_cols = [x.split('_')[-1].capitalize() for x in self.usecols]

    def get_data(self, offset=0, limit=5000):
        url = self.url_base + f'?$limit={limit}&$offset={offset}'
        return pd.read_csv(url, usecols=self.usecols)[self.usecols]

    def iter_data(self, offset=0, limit=5000):
        df = pd.DataFrame(columns=self.usecols)
        while True:
            df = self.get_data(offset=offset, limit=limit)
            if len(df)==0: return
            offset += limit
            yield  df

    def get_all_data(self):
        df = pd.DataFrame(columns=self.usecols)
        for o in self.iter_data(): df = df.append(o)
        return df

    def get_all_data_nice(self):
        df = self.get_all_data()
        df = df.rename(columns={k:v for k,v in zip(self.usecols, self.pretty_cols)})
        if 'Date' in df.columns: df['Date'] = pd.to_datetime(df['Date'])
        return df

    def get_all_data_statewide(self, min_date='2020-03-15'):
        '''Gets statewide aggregated data.'''
        df = self.get_all_data_nice()
        assert 'Date' in df.columns, 'data do not have Date column'
        df['date'] = df['Date']
        df = df.groupby('date').sum()
        df['Date'] = pd.to_datetime(df.index)
        df['Odds'] = df.Positives / (df.Tests - df.Positives)
        df = df[df.Date>=min_date]
        return df

# Cell
NEW_YORK_EVENTS = L('03-16-2020 20:00',
                    '03-18-2020 20:00',
                    '03-20-2020 20:00',
                    '03-22-2020 00:00',
                    '04-03-2020 00:00',
                    '04-12-2020 00:00',
                    '04-17-2020 00:00').map(pd.to_datetime)

# Cell
@delegates(plt.plot)
def plot_data_and_fit(df, x, y, y_hat, yl, yu, logy=True, **kwargs):
    ax = df.plot(x=x, y=y_hat, logy=logy, **kwargs);
    ax = df.plot.scatter(x=x, y=y, logy=logy, ax=ax);
    plt.fill_between(df.index, df.Odds_l, df.Odds_u, color='b', alpha=0.2);
    return ax