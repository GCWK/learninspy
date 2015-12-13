__author__ = 'leferrad'

import time

from learninspy.core.model import NetworkParameters, NeuralNetwork
from learninspy.core.optimization import OptimizerParameters
from learninspy.core.stops import criterion
from learninspy.utils.data import StandardScaler, LabeledDataSet
from learninspy.utils.evaluation import ClassificationMetrics
from learninspy.utils.feature import PCA

print "Cargando base de datos ..."
# Uso clase hecha para manejo de DataSet (almacena en RDD)
dataset = LabeledDataSet()
dataset.load_file("/media/leeandro04/Data/Downloads/P300-MMSPG/p300soft/datalabels_S1_dec.dat")
rows = dataset.data.count()
cols = len(dataset.features.take(1)[0].toArray())
print "Size de data: ", rows, " x ", cols

train, valid, test = dataset.split_data([.7, .2, .1])  # Particiono conjuntos

"""
# Aplico PCA
pca = PCA(train)
train = pca.transform()
valid = pca.transform(data=valid)
test = pca.transform(data=test)
k = pca.k
"""
# Standarize data
std = StandardScaler()
std.fit(train)
train = std.transform(train)
valid = std.transform(valid)
test = std.transform(test)

# Seleccion de parametros para la construccion de red neuronal
net_params = NetworkParameters(units_layers=[205, 100, 50, 20, 3], activation='Tanh',
                                dropout_ratios=[0.2, 0.5, 0.5, 0.0], classification=True)
neural_net = NeuralNetwork(net_params)

# Seleccion de parametros de optimizacion
local_stops = [criterion['MaxIterations'](10),
               criterion['AchieveTolerance'](0.90, key='hits')]

global_stops = [criterion['MaxIterations'](50),
                criterion['AchieveTolerance'](0.95, key='hits')]

opt_params = OptimizerParameters(algorithm='Adadelta', stops=local_stops, merge_criter='log_avg')

print "Entrenando red neuronal ..."
t1 = time.time()
hits_valid = neural_net.fit(train, valid, mini_batch=200, parallelism=4, stops=global_stops,
                            optimizer_params=opt_params, keep_best=True)
t1f = time.time() - t1

# Resultados
test = test.collect()
hits_test, predict = neural_net.evaluate(test, predictions=True)
print 'Tiempo: ', t1f, 'Tasa de acierto final: ', hits_test

print "Metricas: "
labels = map(lambda lp: float(lp.label), test)
metrics = ClassificationMetrics(zip(predict, labels), 2)
print "Precision: ", metrics.precision()
print "Recall: ", metrics.recall()
print "Confusion: "
print metrics.confusion_matrix()




