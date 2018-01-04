__all__ = ['RawDictStreamable', 'RawDictStreamer', 'RawDictCnv', 'mangle_attr',
           'LoggerStreamable', 'LoggerRawDictStreamer', 'checkAttrOrSetDefault',
           'isRawDictFormat', 'retrieveRawDict', 'calculate_mro',
           'createClassStr', 'getClassStr', 'getModuleStr']

from RingerCore.Logger import Logger

mLogger = Logger.getModuleLogger( __name__ )

def calculate_mro(*bases):
  """Calculate the Method Resolution Order of bases using the C3 algorithm.

  Suppose you intended creating a class K with the given base classes. This
  function returns the MRO which K would have, *excluding* K itself (since
  it doesn't yet exist), as if you had actually created the class.

  Another way of looking at this, if you pass a single class K, this will
  return the linearization of K (the MRO of K, *including* itself).

  Taken from: http://code.activestate.com/recipes/577748-calculate-the-mro-of-a-class/
  """
  seqs = [list(C.__mro__) for C in bases] + [list(bases)]
  res = []
  while True:
    non_empty = list(filter(None, seqs))
    if not non_empty:
      # Nothing left to process, we're done.
      return tuple(res)
    for seq in non_empty:  # Find merge candidates among seq heads.
      candidate = seq[0]
      not_head = [s for s in non_empty if candidate in s[1:]]
      if not_head:
        # Reject the candidate.
        candidate = None
      else:
        break
    if not candidate:
      raise TypeError("inconsistent hierarchy, no C3 MRO is possible")
    res.append(candidate)
    for seq in non_empty:
      # Remove candidate.
      if seq[0] == candidate:
        del seq[0]

def mangle_attr(source, attr):
  """
  Simulate python private attritubutes mangling. Taken from:
  http://stackoverflow.com/a/7789483/1162884
  """
  # return public attrs unchanged
  if not attr.startswith("__") or attr.endswith("__") or '.' in attr:
    return attr
  # if source is an object, get the class
  if not hasattr(source, "__bases__"):
    source = source.__class__
  # mangle attr
  return "_%s%s" % (source.__name__.lstrip("_"), attr)

def createClassStr( c ):
  " Generates class name str to be used in the rawDict"
  return c.__module__ + '.' + c.__name__

def getClassStr( s ):
  return s.split('.')[1]

def getModuleStr( s ):
  return s.split('.')[0]

class RawDictStreamer( Logger ):
  """
  This is the default streamer class, responsible of converting python classes
  to raw dictionaries.
  """

  def __init__(self, transientAttrs = set(), toPublicAttrs = set(), **kw):
    "Initialize streamer and declare transient variables."
    Logger.__init__(self, kw)
    self.transientAttrs = set(transientAttrs) | {'_readVersion','_readVersionedClasses', '_cnvObj', '_streamerObj'}
    self.toPublicAttrs = set(toPublicAttrs)
    from RingerCore.Configure import checkForUnusedVars
    checkForUnusedVars( kw, self._logger.warning )

  def preCall(self, obj):
    "Overload this method if you want to make special treatments before streaming the object."
    pass

  def __call__(self, obj):
    "Return a raw dict object from itself"
    self.preCall(obj)
    raw = { key : val for key, val in obj.__dict__.iteritems() if key not in self.transientAttrs }
    for searchKey in self.toPublicAttrs:
      publicKey = searchKey.lstrip('_')
      searchKey = mangle_attr(obj, searchKey)
      if searchKey in raw:
        self._verbose( "Transforming '%s' attribute to public attribute '%s'.",
                              searchKey,
                              publicKey )
        raw[publicKey] = raw.pop(searchKey)
      else:
        self._fatal("Cannot transform to public key attribute '%s'", searchKey, KeyError)
    for key, val in raw.iteritems():
      try:
        streamable = issubclass( val.__metaclass__, RawDictStreamable)
      except AttributeError:
        streamable = False
      if not hasattr(val, "__bases__"):
        cl = val.__class__
        #bases = []
      else:
        cl = val
        #bases = val.__bases__
      if streamable or isinstance( cl, RawDictStreamable):
        self._verbose( "Found a streamable instance of type '%s' on attribute named '%s'."
                     , createClassStr(cl)
                     , key )
        raw[key] = val.toRawObj()
    #  else:
    #    self._verbose( "===== NOT Found a streamable instance of type '%s' + (%r) on attribute named '%s'."
    #                 , createClassStr(cl)
    #                 , bases
    #                 , key )
    from copy import copy
    raw = copy( raw )
    raw['class'] = obj.__class__.__name__
    raw['__module'] = obj.__class__.__module__
    raw['__versionedClasses'] = { createClassStr(c) : v for c, v in self._versionedClasses.iteritems() }
    return self.treatDict( obj, raw )

  def treatDict(self, obj, raw):
    """
    Method dedicated to modifications on raw dictionary
    """
    return raw

  def deepCopyKey(self, raw, key):
    """
    Helper method for deepcopying dict key.
    """
    if key in raw:
      from copy import deepcopy
      raw[key] = deepcopy(raw[key])
    else:
      self._warning("Cannot deepcopy key(%s) as it does not exists on rawDict.", key)

