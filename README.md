# Masks and COVID-19: a causal framework for imputing value to public-health interventions
> Code to reproduce <a href='https://arxiv.org/abs/2006.05532'>Masks and COVID-19</a>.


This is a refactored version of the original [code](https://github.com/ababino/corona). 

## Install

`pip install babino2020masks`

## How to use

### Gather data

```python
ny = API(api_settings['NYS'][:2], **api_settings['NYS'][2])
df = ny.get_all_data_statewide()
```

    /home/runner/work/babino2020masks/babino2020masks/babino2020masks/core.py:78: FutureWarning: Dropping invalid columns in DataFrameGroupBy.add is deprecated. In a future version, a TypeError will be raised. Before calling .add, select only columns which should be valid for the function.
      df = df.groupby('date').sum()


```python
ax = plot_data_and_fit(df, 'Date', 'Odds', None, None, None, figsize=(10, 7))
ax.set_title(f'{df.tail(1).Date[0]:%B %d, %Y}, Positivity Odds:{df.tail(1).Odds[0]:2.3}');
```


![png](docs/images/output_6_0.png)


### Fit the model

```python
sdf = df.loc[df.Date<='15-05-2020'].copy()
lics = LassoICSelector(sdf['Odds'], 'bic')
lics.fit_best_alpha()
```

    /opt/hostedtoolcache/Python/3.8.12/x64/lib/python3.8/site-packages/sklearn/linear_model/_base.py:133: FutureWarning: The default of 'normalize' will be set to False in version 1.2 and deprecated in version 1.4.
    If you wish to scale the data, use Pipeline with a StandardScaler in a preprocessing stage. To reproduce the previous behavior:
    
    from sklearn.pipeline import make_pipeline
    
    model = make_pipeline(StandardScaler(with_mean=False), LassoLars())
    
    If you wish to pass a sample_weight parameter, you need to pass it as a fit parameter to each step of the pipeline as follows:
    
    kwargs = {s[0] + '__sample_weight': sample_weight for s in model.steps}
    model.fit(X, y, **kwargs)
    
    Set parameter alpha to: original_alpha * np.sqrt(n_samples). 
      warnings.warn(


### Positivity Odds in NYS

```python
sdf['Fit'], sdf['Odds_l'], sdf['Odds_u'] = lics.odds_hat_l_u()
ax = plot_data_and_fit(sdf, 'Date', 'Odds', 'Fit', 'Odds_l', 'Odds_u', figsize=(10, 7))
```


![png](docs/images/output_10_0.png)


### Instantaneous reproduction number, $R_t$

```python
sdf['R'], sdf['Rl'], sdf['Ru'] = lics.rt()
ax = plot_data_and_fit(sdf, 'Date', None, 'R', 'Rl', 'Ru', figsize=(10, 7), logy=False, palette=[colorblind[1],colorblind[1]])
```


![png](docs/images/output_12_0.png)


### Counterfactual Scenario without  Masks

```python
sdf['Cf. Odds'], sdf['cf_odds_l'], sdf['cf_odds_u'] = lics.counterfactual()
```

```python
ax = plot_data_and_fit(sdf, 'Date', 'Odds', 'Fit', 'Odds_l', 'Odds_u', figsize=(10, 7))
plot_data_and_fit(sdf, 'Date', None, 'Cf. Odds', 'cf_odds_l', 'cf_odds_u', palette=[colorblind[2],colorblind[2]], ax=ax);
```


![png](docs/images/output_15_0.png)


    Last updated on 01/19/2022 13:26:14

