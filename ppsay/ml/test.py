import numpy as np
from sklearn import linear_model

def get_classifier():
    logistic = linear_model.LogisticRegression()

    params = {'C': 100000.0,
     'class_weight': 'auto',
     'dual': False,
     'fit_intercept': True,
     'intercept_scaling': 1,
     'max_iter': 100,
     'multi_class': 'ovr',
     'penalty': 'l2',
     'random_state': None,
     'solver': 'liblinear',
     'tol': 0.0001,
     'verbose': 0}

    coef = np.array([[ 0.01020062,  0.99621041,  4.18454742,  0.23268564,  1.88353177]])
    intercept = np.array([-2.74706061])
    classes = np.array([0, 1])

    logistic.set_params(**params)
    logistic.classes_ = classes
    logistic.coef_ = coef
    logistic.intercept_ = intercept

    return logistic

if __name__ == "__main__":
    logistic = get_classifier()