class RawDictCnv( Logger ):
  """
  This is the default converter class: it transforms raw dictionaries saved
  using RawDictStreamer into python classes.
  """
  # FIXME: class should be __class. How to treat __class so that matlab can
  # read it as well?

  _baseAttrs_v1 = {'class' , '__version', '__module'}
  baseAttrs = {'class' , '__versionedClasses', '__module'}

  def __init__(self, ignoreAttrs = set(), toProtectedAttrs = set(), ignoreRawChildren = False
                   , oldClasses = {}, **kw ):
    """
      -> ignoreAttrs: not consider this attributes on the dictionary values.
      -> toProtectedAttrs: change public attributes to protected or private
        attributes. That is, suppose the dictionary value is 'val' and the class
        value should be _val or __val, then add toProtectedAttrs = ['_val'] or
        '__val'.
      -> ignoreRawChildren: Do not attempt to conver raw children to higher level object.
      -> oldClasses: a dict where the keys are the name of the old classes and 
      the values are the names of the current name used for the same classes.
    """
    Logger.__init__(self, kw)
    ignoreAttrs = list(set(ignoreAttrs) | RawDictCnv.baseAttrs | RawDictCnv._baseAttrs_v1)
    import re
    self.ignoreAttrs = [re.compile(ignoreAttr) for ignoreAttr in ignoreAttrs]
    self.toProtectedAttrs = set(toProtectedAttrs)
    self.ignoreRawChildren = ignoreRawChildren
    self.oldClasses = { (c.__name__ if isinstance(c,type) else c ) : val for c, val in oldClasses.iteritems() }
    from RingerCore.Configure import checkForUnusedVars
    checkForUnusedVars( kw, self._logger.warning )

  def _searchAttr(self, val):
    return [protectedAttr.lstrip('_') for protectedAttr in self.toProtectedAttrs].index(val)

  def preCall(self, obj, d):
    """Overload this method if you want to make special treatments before
    streaming the object.

    _readVersionedClasses is not yet available at this method, it can be used
    to adjust ignoreAttr accordingly.
    """
    return obj, d

  def __call__(self, obj, d):
    """
    Add information to python class from dictionary d
    """
    obj, d = self.preCall(obj, d)
    if not '__versionedClasses' in d:
      try:
        # In the old way, all classes would increase their version together:
        readVersion = d['__version']
      except KeyError:
        readVersion = 0
      readVersionedClasses = { createClassStr(c) : readVersion for c in self._versionedClasses }
    else:
      readVersionedClasses = d['__versionedClasses']
      # Transform all old versioned classes name 
      for orig_cStr in readVersionedClasses:
        if orig_cStr in self.oldClasses:
          readVersionedClasses[self.oldClasses[orig_cStr]] = readVersionedClasses.pop(orig_cStr)
          continue
        cStr = getClassStr( orig_cStr )
        cMod = getModuleStr( orig_cStr )
        if cStr in self.oldClasses:
          readVersionedClasses[createClassStr( cMod, self.oldClasses[cStr])] = readVersionedClasses.pop(orig_cStr)
          continue
        # TODO Make self.oldModules and check whether we can match updating the module
    # Check whether all class versions are available:
    for c in self._versionedClasses:
      if not createClassStr(c) in readVersionedClasses:
        self._fatal("Couldn't find version for class %s", c.__name__)
    # Transform the string names to the classes and keep the read versions:
    obj._readVersionedClasses = { filter( lambda c: createClassStr(c) == clsStr, self._versionedClasses )[0] : v for clsStr, v in readVersionedClasses.iteritems() }
    # Read version 
    # Just in case user implements each cnv calling the child converter
    self._readVersion = obj._readVersionedClasses[ self._mainClass ]
    obj._readVersion = obj._readVersionedClasses[ type(obj) ]
    for k in d:
      if any([bool(ignoreAttr.match(k)) for ignoreAttr in self.ignoreAttrs]): 
        continue
      try:
        # We only load val if it is not in ignoredAttr
        val = d[k]
        nK = mangle_attr( self.__class__, 
                          list(self.toProtectedAttrs)[self._searchAttr(k)] 
                        )
        if not self.ignoreRawChildren:
          obj.__dict__[nK] = retrieveRawDict( val, logger = self._logger )
        else:
          obj.__dict__[nK] = val
        continue
      except ValueError:
        pass
      if not self.ignoreRawChildren:
        obj.__dict__[k] = retrieveRawDict( val, logger = self._logger )
      else:
        obj.__dict__[k] = val
    ret = self.treatObj( obj, d )
    return ret

  def treatObj( self, obj, d ):
    """
    Overload this method to treat the python object
    """
    return obj

  def __getstate__(self):
    """
      Makes logger invisible for pickle
    """
    odict = Logger.__getstate__(self)
    if 'ignoreAttrs' in odict:
      s = odict['ignoreAttrs']
      def getStr(c):
        try:
          return  c.pattern
        except AttributeError:
          return c
      odict['ignoreAttrs'] = [getStr(v) for v in s]
    return odict

  def __setstate__(self, d):
    """
      Add logger to object if it doesn't have one:
    """
    v = d.pop('ignoreAttrs')
    self.__dict__['ignoreAttrs'] = [re.compile(s) for s in v]
    Logger.__setstate__(self,d)


