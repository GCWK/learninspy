__author__ = 'leferrad'

# Dependencias externas
import numpy as np

# Dependencias internas
from neurons import LocalNeurons
from stops import criterion
from learninspy.utils.data import subsample

# Librerias de Python
import copy


class OptimizerParameters:
    def __init__(self, algorithm='Adadelta', options=None, stops=None,
                 merge_criter='w_avg', merge_goal='hits'):
        if options is None:  # Agrego valores por defecto
            if algorithm == 'Adadelta':
                options = {'step-rate': 1, 'decay': 0.99, 'momentum': 0.0, 'offset': 1e-8}
            elif algorithm == 'GD':
                options = {'step-rate': 1, 'momentum': 0.3, 'momentum_type': 'standart'}
        self.options = options
        self.algorithm = algorithm
        if stops is None:
            stops = [criterion['MaxIterations'](10),
                     criterion['AchieveTolerance'](0.99, key='hits')]
        self.stops = stops
        self.merge = {'criter': merge_criter, 'goal': merge_goal}



class Optimizer(object):
    """

    """

    def __init__(self, model, data, parameters=None):
        self.model = copy.copy(model)
        self.num_layers = model.num_layers
        self.data = data
        if parameters is None:
            parameters = OptimizerParameters()
        self.parameters = parameters
        self.cost = 0.0
        self.n_iter = 0
        self.hits = 0.0
        self.step_w = None
        self.step_b = None

    def _iterate(self):
        # Implementacion hecha en las clases que heredan
        yield

    def _update(self):
        #  Tener en cuenta que las correcciones son restas, por lo cual se cambia el signo
        self.step_w = [w * -1.0 for w in self.step_w]
        self.step_b = [b * -1.0 for b in self.step_b]
        self.model.update(self.step_w, self.step_b)

    def results(self):
        return {
            'model': self.model.list_layers,
            'hits': self.hits,
            'iterations': self.n_iter,
            'cost': self.cost
        }

    def __iter__(self):
        results = None
        for stop in self._iterate():
            results = self.results()
        yield results

    def check_stop(self, check_all=False):
        if check_all is True:
            stop = all(c(self.results()) for c in self.parameters.stops)
        else:
            stop = any(c(self.results()) for c in self.parameters.stops)
        return stop





class Adadelta(Optimizer):
    """Adadelta optimizer.
    https://github.com/BRML/climin/blob/master/climin/adadelta.py
    .. [zeiler2013adadelta] Zeiler, Matthew D.
       "ADADELTA: An adaptive learning rate method."
       arXiv preprint arXiv:1212.5701 (2012).
    """

    def __init__(self, model, data, parameters=None):
        """

        :param model: NeuralNetwork
        :param data: list of LabeledPoint
        :param parameters: OptimizerParameters
        :return:
        """
        super(Adadelta, self).__init__(model, data, parameters)
        self._init_acummulators()


    def _init_acummulators(self):
        """
        Inicializo acumuladores usados para la optimizacion
        :return:
        """
        self.gms_w = []
        self.gms_b = []
        self.sms_w = []
        self.sms_b = []
        self.step_w = []
        self.step_b = []
        for layer in self.model.list_layers:
            shape_w = layer.get_weights().shape
            shape_b = layer.get_bias().shape
            self.gms_w.append(LocalNeurons(np.zeros(shape_w), shape_w))
            self.gms_b.append(LocalNeurons(np.zeros(shape_b), shape_b))
            self.sms_w.append(LocalNeurons(np.zeros(shape_w), shape_w))
            self.sms_b.append(LocalNeurons(np.zeros(shape_b), shape_b))
            self.step_w.append(LocalNeurons(np.zeros(shape_w), shape_w))
            self.step_b.append(LocalNeurons(np.zeros(shape_b), shape_b))

    def _iterate(self):
        while self.check_stop() is False:
            d = self.parameters.options['decay']
            o = self.parameters.options['offset']  # offset
            m = self.parameters.options['momentum']
            sr = self.parameters.options['step-rate']
            # --- Entrenamiento ---
            for lp in self.data:  # Por cada LabeledPoint del conj de datos
                # 1) Computar el gradiente
                cost, (nabla_w, nabla_b) = self.model.cost(lp.features, lp.label)
                for l in xrange(self.num_layers):
                    # ADICIONAL: Aplico momentum y step-rate (ANTE LA DUDA, COMENTAR ESTAS LINEAS)
                    step1w = self.step_w[l] * m * sr
                    step1b = self.step_b[l] * m * sr
                    # 2) Acumular el gradiente
                    self.gms_w[l] = (self.gms_w[l] * d) + (nabla_w[l] ** 2) * (1 - d)
                    self.gms_b[l] = (self.gms_b[l] * d) + (nabla_b[l] ** 2) * (1 - d)
                    # 3) Computar actualizaciones
                    step2w = ((self.sms_w[l] + o) ** 0.5) / ((self.gms_w[l] + o) ** 0.5) * nabla_w[l] * sr
                    step2b = ((self.sms_b[l] + o) ** 0.5) / ((self.gms_b[l] + o) ** 0.5) * nabla_b[l] * sr
                    # 4) Acumular actualizaciones
                    self.step_w[l] = step1w + step2w
                    self.step_b[l] = step1b + step2b
                    self.sms_w[l] = (self.sms_w[l] * d) + (self.step_w[l] ** 2) * (1 - d)
                    self.sms_b[l] = (self.sms_b[l] * d) + (self.step_b[l] ** 2) * (1 - d)
                # 5) Aplicar actualizaciones a todas las capas
                self.cost = cost
                self._update()
            # --- Error de clasificacion---
            data = copy.deepcopy(self.data)
            self.hits = self.model.evaluate(data)
            self.n_iter += 1
            yield self.check_stop()


