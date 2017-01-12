__all__ = ['StoreGate']
import sys
from RingerCore.Logger  import Logger, LoggingLevel
import numpy as np

class StoreGate( Logger) :

  def __init__( self, outputFile, **kw ):
    Logger.__init__(self, kw)
    if not outputFile.endswith('.root'):
      outputFile += '.root'
    #Create TFile object to hold everything
    from ROOT import TFile
    self._file = TFile( outputFile, "recreate")
    self._currentDir = ""
    self._objects    = dict()
    self._dirs       = list()

  #Save objects and delete storegate
  def __del__(self):
    self._file.Close()

  def write(self):
    self._file.Write()

  #Create a folder
  def mkdir(self, theDir):
    fullpath = (theDir).replace('//','/')    
    if not fullpath in self._dirs:
      self._dirs.append( fullpath )
      self._file.mkdir(fullpath)
      self._file.cd(fullpath)
      self._currentDir = fullpath
      self._verbose('Created directory with name %s', theDir)

  #Go to the pointed directory
  def cd(self, theDir):
    self._currentDir = ''
    self._file.cd()
    fullpath = (theDir).replace('//','/')
    if fullpath in self._dirs:
      self._currentDir = fullpath
      self._file.cd(fullpath)

  def addHistogram( self, obj ):
    feature = obj.GetName()
    fullpath = (self._currentDir + '/' + feature).replace('//','/')
    if not fullpath in self._dirs:
      self._dirs.append(fullpath)
      self._objects[fullpath] = obj
      #obj.Write()
      self._debug('Saving object type %s into %s',type(obj), fullpath)
  
  def histogram(self, feature):
    #self._currentDir = ''
    self._file.cd()
    fullpath = (feature).replace('//','/')
    if fullpath in self._dirs:
      obj = self._objects[fullpath]
      self._verbose('Retrieving object type %s into %s',type(obj), fullpath)
      return obj
    else:
      #None object if doesnt exist into the store
      self._warning('Object with path %s doesnt exist', fullpath)
      return None

  # Use this to set labels into the histogram
  def setLabels(self, feature, labels):
    histo = self.histogram(feature)
    if not histo is None:
      try:
	      if ( len(labels)>0 ):
	        for i in range( min( len(labels), histo.GetNbinsX() ) ):
	          bin = i+1;  histo.GetXaxis().SetBinLabel(bin, labels[i])
	        for i in range( histo.GetNbinsX(), min( len(labels), histo.GetNbinsX()+histo.GetNbinsY() ) ):
	          bin = i+1-histo.GetNbinsX();  histo.GetYaxis().SetBinLabel(bin, labels[i])
      except:
        self._fatal("Can not set the labels! abort.")
    else:
      self._warning("Can not set the labels because this feature (%s) does not exist into the storage",feature)


  def histogram_FillN1(self,feature, value1):
    try:
      if value1.shape[1] > value1.shape[0]:
        np_array_value1 = np.array(value1.T)
      else:
        np_array_value1 = np.array(value1)
      weights = np.ones(np_array_value1.shape)
      self.histogram(feature).FillN(np_array_value1.shape[0],np_array_value1,weights)
    except:
      self._warning("Can not attach the vector into the feature: %s", feature)


  def histogram_FillN2(self,feature, value1, value2):
    try:
      np_array_value1 = np.array(value1).astype('float')
      np_array_value2 = np.array(value2).astype('float')
      if np_array_value1.shape[1] > np_array_value1.shape[0]:
        np_arrar_value1=np_array_value1.T
      if np_array_value2.shape[1] > np_array_value2.shape[0]:
        np_arrar_value2=np_array_value2.T
      if np_array_value1.shape[0] != np_array_value2.shape[0]:
        self._warning('Value1 and Value2 must be the same length.')
      else:
        # do fast
        weights = np.ones(np_array_value1.shape).astype('float')
        self.histogram(feature).FillN(np_array_value1.shape[0],np_array_value1,np_array_value2,weights)
    except:
      self._warning("Can not attach the vector into the feature: %s", feature)

  def collect(self):
    self._objects.clear()
    self._dirs = list()

  def getObjects(self):
    return self._objects

  def getDirs(self):
    return self._dirs