def isRawDictFormat( d ):
  """
  Returns if dictionary is on streamed raw dictionary format.
  """
  isRawDictFormat = False
  if type(d) is dict and all( baseAttr in d for baseAttr in RawDictCnv.baseAttrs ):
    isRawDictFormat = True
  elif type(d) is dict and all( baseAttr in d for baseAttr in RawDictCnv._baseAttrs_v1 ):
    isRawDictFormat = True
  return isRawDictFormat

def retrieveRawDict( val, logger = mLogger ):
  """
  Transform rawDict to an instance from its respective python class
  """
  if isRawDictFormat( val ):
    try:
      from RingerCore.util import str_to_class
      logger.verbose( "Converting rawDict to an instance of type '%s'." % val['class'] )
      # TODO Create a global dict with oldClasses and oldModules and evaluate
      # if val['__module'] or class are in global dict.
      cls = str_to_class( val['__module'], val['class'] )
      val = cls.fromRawObj( val )
    except KeyError, e:
      logger.error("Couldn't convert rawDict to an instance of type '%s'!\n Reason: %s", val['class'], e)
  return val

import re
_lMethodSearch=re.compile("_RawDictStreamable__(\S+)")

def checkAttrOrSetDefault( key, dct, bases, defaultType ):
  """
  Check if class factory attribute exists and is a defaultType instance. 
  Otherwise set it to defaultType.
  """
  from copy import deepcopy
  if not key in dct:
    dct[key] = defaultType()
    for base in bases:
      if key in base.__dict__:
        # We deep copy the converter and streamer. The idea is to 
        # have a unique bind to the converter and streamers but 
        # keeping any changes done to the default classes.
        # NOTE: Previous behavior was to always instantiate 
        # the default instance
        wantedAttr = getattr(base,key)
        dct[key] = deepcopy( wantedAttr )
        break
  else:
    if not isinstance(dct[key], defaultType):
      if type(dct[key]) is type:
        dct[key] = dct[key]()
  if not isinstance(dct[key], defaultType):
    raise ValueError("%s must be a %s instance." % (key, defaultType.__name__,) )

