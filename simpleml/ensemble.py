'''
Ensemble methods
'''
import numpy as np

from . import baseclasses as bc


class EnsembleBinaryClassifier:
    def __init__(self):
        self.models = []
        self.n_models = 0
        self.weights = []

    def add_model(self, model, weight=1):
        typename = type(model).__name__
        if not isinstance(model, bc.BinaryClassifier):
            raise TypeError("Model is '{}', which is not a "
                            "'BinaryClassifier'.".format(typename))
        self.models.append(model)
        self.n_models += 1
        self.weights.append(weight)

    def classify(self, X):
        if len(X.shape) == 1:
            n_obs = 1
        else:
            n_obs = len(X)

        model_preds = np.zeros((n_obs, self.n_models))
        for i, model in enumerate(self.models):
            model_preds[:,i] = model.classify(X)
        results = np.average(model_preds, axis=1, weights=self.weights)
        return results >= .5


class BaggingBinaryClassifier(EnsembleBinaryClassifier):
    bag_params_names = ('model_params', 'n_models_fit', 'seed')

    def __init__(self, binaryclassifiercls, model_params=None, n_models_fit=10,
                 seed=None):
        super(type(self), self).__init__()

        self.base_model = binaryclassifiercls
        if model_params is None:
            model_params = {}
        self.model_params = model_params
        self.n_models_fit = n_models_fit
        self.seed = seed

        self.obs_used = []
        self._oob_error = None
        self._oob_num = None

    @property
    def params(self):
        result = {}
        for name in self.bag_params_names:
            result[name] = getattr(self, name)
        return result

    @property
    def oob_error(self):
        if self._oob_error is None:
            raise AttributeError('Model has not been fitted yet.')
        return self._oob_error

    def fit(self, X, Y, oob_error=True):
        if oob_error:
            self._oob_error = 0
            self._oob_num = 0

        num_obs = len(X)
        for i in range(self.n_models_fit):
            curr_ind = np.random.choice(num_obs, num_obs)
            curr_X = X[curr_ind]
            curr_Y = Y[curr_ind]

            curr_model = self.base_model(**self.model_params)
            curr_model.fit(curr_X, curr_Y)
            self.add_model(curr_model)

            obs_used = np.unique(curr_ind)
            self.obs_used.append(obs_used)

            if oob_error:
                obs_not_used = np.setdiff1d(np.arange(num_obs), obs_used,
                                            assume_unique=True)
                curr_oob_error = np.mean(
                    curr_model.test_err(curr_X[obs_not_used],
                                        curr_Y[obs_not_used])
                )
                curr_oob_num = len(obs_not_used)

                self._oob_num += curr_oob_num
                self._oob_error = (self._oob_error*self._oob_num +
                                   curr_oob_error*curr_oob_num) / self._oob_num

        return self

