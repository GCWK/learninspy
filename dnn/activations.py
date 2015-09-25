__author__ = 'leferrad'


import numpy as np

#TODO plotear en una parte del notebook la funcion de activacion elegida
#TODO cambiar nombre de ReLU a rectifier ? ya que me refiero a la funcion, no a la unidad

def tanh(x):
    return np.tanh(x)


def tanh_d(x):
    return 1.0 - np.tanh(x) ** 2


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def sigmoid_d(x):
    return sigmoid(x) * (1.0 - sigmoid(x))


def relu(x):
    if isinstance(x, np.ndarray) or type(x) == list:
        x = x[0]
    return max(0.0, x)


def relu_d(x):
    if x > 0.0:
        ret = 1.0
    else:
        ret = 0.0
    return ret


def lrelu(x):
    if x > 0.0:
        ret = x
    else:
        ret = 0.01 * x
    return ret

def lrelu_d(x):
    if x > 0.0:
        ret = 1
    else:
        ret = 0.01
    return ret


def softplus(x):
    return np.log(1.0 + np.exp(x))


def softplus_d(x):
    return sigmoid(x)


def identity(x):
    return x


def identity_d(x):
    return 1


def sin(x):
    return np.sin(x)


def sin_d(x):
    return np.cos(x)


fun_activation = {'Tanh': tanh, 'Sigmoid': sigmoid, 'ReLU': relu, 'Softplus': softplus,
                                'Identity': identity, 'Sin': sin, 'LeakyReLU': lrelu}
fun_activation_d = {'Tanh': tanh_d, 'Sigmoid': sigmoid_d, 'ReLU': relu_d, 'Softplus': softplus_d,
                                    'Identity': identity_d, 'Sin': sin_d, 'LeakyReLU': lrelu_d}





