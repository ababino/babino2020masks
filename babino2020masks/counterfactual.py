# AUTOGENERATED! DO NOT EDIT! File to edit: 02_counterfactual.ipynb (unless otherwise specified).

__all__ = []

# Cell
from .lasso import *
import statsmodels.api as sm
from fastcore.all import *
from statsmodels.sandbox.regression.predstd import wls_prediction_std
import numpy as np

# Cell
@patch
def counterfactual(self:LassoICSelector):
    exog_full = self.transform_to_ols(self.X)
    ind = exog_full[:, -2]<2
    y_sub = self.y[ind]
    exog_sub = exog_full[ind,:]
    exog_sub = np.hstack([exog_sub[:, :-2],exog_sub[:,-1:]])
    ols = sm.OLS(y_sub, exog_sub)
    res = ols.fit()
    exog = np.hstack([exog_full[:, :-2],exog_full[:,-1:]])
    yhat = res.predict(exog)
    yhat_orig = self.predict(exog_full)

    odds_cf = np.exp(yhat)
    (yhat_std, yhat_l, yhat_u) = wls_prediction_std(res, exog)
    oddshat_std = odds_cf*yhat_std
    return odds_cf, odds_cf - 2*oddshat_std, odds_cf + 2*oddshat_std