class RawDictStreamable( type ):
  """
  Class factory which adds streaming capability to python raw dictionary when
  using the _streamerObj attribute which should inherit from the
  RawDictStreamer class. When not specified, it is set to a standard
  RawDictStreamer instance.
  
  The dict can be transformed back into the python class using the _cnvObj
  attribute which must inherit from the RawDictCnv class. When not specified,
  it is set to a standard RawDictCnv instance.

  The version is specified using the _version attribute. Default value is 0.

  There is always only one _streamerObj and _cnvObj available, which is replaced
  by the nearest class following python MRO resolution. It is appended to these
  classes a list of all versioned (i.e.: classes contining _version attribute)
  base classes also following python MRO resolution.

  For legacy classes where only one version was saved, the attribute
  _fixUniqueVersion will allow to specify the desired behavior. When equal to
  -1, it will set the version equal to __version or _version, whatever
  available first. Otherwise, it will be set to the value available in that
  attribute. If it is not specified, then -1 behavior is assumed.
  """

  def __new__(meta, name, bases, dct):
    import inspect
    import sys
    for localFcnName, fcn in inspect.getmembers( sys.modules[__name__], inspect.isfunction):
      m = _lMethodSearch.match(localFcnName)
      if m:
        fcnName = m.group(1)
        if not fcnName in dct:
          dct[fcnName] = fcn
    mro = calculate_mro(*bases)
    checkAttrOrSetDefault( '_streamerObj', dct, mro, RawDictStreamer )
    checkAttrOrSetDefault( '_cnvObj',      dct, mro, RawDictCnv      )
    ## Take care to _streamerObj and _cnvObj be in the right specification
    if not '_version' in dct:
      dct['_version'] = 1
    if not type(dct['_version']) is int:
      raise ValueError("_version must be declared as an int.")
    return type.__new__(meta, name, bases, dct)

  def __init__(cls, name, bases, dct):
    # Bases mro:
    bmro = cls.mro()[1:]
    versionedClasses = { base : base._version for base in bmro if hasattr(base,'_version') }
    versionedClasses.update( { cls : dct['_version'] } )
    dct['_versionedClasses'] = versionedClasses
    # We overwrite previous streamers versionedClasses
    dct['_streamerObj']._versionedClasses = versionedClasses
    dct['_cnvObj']._versionedClasses = versionedClasses
    dct['_cnvObj']._mainClass = cls
    # Keep record of this class read version
    dct['_readVersionedClasses'] = None
    # A shortcut to self._readVersionedClasses[self]
    dct['_readVersion'] = None

  def fromRawObj(cls, obj, workOnCopy = False, **kw):
    """
      Builds an instance of this class using RawDict obj.
      -> workOnCopy: if set to false, it will change the input rawDict values,
      otherwise work on a deep copy.
      -> kw: Changes attributes from RawDictCnv object.
    """
    from copy import deepcopy
    if workOnCopy:
      obj = deepcopy( obj )
    self = cls()
    # NOTE: We always replace the cnvObj by the one available in the class to
    # ensure that it will behave as desired in case it is used to read an 
    # object twice, though this will probably very rarely (if ever) be used.
    self._cnvObj = deepcopy(cls._cnvObj)
    if kw:
      for key, val in kw.iteritems():
        setattr( self._cnvObj, key, val)
    self = self.buildFromDict( obj )
    # Delete instance specific converter
    if kw: del self._cnvObj
    return self

  def __hash__(cls):
    return hash('%r' % cls)

def _RawDictStreamable__toRawObj(self):
  "Return a raw dict object from itself"
  raw = self._streamerObj( self )
  return raw

def _RawDictStreamable__buildFromDict(self, d):
  self = self._cnvObj( self, d )
  return self

class LoggerRawDictStreamer(RawDictStreamer):
  """
  Deal logger object streaming. All streaming Logger objects should have
  _streamerObj inheriting from this class.
  """
  
  transientAttrs = {'_logger','_level'}

  def __init__(self, transientAttrs = set(), toPublicAttrs = set(), **kw):
    transientAttrs = set(transientAttrs) | LoggerRawDictStreamer.transientAttrs
    RawDictStreamer.__init__(self, transientAttrs, toPublicAttrs, **kw)

class LoggerStreamable( Logger ):
  """
  Logger class with RawDictStreamer capabilities.
  """
  __metaclass__ = RawDictStreamable
  _streamerObj = LoggerRawDictStreamer
  _version = 1

  def __init__(self, d = {}, **kw): 
    Logger.__init__(self, d, **kw)

