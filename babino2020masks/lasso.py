# AUTOGENERATED! DO NOT EDIT! File to edit: 01_lasso.ipynb (unless otherwise specified).

__all__ = ['FirstInChunkSelector', 'LassoICSelector']

# Cell
import numpy as np
from sklearn import linear_model
import statsmodels.api as sm
from statsmodels.sandbox.regression.predstd import wls_prediction_std
from fastcore.all import *
from .core import *

# Cell
class FirstInChunkSelector(object):
    '''Selects first element from each non zero chunk.'''

    def __init__(self, clf):
        self.clf, self.coef, self.mask = clf, None, None

    def select_coef(self):
        n_features = len(self.clf.coef_)
        no_zero = np.zeros(n_features+1)
        no_zero[1:] = self.clf.coef_ != 0
        self.mask = np.diff(no_zero)>0
        self.mask[0] = True
        self.coef = self.clf.coef_[self.mask]
        return self.coef

    def transform(self, X):
        self.select_coef()
        return X[:, self.mask]

    def get_support(self):
        self.select_coef()
        return self.mask

    def get_number_of_features(self):
        self.select_coef()
        return sum(self.mask)

# Cell
class LassoICSelector(object):
    """LASSO regression with FirstInChunkSelector."""

    def __init__(self, y, criterion, alpha=0.05):
        self.lasso = linear_model.LassoLars(alpha=0, max_iter=100000)
        self.criterion = criterion
        self.selector = FirstInChunkSelector(self.lasso)
        self.OLS = sm.OLS
        self.X, self.y = self.liniarize_Xy(y)
        self.ols = self.OLS(self.y, self.X)
        self.ols_results = None
        self.final_ols = False
        self.alpha = alpha

    def liniarize_Xy(self, y):
        y = np.log(y)
        X = np.tri(len(y))
        X = np.cumsum(X, axis=0)[:, 1:]
        return X[~np.isnan(y), :], maybe_attr(y[~np.isnan(y)], 'values')

    def transform_to_ols(self, X):
        '''Selects only the features of  that X are used by OLS.
        Also, adds a coloumn with ones for the intercept.
        '''
        X_new = self.selector.transform(X)
        if self.final_ols: X_new = X[:, self.support]
        return np.hstack([X_new, np.ones((X_new.shape[0], 1))])

    def fit(self, X, y):
        '''Selects features and fits the OLS.'''

        # select features
        X_new = self.transform_to_ols(X)

        # fit ols
        self.ols = self.OLS(y, X_new)
        self.ols_results = self.ols.fit()

        # iteratively remove non signicative variables and fit again
        mask = self.ols_results.pvalues < self.alpha / len(self.ols_results.pvalues)
        mask[0] = True
        Xnew = self.transform_to_ols(X)
        Xnew = Xnew[:, mask]
        self.support = self.selector.get_support()
        self.ols = self.OLS(y, Xnew)
        self.ols_results = self.ols.fit()
        while any(self.ols_results.pvalues[1:] >= self.alpha / len(self.ols_results.pvalues)):
            mask[mask] = (self.ols_results.pvalues < self.alpha / len(self.ols_results.pvalues))
            mask[0] = True
            Xnew = self.transform_to_ols(X)
            Xnew = Xnew[:, mask]
            self.support = self.selector.get_support()
            self.ols = self.OLS(y, Xnew)
            self.ols_results = self.ols.fit()

        self.support[self.support] = mask[:-1]

    def fit_best_alpha(self):
        '''Returns the model with the lowest cirterion.'''
        X, y = self.X, self.y
        self.lasso.fit(X, y)
        alphas = self.lasso.alphas_
        self.criterions_ = np.zeros(len(alphas))
        self.log_liklehods = np.zeros(len(alphas))


        for i, alpha in enumerate(alphas):
            self.lasso.coef_ = self.lasso.coef_path_[:, i]
            self.fit(X, y)
            self.criterions_[i], self.log_liklehods[i] = self.get_criterion(self.ols.exog, y)

        # we use a list of tuples to find the minimum cirterion value.
        # If there are ties, we use the maximum alpha value.
        criterions_idx = list(zip(self.criterions_, alphas, range(len(alphas))))
        criterion, alpha, idx = min(criterions_idx, key=lambda x: (x[0], -x[1]))
        self.lasso.coef_ = self.lasso.coef_path_[:, idx]
        self.lasso.alpha = alpha
        self.fit(X, y)
        self.final_ols = True

    def predict(self, X):
        '''Predicts y useing the OLS fit.'''
        return self.ols.predict(self.ols_results.params, X)

    def log_liklihood(self, X, y):
        '''Computes the log liklihood assuming normally distributed errors.'''

        eps64 = np.finfo('float64').eps

        # residuals
        R = y - self.predict(X)
        sigma2 = np.var(R)

        loglike = -0.5 * len(R) * np.log(sigma2)
        loglike -= 0.5 * len(R) * np.log(2*np.pi) - 0.5*len(R) + 0.5
        return loglike

    def get_criterion(self, X, y):
        '''Computes AIC or BIC criterion.'''

        n_samples = X.shape[0]
        if self.criterion == 'aic':
            K = 2  # AIC
        elif self.criterion == 'bic':
            K = np.log(n_samples)
        else:
            raise ValueError('criterion should be either bic or aic')

        log_like = self.log_liklihood(X, y)
        df = X.shape[1]

        aic = K * df - 2*log_like
        self.criterion_ = aic

        return self.criterion_, log_like

    def odds_hat_l_u(self):
        Xols = self.transform_to_ols(self.X)
        yhat = self.ols.predict(self.ols_results.params, Xols)
        # from equation 5
        odds_hat = np.exp(yhat)
        # the error in yhat is
        (yhat_std, yhat_l, yhat_u) = wls_prediction_std(self.ols_results, Xols)
        oddshat_l = np.exp(yhat-2*yhat_std)
        oddshat_u = np.exp(yhat+2*yhat_std)
        return odds_hat, oddshat_l, oddshat_u