import os
import itertools
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import logging, coloredlogs

#from sklearn.cluster import KMeans
from sklearn import mixture
from sklearn import preprocessing
from collections import OrderedDict
from sklearn import metrics
from datetime import datetime

# create logger with 'spam_application'
log = logging.getLogger("["+os.path.basename(__file__)+"] ")
log.setLevel(logging.DEBUG)

prettyFormatter = coloredlogs.ColoredFormatter(fmt='%(asctime)s [[%(filename)s | %(lineno)s]] %(levelname)s - %(message)s', datefmt="%H:%M:%S")
plainFormatter = logging.Formatter('%(asctime)s [[%(filename)s | %(lineno)s]] %(levelname)s - %(message)s', '%H:%M:%S')
TQDM_DISABLE=False

h = logging.StreamHandler()
h.setLevel(logging.INFO)
h.setFormatter(prettyFormatter)
log.addHandler(h)

histlen_MAX = 4

# feature set
# 1: default (RTT and IAT)
# 2: only RTT
#fset = '1'

# threshold for 0/1
thres = 0.5

#TrafficRates = ['620']
#TrafficRates = ['620-680']
#TrafficRates = ['100', '200', '300', '400', '500', '600', '700', '800', '900', '1000']
#TrafficRates = ['100-1000']
TrafficRates = ['1000']

# averaging window size
#Npkts = [1, 10, 50]
#Npkts = [1, 10]
Npkts = [1]

# relative weight between RTT and IAT
#Weights = np.arange(.1, 1.0, .2)

# weights over [RTT, IAT1, delay, IAT2]
# Weights = [(1, 1, 1, 1),
#            (1, 1, 1, 0),
#            (1, 1, 0, 1),
#            (1, 0, 1, 1),
#            (0, 1, 1, 1),
#            (1, 0, 1, 0),
#            (0, 1, 0, 1),
#            (1, 0, 0, 1)]
Weights = [(1, 1)]

# datasets2 folder is for recording capacity
inFolder = './datasets'
outFolder = './results'
saveFolder = os.path.join(outFolder, 'clustering_{}'.format(datetime.now().strftime('%Y%m%d%H%M')))
if os.path.exists(saveFolder):
  raise Exception('Save path {} already exists! Rename it and run again.'.format(saveFolder))

os.makedirs(saveFolder)

#emulTime = 50
emulTime = 60

# for outlier removal (INF means no removal at all)
#sigmas = [1, 2, 3, np.inf]
sigmas = [np.inf]

# for selecting the input files
#spikes = [5, 10]
spikes = [1]
traces = [
  {
    'name': 'fanrunning',
    'ql': 400000
  }
]
# traces = [
#   # {
#   #   'name': 'fanrunning',
#   #   'ql': 400000
#   # }, 
#   # {
#   #   'name': 'stationary',
#   #   'ql': 500000
#   # }, 
#   {
#     'name' : 'humanmotion',
#     'ql' : 300000
#   },
#   {
#     'name' : 'walkandturn',
#     'ql' : 500000
#   }
# ]

random_state = 1

#kmeans_cluster = KMeans(n_clusters=2, random_state=random_state)

def FindOutliers (data, m = 1): 
  ncols = len(data[0]) 
  f_std = []
  f_mean = []
  for i in range(0, ncols):
    f_std.append(np.std(data[:, i]))
    f_mean.append(np.mean(data[:, i]))
  rms = []
  for i in range(0, len(data)):
    if (sum(abs(data[i, :]- f_mean) > m*np.asarray(f_std)) > 0):
      rms.append(i)
  return rms

def MinMaxScale (dataset) :
  scaler = preprocessing.MinMaxScaler()
  dataset = scaler.fit_transform(dataset)
  return dataset

def ScaleFeatures (data, ws):
  rows, cols = data.shape
  for i in range(cols):
    data[:, i] *= ws[i]
  return data  


def FilterData (X, Y, Cap, m = 1): 
#def FilterData (X, Y, m = 1):
  outliers = FindOutliers(X, m)
  X = np.delete(X, outliers, 0)
  Y = np.delete(Y, outliers, 0)
  Cap = np.delete(Cap, outliers, 0)
  return X, Y, Cap
  #return X, Y


def ShapeData (X, ws): 
  X = MinMaxScale(X)
  #X = preprocessing.normalize(X, norm='l2', axis=0)
  X = ScaleFeatures(X, ws)
  return X

