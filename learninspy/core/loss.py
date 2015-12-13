__author__ = 'leferrad'

# Dependencias externas
import numpy as np

# Dependencias internas
from learninspy.utils.data import label_to_vector

# Se define la funcion de error 'fun(x)' y su derivada respecto a x 'fun_d(x)'

def mse(value, target):
    err = np.array(map(lambda(y, t): y - t, zip(value, target)))
    N = err.size
    return np.sum(np.square(err)) / (1.0 * N)


def mse_d(value, target):
    err = np.array(map(lambda (y, t): y - t, zip(value, target)))
    N = err.size
    return 2 * err / (1.0 * N)


def cross_entropy(y, t):
    num_classes = len(y)
    t = label_to_vector(t, num_classes)
    return -sum(t * np.log(y))[0]


def cross_entropy_d(y, t):
    num_classes = len(y)
    t = label_to_vector(t, num_classes)
    return y - t


fun_loss = {'MSE': mse, 'CrossEntropy': cross_entropy}
fun_loss_d = {'MSE': mse_d, 'CrossEntropy': cross_entropy_d}