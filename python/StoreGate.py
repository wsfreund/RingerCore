__all__ = ['StoreGate','restoreStoreGate']
import sys
from RingerCore  import Logger, LoggingLevel, retrieve_kw
import numpy as np


class StoreGate( Logger) :

  def __init__( self, outputFile, **kw ):
    Logger.__init__(self,kw)
    if not outputFile.endswith('.root'):
      outputFile += '.root'
    # Use this property to rebuild the storegate from a root file
    restoreStoreGate=retrieve_kw(kw,'restoreStoreGate',False)
    #Create TFile object to hold everything
    from ROOT import TFile
    if restoreStoreGate:
      self._file = TFile( outputFile, "read")
    else:
      self._file = TFile( outputFile, "recreate")
    
    self._currentDir = ""
    self._objects    = dict()
    self._dirs       = list()
    import os
    self._outputFile = os.path.abspath(outputFile)

    if restoreStoreGate:
      retrievedObjs = self.__restore(self._file)
      for name, obj in retrievedObjs:
        self._dirs.append(name)
        self._objects[name]=obj

  def local(self):
    return self._outputFile

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
      if self._file.cd(fullpath):
        return True
    self._error("Couldn't cd to folder %s", fullpath)
    return False


  def addHistogram( self, obj ):
    feature = obj.GetName()
    fullpath = (self._currentDir + '/' + feature).replace('//','/')
    if not fullpath.startswith('/'):
      fullpath='/'+fullpath
    if not fullpath in self._dirs:
      self._dirs.append(fullpath)
      self._objects[fullpath] = obj
      #obj.Write()
      self._debug('Saving object type %s into %s',type(obj), fullpath)
  
  def histogram(self, feature):
    #self._currentDir = ''
    self._file.cd()
    fullpath = (feature).replace('//','/')
    if not fullpath.startswith('/'):
      fullpath='/'+fullpath
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

  def collect(self):
    self._objects.clear()
    self._dirs = list()

  def getObjects(self):
    return self._objects

  def getDirs(self):
    return self._dirs

# Use this method to retrieve the dirname and root object
  def __restore(self,d, basepath="/"):
    """
    Generator function to recurse into a ROOT file/dir and yield (path, obj) pairs
    Taken from: https://root.cern.ch/phpBB3/viewtopic.php?t=11049
    """
    try:
      for key in d.GetListOfKeys():
        kname = key.GetName()
        if key.IsFolder():
          for i in self.__restore(d.Get(kname), basepath+kname+"/"):
            yield i
        else:
          yield basepath+kname, d.Get(kname)
    except AttributeError, e:
      self._logger.debug("Ignore reading object of type %s.",type(d))



# helper function to retrieve the storegate using
# a root file as base.
def restoreStoreGate( ifile ):
  return StoreGate( ifile, restoreStoreGate=True )