def GetData (traceName, ql, trrate, sp, npkts):
  # suffix = 'dataset_H04_{}_udp_file_{}-mbps-poisson+spikes-{}-10-T-{}-seed-0_q{}'.format(traceName, trrate, sp, emulTime, ql)
  # dpath = inFolder + '/' + suffix + '_uplink.csv'
  #suffix = 'dataset_H04_{}_bint-{}_{}_t={}_ECN2'.format(traceName, sp, trrate, emulTime) 
  #suffix = 'dataset_H04_{}_bint{}_q{}_T{}_qfrac'.format(traceName, sp, ql, emulTime)

  #suffix = 'dataset_H04_{}_{}mbps_bint{}_q{}_T{}_qfrac'.format(traceName, trrate, sp, ql, emulTime)
  suffix = 'dataset_H04_{}_make_dataset_out'.format(traceName)
  dpath = inFolder + '/' + suffix + '.csv'
  
  log.info ('Opening "{}"'.format(dpath) )
  #dataset = np.genfromtxt(dpath, delimiter=',', skip_header=1, missing_values="", filling_values=0.0)
  #dataset = np.loadtxt(dpath, delimiter=',', skiprows=1)#, max_rows=1e4)
  dataset = pd.read_csv(dpath)
  dataset.dropna(inplace=True)
  #X = dataset[:, [0,1,3,4,6,7,9,10,12,13]]
  #Y = dataset[:, 14]
  #Cap = dataset[:, 15]
  dataset.loc[:,['IAT1_tminus4', 'IAT1_tminus3', 'IAT1_tminus2', 'IAT1_tminus1', 'IAT1_tminus0']] /= 1e6
  X = dataset[['RTT_tminus4', 'IAT1_tminus4', 
               'RTT_tminus3', 'IAT1_tminus3', 
               'RTT_tminus2', 'IAT1_tminus2',
               'RTT_tminus1', 'IAT1_tminus1', 
               'RTT_tminus0', 'IAT1_tminus0']].values
  #Y = (dataset['Qfrac_tminus0'].values > thres)
  Y = (dataset['QfracCap_tminus0'].values > thres)
  Cap = dataset['Cap_tminus0'].values
  
  if npkts > 1:
    Yaux = []
    Xaux = []
    Capaux = []
    
    i = 0
    while i < len(Y):
      end = i + npkts
      if i + end > len(Y):
        end = len(Y)
      newY = 0
      if np.sum(Y[i:end]) >= 1: #0.1*npkts:   
        newY = 1
      Xaux.append(X[i:end,:].max(axis=0).tolist()) # changed max to mean, makes more sense now 
      Yaux.append(newY)
      Capaux.append(Cap[i:end].mean())
      i = i + 1             # changed it from i = i + 1, samples should probably be independent

    Xaux = np.asarray(Xaux)
    Yaux = np.asarray(Yaux)
    Capaux = np.asarray(Capaux)
  else:
    Yaux = Y
    Xaux = X
    Capaux = Cap
  
  # exponentiation transformation
  Xaux = np.exp(Xaux)
  
  #return np.asarray(Xaux), np.asarray(Yaux), np.asarray(Capaux)
  #return np.asarray(Xaux), np.asarray(Yaux)
  return Xaux, Yaux, Capaux


def FixLegendEntries (plt) : 
  handles, labels = plt.gca().get_legend_handles_labels()
  by_label = OrderedDict(zip(labels, handles))
  plt.legend(by_label.values(), by_label.keys())

def PlotScat (cm, non_cm):
  fig, ax = plt.subplots(1,1)
  fig.set_figheight(3)
  fig.set_figwidth(8)
  ax.scatter(non_cm[:,0], non_cm[:,1], label="Non Congestion")
  ax.scatter(cm[:,0], cm[:,1], label="Congestion")
  ax.legend(numpoints=1)
  ax.set_xlabel("IAT")
  ax.set_ylabel("Delay")
  FixLegendEntries(plt)
  fig.tight_layout()
  plt.grid()
  plt.show()

def ChooseLabel (y_pred, Y):
  y_pred_inv = np.logical_not(y_pred)
  asIs = float(sum(y_pred==Y))/len(Y)
  inv = float(sum(y_pred_inv==Y))/len(Y)
  if (inv > asIs): 
    return y_pred_inv
  return y_pred


