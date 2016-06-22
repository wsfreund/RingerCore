
__all__ = ['StoreGate']

import sys

def progressbar(it, prefix="", size=60):
    count = len(it)
    def _show(_i):
        x = int(size*_i/count)
        sys.stdout.write("%s[%s%s] %i/%i\r" % (prefix, "#"*x, "."*(size-x), _i, count))
        sys.stdout.flush()

    _show(0)
    for i, item in enumerate(it):
        yield item
        _show(i+1)
    sys.stdout.write("\n")
    sys.stdout.flush()



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
    #Property
    self._holdObj = True


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
      self._logger.verbose('Created directory with name %s', theDir)

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

  def attach( self, obj, **kw ):
    hold = kw.pop('hold',True)
    feature = obj.GetName()
    fullpath = (self._currentDir + '/' + feature).replace('//','/')
    if not fullpath in self._dirs:
      self._dirs.append(fullpath)
      if self._holdObj:  self._objects[fullpath] = obj
      obj.Write()
      self._logger.verbose('Saving object type %s into %s',type(obj), fullpath)
  
  def retrieve(self, feature):
    if self._holdObj is False:
      self._logger.warning('There is no object in store, maybe you set holdObj to False after create the storegate. Dont \
          set this to store the object and enable the retrieve method')
      return None
    fullpath = (self._currentDir + '/' + feature).replace('//','/')
    if fullpath in self._dirs:
      self._logger.verbose('Retrieving object type %s into %s',type(obj), fullpath)
      return self._objects[fullpath]
    else:
      #None object if doesnt exist into the store
      self._logger.warning('Object with path %s doesnt exist', fullpath)
      return None

  def setProperty(self, **kw):
    self._holdObj = kw.pop('holdObj', True)
    del kw
    #Properties
    if self._holdObj is False:
      self._logger.warning('setProperty: holdObj is False, The storage will not hold the objects in the memory, retrieve method is not allow.')
    

  def collect(self):
    self._objects.clear()
    self._dirs = list()

  def getObjects(self):
    return self._objects

  def getDirs(self):
    return self._dirs