class GD(Optimizer):
    def __init__(self, model, data, parameters=None):
        super(GD, self).__init__(model, data, parameters)
        self._init_acummulators()

    def _init_acummulators(self):
        """
        Inicializo acumuladores usados para la optimizacion
        :return:
        """
        self.step_w = []
        self.step_b = []
        for layer in self.model.list_layers:
            shape_w = layer.get_weights().shape
            shape_b = layer.get_bias().shape
            self.step_w.append(LocalNeurons(np.zeros(shape_w), shape_w))
            self.step_b.append(LocalNeurons(np.zeros(shape_b), shape_b))

    def _iterate(self):
        while self.check_stop() is False:
            m = self.parameters.options['momentum']
            sr = self.parameters.options['step-rate']
            # --- Entrenamiento ---
            for lp in self.data:  # Por cada LabeledPoint del conj de datos
                for l in xrange(self.num_layers):
                    cost = 0.0
                    if self.parameters.options['momentum_type'] == 'standard':
                        # Computar el gradiente
                        cost, (nabla_w, nabla_b) = self.model.cost(lp.features, lp.label)
                        self.step_w[l] = nabla_w[l] * sr + self.step_w[l] * m
                        self.step_b[l] = nabla_b[l] * sr + self.step_b[l] * m
                    elif self.parameters.options['momentum_type'] == 'nesterov':
                        # TODO: terminar, pq no anda hasta ahora
                        big_jump_w = self.step_w[l] * m
                        big_jump_b = self.step_b[l] * m
                        #  Aplico primera correccion
                        self.step_w[l] = big_jump_w
                        self.step_b[l] = big_jump_b
                        self._update()
                        # Computar el gradiente
                        cost, (nabla_w, nabla_b) = self.model.cost(lp.features, lp.label)

                        correction_w = nabla_w[l] * sr
                        correction_b = nabla_b[l] * sr
                        #  Aplico segunda correccion
                        self.step_w[l] = correction_w
                        self.step_b[l] = correction_b
                        self._update()

                        #  Acumulo correcciones hechas
                        self.step_w[l] = big_jump_w + correction_w
                        self.step_b[l] = big_jump_b + correction_b

                # Aplicar actualizaciones a todas las capas
                self.cost = cost
                self._update()
            # --- Error de clasificacion---
            data = copy.deepcopy(self.data)
            self.hits = self.model.evaluate(data)
            self.n_iter += 1
            yield self.check_stop()

Minimizer = {'Adadelta': Adadelta, 'GD': GD}

# Funciones usadas en model


def optimize(model, data, mini_batch=50, params=None, seed=123):
    final = {
        'model': model.list_layers,
        'hits': 0.0,
        'epochs': 0,
        'cost': -1.0,
        'seed': seed
    }
    # TODO: modificar el batch cada tantas iteraciones (que no sea siempre el mismo)
    balanced = model.params.classification  # Bool que indica que se balanceen clases (problema de clasificacion)
    batch = subsample(data, mini_batch, balanced, seed)  # Se balancea si se trata con clases
    minimizer = Minimizer[params.algorithm](model, batch, params)
    # TODO: OJO que al ser un iterator, result vuelve a iterar cada vez
    # que se hace una accion desde la funcion 'train' (solucionado con .cache() para que no se vuelva a lanzar la task)
    for result in minimizer:
        final = result
        print 'Cant de iteraciones: ' + str(result['iterations']) +\
              '. Hits en batch: ' + str(result['hits']) + \
              '. Costo: ' + str(result['cost'])
    final['seed'] = seed
    return final


def mix_models(left, right):
    """
    Se devuelve el resultado de sumar las NeuralLayers
    de left y right
    :param left: list of NeuralLayer
    :param right: list of NeuralLayer
    :return: list of NeuralLayer
    """
    for l in xrange(len(left)):
        w = right[l].get_weights()
        b = right[l].get_bias()
        left[l].update(w, b)  # Update suma el w y el b
    return left


def merge_models(results_rdd, criter='w_avg', goal='hits'):
    """
    Funcion para hacer merge de modelos, en base a un criterio de ponderacion sobre un valor objetivo
    :param results_rdd:
    :param criter:
    :param goal:
    :return:
    """
    assert goal == 'hits' or goal == 'cost', "Solo se puede ponderar por hits o cost!"
    if criter == 'avg':
        # Promedio sin ponderacion
        merge_fun = lambda res: [layer for layer in res['model']]
        weights = lambda res: 1
    elif criter == 'w_avg':
        # Promedio con ponderacion lineal
        # TODO: y si todas las tasas son 0.0 ?? se divide por 0?!
        merge_fun = lambda res: [layer * res[goal] for layer in res['model']]
        weights = lambda res: res[goal]
    elif criter == 'log_avg':
        # Promedio con ponderacion logaritmica
        merge_fun = lambda res: [layer * (1.0 + np.log(res[goal])) for layer in res['model']]
        weights = lambda res: (1.0 +np.log(res[goal]))
    else:
        raise ValueError('No existe tal criterio para merge!')
    # Mezclo modelos con la funcion de merge definida
    layers = (results_rdd.map(merge_fun).reduce(lambda left, right: mix_models(left, right)))
    total = results_rdd.map(weights).sum()
    # Promedio sobre todas las capas
    final_list_layers = map(lambda layer: layer / total, layers)
    return final_list_layers