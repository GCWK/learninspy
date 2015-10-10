__author__ = 'leferrad'

import dnn.model as mod
from dnn.optimization import OptimizerParameters
import time
from utils.data import split_data, label_data
from dnn.evaluation import ClassificationMetrics
from context import sc

def parsePoint(line):
    values = [float(x) for x in line.split(';')]
    return values[-1], values[0:-1]

# TODO: incoportar posibilidad de admitir Ctrl+c sin perder todo el trabajo
parametros_red = mod.DeepLearningParams(units_layers=[230, 300, 20, 2], activation='Softplus',
                                        dropout_ratios=[0.5, 0.5, 0.0], classification=True)
parametros_opt = OptimizerParameters(algorithm='Adadelta', n_iterations=50)

redneuronal = mod.NeuralNetwork(parametros_red)

print "Cargando base de datos ..."
data = sc.textFile("/home/leeandro04/Documentos/Datos/EEG/P300-Disabled/datalabels_cat5_FIRDec_Norm.dat").map(parsePoint)
features = data.map(lambda (l,f): f).collect()
labels = data.map(lambda (l,f): l).collect()
print "Size de la data: ", len(features), " x ", len(features[0])

train, valid, test = split_data(label_data(features, labels), [.7, .2, .1])

print "Entrenando red neuronal ..."
t1 = time.time()
hits_valid = redneuronal.fit(train, valid, mini_batch=50, parallelism=4, epochs=5, optimizer_params=parametros_opt)
hits_test, predict = redneuronal.evaluate(test, predictions=True)
t1f = time.time() - t1

print 'Tiempo: ', t1f, 'Tasa de acierto final: ', hits_test

print "Metricas: "
labels = map(lambda lp: float(lp.label), test)
metrics = ClassificationMetrics(zip(predict, labels), 2)
print "Precision: ", metrics.precision()
print "Recall: ", metrics.recall()
print "Confusion: "
print metrics.confusion_matrix()




