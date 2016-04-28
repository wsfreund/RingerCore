__all__ = ['RawDictStreamable', 'RawDictStreamer', 'RawDictCnv', 'mangle_attr',
           'LoggerStreamable', 'LoggerRawDictStreamer', 'checkAttrOrSetDefault']

from RingerCore.Logger import Logger
from RingerCore.util import checkForUnusedVars

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

class RawDictStreamer( Logger ):
  """
  This is the default streamer class. Overload this method to deal with
  special cases.
  """

  def __init__(self, transientAttrs = set(), toPublicAttrs = set(), **kw):
    "Initialize streamer and declare transient variables."
    Logger.__init__(self, kw)
    self.transientAttrs = set(transientAttrs)
    self.toPublicAttrs = set(toPublicAttrs)
    checkForUnusedVars( kw, self._logger.warning )

  def __call__(self, obj):
    "Return a raw dict object from itself"
    from copy import deepcopy
    raw = { key : val for key, val in obj.__dict__.iteritems() if key not in self.transientAttrs }
    for searchKey in self.toPublicAttrs:
      publicKey = searchKey.lstrip('_')
      searchKey = mangle_attr(obj, searchKey)
      if searchKey in raw:
        self._logger.verbose( "Transforming '%s' attribute to public attribute '%s'.",
                              searchKey,
                              publicKey )
        raw[publicKey] = raw.pop(searchKey)
      else:
        raise KeyError("Cannot transform to public key attribute '%s'" % searchKey)
    for key, val in raw.iteritems():
      try:
        streamable = issubclass( val.__metaclass__, RawDictStreamable)
      except AttributeError:
        streamable = False
      if not hasattr(val, "__bases__"):
        cl = val.__class__
      else:
        cl = val
      if streamable or isinstance( cl, RawDictStreamable):
        self._logger.debug( "Found a streamable instance of type '%s' on attribute named '%s'.",
                            cl.__name__,
                            key )
        raw[key] = val.toRawObj()
    raw = deepcopy( raw )
    return self.treatDict( obj, raw )

  def treatDict(self, obj, raw):
    """
    Method dedicated to modifications on raw dictionary
    """
    raw['class'] = obj.__class__.__name__
    raw['__module'] = obj.__class__.__module__
    try:
      raw['__version'] = raw.pop('_version')
    except KeyError:
      raw['__version'] = obj.__class__._version
    return raw

def isRawDictFormat( d ):
  """
  Returns if dictionary is on streamed raw dictionary format.
  """
  isRawDictFormat = False
  if type(d) is dict and \
      all( baseAttr in d for baseAttr in RawDictCnv.baseAttrs ):
    isRawDictFormat = True
  return isRawDictFormat

class RawDictCnv( Logger ):
  """
  This is the default converter class. Overload this method to deal with
  special cases.
  """
  # FIXME: class should be __class. How to treat __class so that matlab can
  # read it as well?

  baseAttrs = {'class' , '__version', '__module'}

  def __init__(self, ignoreAttrs = set(), toProtectedAttrs = set(), **kw ):
    """
      Add ignoreAttrs to not considering the written dictionary values.
      Add toProtectedAttrs to change public attributes to protected or private
      attributes. That is, suppose the dictionary value is 'val' and the class
      value should be _val or __val, then add toProtectedAttrs = ['_val'] or
      '__val'.
    """
    Logger.__init__(self, kw)
    self.ignoreAttrs = set(ignoreAttrs) | RawDictCnv.baseAttrs
    self.toProtectedAttrs = set(toProtectedAttrs)
    checkForUnusedVars( kw, self._logger.warning )

  def _searchAttr(self, val):
    return [protectedAttr.lstrip('_') for protectedAttr in self.toProtectedAttrs].index(val)

  def __call__(self, obj, d):
    """
    Add information to python class from dictionary d
    """
    for k, val in d.iteritems():
      if k in self.ignoreAttrs: 
        continue
      try:
        nK = mangle_attr( self.__class__, 
                          list(self.toProtectedAttrs)[self._searchAttr(k)] 
                        )
        obj.__dict__[nK] = self.retrieveAttrVal( nK, d[k] )
        continue
      except ValueError:
        pass
      obj.__dict__[k] = self.retrieveAttrVal( k, d[k] )
    return self.treatObj( obj, d )

  def treatObj( self, obj, d ):
    """
    Overload this method to treat the python object
    """
    return obj

  def retrieveAttrVal( self, key, val ):
    """
    Transform contained values to their respective python classes if they are a
    raw dictionary.
    """
    if isRawDictFormat( val ):
      try:
        from RingerCore.util import str_to_class
        self._logger.debug( "Converting streamable instance of type '%s' on attribute named '%s'.",
                            val['class'],
                            key )
        cls = str_to_class( val['__module'], val['class'] )
        val = cls.fromRawObj( val )
      except KeyError,  e:
        self._logger.error("Couldn't convert attribute %s! Reason: %s", key, e)
    return val

import re
_lMethodSearch=re.compile("_RawDictStreamable__(\S+)")

def checkAttrOrSetDefault( key, dct, bases, defaultType ):
  """
  Check if class factory attribute exists and is a defaultType instance. 
  Otherwise set it to defaultType.
  """
  if not key in dct:
    dct[key] = defaultType()
    for base in bases:
      if key in base.__dict__:
        dct[key] = getattr(base,key)
  else:
    if not isinstance(dct[key], defaultType):
      if type(dct[key]) is type:
        dct[key] = dct[key]()
      if not isinstance(dct[key], defaultType):
        raise ValueError("%s must be a %s instance." % (key, defaultType.__name__,) )

class RawDictStreamable( type ):

  def __new__(cls, name, bases, dct):
    import inspect
    import sys
    for localFcnName, fcn in inspect.getmembers( sys.modules[__name__], \
        inspect.isfunction):
      m = _lMethodSearch.match(localFcnName)
      if m:
        fcnName = m.group(1)
        if not fcnName in dct:
          dct[fcnName] = fcn
    ## Take care to _streamerObj and _cnvObj be in the right specification
    checkAttrOrSetDefault( '_streamerObj', dct, bases, RawDictStreamer )
    checkAttrOrSetDefault( '_cnvObj',      dct, bases, RawDictCnv      )
    if not '_version' in dct:
      dct['_version'] = 0
    if not type(dct['_version']) is int:
      raise ValueError("_version must be declared as an int.")
    return type.__new__(cls, name, bases, dct)

  def fromRawObj(cls, obj):
		from copy import deepcopy
		obj = deepcopy( obj )
		self = cls().buildFromDict( obj )
		return self

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

LoggerStreamable = RawDictStreamable( 
                                      "LoggerStreamable", (Logger,), 
                                      { 
                                        '_version' : 1, 
                                        '_streamerObj' : LoggerRawDictStreamer,
                                      }
                                    )


