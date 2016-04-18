
__all__ = ['StoreGate']

from RingerCore.Logger  import Logger, LoggingLevel

class StoreGate(Logger):
  _currentDir = ""
  _objects    = dict()
  _dirs       = list()

  def __init__( self, outputFile, **kw ):
    
    Logger.__init__(self, kw)
    from ROOT import TFile
    self._outputFile = outputFile
    #Create TFile object to hold everything
    self._file = TFile( outputFile, "recreate")

  #Save objects and delete storegate
  def __del__(self):
    #self._file.Write()
    self._file.Close()

  #Create a folder
  def mkdir(self, theDir):
    fullpath = (theDir).replace('//','/')    
    if not fullpath in self._dirs:
      self._dirs.append( fullpath )
      self._file.mkdir(fullpath)
      self._file.cd(fullpath)
      self._currentDir = fullpath
      self._logger.debug('Created directory with name %s', theDir)

  #Go to the root base dir
  def root(self):
    self._currentDir = ''
    self._file.cd()

  #Go to the pointed directory
  def cd(self, theDir):
    self.root()
    fullpath = (theDir).replace('//','/')
    if fullpath in self._dirs:
      self._currentDir = fullpath
      self._file.cd(fullpath)

  def attach( self, obj ):
    feature = obj.GetName()
    fullpath = (self._currentDir + '/' + feature).replace('//','/')
    if not fullpath in self._dirs:
      self._dirs.append(fullpath)
      self._objects[fullpath] = obj
      obj.Write()
      self._logger.debug('Saving object type %s into %s',type(obj), fullpath)
  
  def retrieve(self, feature):
    fullpath = (self._currentDir + '/' + feature).replace('//','/')
    if fullpath in self._dirs:
      self._logger.debug('Retrieving object type %s into %s',type(obj), fullpath)
      return self._objects[fullpath]
    else:
      #None object if doesnt exist into the store
      self._logger.warning('Object with path %s doesnt exist.', fullpath)
      return None

  def getObjects(self):
    return self._objects

  def getDirs(self):
    return self._dirs