def DoCluster (name, ql, sp, npkts):
  
  featuresS = np.asarray(['RTT-4', 'IAT1-4',
                          'RTT-3', 'IAT1-3', 
                          'RTT-2', 'IAT1-2',
                          'RTT-1', 'IAT1-1',
                          'RTT-0', 'IAT1-0'])
  
  for trIdx in range(len(TrafficRates)):
    X, Y, Cap  = GetData(name, ql, TrafficRates[trIdx], sp, npkts)
    #X, Y = GetData(name, ql, TrafficRates[trIdx], sp, npkts)
    for fset, w in enumerate(Weights):
      #wss = np.tile([w, 1-w], 5)
      wss = np.tile(w, histlen_MAX+1)
      for h in range(histlen_MAX+1):
      #for h in [histlen_MAX]:
        # if fset == '1':
        #   cols = range(8-4*(h), 20)
        # elif fset == '2':
        #   cols = range(8-4*(h), 20, 2) # using only sender size info
        # else:
        #   raise Exception('fset needs to be \'1\' or \'2\' only')
        cols = wss.astype(bool)
        # henry: I believe this ought be a function of the number of parameters in weights
        # was not working when hard coded as 4 * ...
        params_in_weights = len(Weights[0])
        cols[:params_in_weights*(histlen_MAX - h)] = False
        features = featuresS[cols]
        ws = wss[cols].astype(float)
        ws /= ws.sum()
        #print(ws)
        data = X[:,cols]
        
        for sigma in reversed(sigmas):
          
          log.info ("=== Trace {} Spikes {} Pkts {} --- Rate {} Weight {} History {} SigmaFactor {} ===".format(name, sp, npkts, TrafficRates[trIdx], w, h, sigma))
          
          s = 'INF' if np.isinf(sigma) else str(sigma)

          data, auxY, auxCap = FilterData (data, Y, Cap, sigma)
          #data, auxY = FilterData (data, Y, sigma)

          data = ShapeData (data, ws)  

          model = mixture.GaussianMixture(n_components=2, verbose=1)
          #kmeans = kmeans_cluster.fit(data)
          #y_pred = kmeans.labels_
          model.fit(data)
          y_pred = model.predict(data)
          y_pred = ChooseLabel(y_pred, auxY)
          report = metrics.classification_report(auxY, y_pred, labels=[0,1], target_names=['No congestion', 'Congestion'])
          print(report)
          
          #savesuffix = 'fset{}_thres{}_H{}_{}_bint{:02d}_tr{}_w{}_pkt{:02d}_s{}'.format(fset, int(thres*10), h, name, sp, TrafficRates[trIdx], int(w*10), npkts, s)
          savesuffix = 'fset{}_thres{}_H{}_{}_bint{:02d}_tr{}_pkt{:02d}_s{}'.format(fset, int(thres*10), h, name, sp, TrafficRates[trIdx], npkts, s)
          
          with open(os.path.join(saveFolder, 'labels_{}.csv'.format(savesuffix)), 'w') as fout:
            print('True,Predicted,Capacity', file=fout)
            np.savetxt(fout, np.hstack((np.vstack(auxY), np.vstack(y_pred), np.vstack(auxCap))), delimiter=',', fmt=['%.0f', '%.0f', '%f'])
            #print('True Predicted', file=fout)
            #np.savetxt(fout, np.hstack((np.vstack(auxY), np.vstack(y_pred))), fmt=['%.0f', '%.0f'])
          
          with open(os.path.join(saveFolder, 'centroids_{}.csv'.format(savesuffix)), 'w') as fout:
            print(','.join(features), file=fout)
            np.savetxt(fout, model.means_, delimiter=',', fmt='%f')
            #np.savetxt(fout, kmeans.cluster_centers_, delimiter=',', fmt='%f')
          
          # only for GMMs: save the covariance matrices as well
          with open(os.path.join(saveFolder, 'covariances_{}.csv'.format(savesuffix)), 'w') as fout:
            for mat in model.covariances_:
              np.savetxt(fout, mat, fmt='%f')
              fout.write(os.linesep)
          
          with open(os.path.join(saveFolder, 'finaldata_{}.csv'.format(savesuffix)), 'w') as fout:
            np.savetxt(fout, features, delimiter=',', fmt='%s')
            print(','.join(features), file=fout)
            np.savetxt(fout, data, delimiter=',', fmt='%f')
          
          with open(os.path.join(saveFolder, 'report_{}.txt'.format(savesuffix)), 'w') as fout:
            print(report, file=fout)
      
  return


if __name__ == '__main__':
  for tr, sp, npkts in itertools.product(traces, spikes, Npkts):
    print("trace = {}; queue length = {}; sp = {};". format(tr['name'], tr['ql'], sp))
    DoCluster(tr['name'], tr['ql'], sp, npkts)
