__all__ = ['StoreGate']
import sys
from RingerCore.Logger  import Logger, LoggingLevel

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
    self._file.Write()
    self._file.Close()

  #Create a folder
  def mkdir(self, theDir):
    fullpath = (theDir).replace('//','/')    
    if not fullpath in self._dirs:
      self._dirs.append( fullpath )
      self._file.mkdir(fullpath)
      self._file.cd(fullpath)
      self._currentDir = fullpath
      self._logger.verbose('Created directory with name %s', theDir)

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
      self._logger.debug('Saving object type %s into %s',type(obj), fullpath)
  
  def histogram(self, feature):
    #self._currentDir = ''
    self._file.cd()
    fullpath = (feature).replace('//','/')
    if fullpath in self._dirs:
      obj = self._objects[fullpath]
      self._logger.debug('Retrieving object type %s into %s',type(obj), fullpath)
      return obj
    else:
      #None object if doesnt exist into the store
      self._logger.warning('Object with path %s doesnt exist', fullpath)
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
        self._logger.fatal("Can not set the labels! abort.")
    else:
      self._logger.warning("Can not set the labels because this feature (%s) does not exist into the storage",feature)


  def collect(self):
    self._objects.clear()
    self._dirs = list()

  def getObjects(self):
    return self._objects

  def getDirs(self):
    return self._dirs





