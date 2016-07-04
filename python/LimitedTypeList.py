__all__ = ['LimitedTypeList', 'LimitedTypeStreamableList', 'NotAllowedType',
           'LimitedTypeListRDC', 'LimitedTypeListRDS', 'LoggerLimitedTypeListRDS',
           'inspect_list_attrs']

import re
_lMethodSearch=re.compile("_LimitedTypeList__(\S+)")

class LimitedTypeList (type):
  """
    LimitedTypeList metaclass create lists which only accept declared types.

    One LimitedTypeList class must specify _acceptedTypes property as a tuple,
    which will be the only types accepted by the list.
  """

  # TODO Add boolean to flag if the class can hold itself

  def __new__(cls, name, bases, dct):
    if not list in bases:
      bases = (list,) + bases 
    import inspect
    import sys
    for localFcnName, fcn in inspect.getmembers( sys.modules[__name__], \
        inspect.isfunction):
      m = _lMethodSearch.match(localFcnName)
      if m:
        fcnName = m.group(1)
        if not fcnName in dct:
          dct[fcnName] = fcn
    return type.__new__(cls, name, bases, dct)

  def __init__(cls, name, bases, dct):
    ## Take care to _acceptedTypes be in the right specification
    if not '_acceptedTypes' in dct:
      raise TypeError("Cannot create a LimitedTypeList without a list of "
          "accepted types defined by _acceptedTypes.")
    if not type(dct['_acceptedTypes']) is tuple:
      raise ValueError("_acceptedTypes must be declared as a tuple.")
    if not dct['_acceptedTypes']:
      raise ValueError("_acceptedTypes cannot be empty.")
    return type.__init__(cls, name, bases, dct)

  def __call__(cls, *args, **kw):
    return type.__call__(cls, *args, **kw)


def _LimitedTypeList__setitem(self, k, var):
  """
    Default override setitem
  """
  # This is default overload for list setitem, checking if item is accepted
  if not isinstance(var, self._acceptedTypes):
    raise NotAllowedType(self, var, self._acceptedTypes)
  list.setitem(self, k, var)

def _LimitedTypeList__append(self, var):
  """
    Default append method
  """
  # This is default overload for list append, checking if item is accepted
  if not isinstance(var, self._acceptedTypes):
    raise NotAllowedType( self, var, self._acceptedTypes)
  list.append(self,var)

def _LimitedTypeList__extend(self, var):
  """
    Default append method
  """
  # This is default overload for list append, checking if item is accepted
  if not isinstance(var, self._acceptedTypes):
    raise NotAllowedType( self, var, self._acceptedTypes)
  list.extend(self,var)

def _LimitedTypeList____add__(self, var):
  """
    Default __add__ method
  """
  if type(var) in (list, tuple, type(self)):
    for value in var:
      if not isinstance(value, self._acceptedTypes):
        raise NotAllowedType( self, value, self._acceptedTypes )
  else:
    if not isinstance(var, self._acceptedTypes):
      raise NotAllowedType( self, var, self._acceptedTypes)
    var = [ var ]
  # This is default overload for list iadd, checking if item is accepted
  copy = list.__add__(self, var)
  return copy 

def _LimitedTypeList____iadd__( self, var, *args ):
  """
    Default __iadd__ method
  """
  for arg in args:
    if not isinstance( arg, self._acceptedTypes ):
      raise NotAllowedType( self, arg, self._acceptedTypes )
  if type(var) in (list, tuple, type(self)):
    for value in var:
      if not isinstance( value, self._acceptedTypes ):
        raise NotAllowedType( self, value, self._acceptedTypes )
  else:
    if not isinstance(var, self._acceptedTypes):
      raise NotAllowedType( self, var, self._acceptedTypes)
    var = [ var ]
  # This is default overload for list iadd, checking if item is accepted
  list.__iadd__(self, var)
  if args:
    list.__iadd__(self, args)
  return self


def _LimitedTypeList____init__( self, *args ):
  """
    Default __init__ method
  """
  if args:
    self.__iadd__(*args)

def _LimitedTypeList____call__( self ):
  """
    Default __call__ method.
    Yield holden objects.
  """
  for obj in self:
    yield obj

class NotAllowedType(ValueError):
  """
    Raised by LimitedTypeList to sign that it was attempted to add an item to the
    list which is not an allowedType instance.
  """
  def __init__( self , obj, input_, allowedTypes ):
    ValueError.__init__(self, ("Attempted to add to %s an object (type=%s) which is not an "
      "instance from the allowedTypes: %s!") % (obj.__class__.__name__, type(input_),allowedTypes,) )

from RingerCore.RawDictStreamable import RawDictStreamable, RawDictStreamer, \
                                         RawDictCnv, LoggerRawDictStreamer, \
                                         checkAttrOrSetDefault

class LimitedTypeListRDS( RawDictStreamer ):
  """
  This is the default streamer class for limited type lists. Overload this
  method to deal with special cases.
  """

  # FIXME: items should be __items. How to treat __items so that matlab can
  # read it as well?

  def __call__(self, obj):
    "Return a raw dict object from itself"
    setattr(obj,'items', list(obj))
    self._logger.debug("Added property items to %s with the following list: %r", 
        obj.__class__.__name__,
        obj.__dict__['items'])
    raw = RawDictStreamer.__call__( self, obj )
    obj.__dict__.pop('items')
    return raw

  def treatDict(self, obj, raw):
    listItems = raw['items']
    from TuningTools.PreProc import PreProcCollection
    tObj = type(obj)
    for idx, cObj in enumerate(listItems):
      if hasattr( cObj, 'toRawObj' ):
        listItems[idx] = cObj.toRawObj()
    RawDictStreamer.treatDict( self, obj, raw )
    return raw

class LimitedTypeListRDC( RawDictCnv ):
  """
  This is the default converter class for the limited type list. Overload this
  method to deal with special cases.
  """

  ignoreAttrs = {'items'}

  def __init__(self, ignoreAttrs = set(), toProtectedAttrs = set(), **kw ):
    ignoreAttrs = set(ignoreAttrs) | LimitedTypeListRDC.ignoreAttrs
    RawDictCnv.__init__( self, ignoreAttrs, toProtectedAttrs, **kw )

  def treatObj( self, obj, d ):
    """
    Overload this method to treat the python object
    """
    from RingerCore.RawDictStreamable import retrieveRawDict
    for rawObj in d['items']:
      obj.append( retrieveRawDict( rawObj ) )
    return obj

class LoggerLimitedTypeListRDS( LoggerRawDictStreamer, LimitedTypeListRDS ):
  # FIXME This should be a collection of RDCs to be applied
  def __init__(self, transientAttrs = set(), toPublicAttrs = set(), **kw):
    LoggerRawDictStreamer.__init__(self, transientAttrs, toPublicAttrs, **kw)

  def __call__(self, obj):
    return LimitedTypeListRDS.__call__( self, obj )

class LimitedTypeStreamableList( RawDictStreamable, LimitedTypeList):
  """
  LimitedTypeList with RawDictStreamable capability.
  """

  def __init__(cls, name, bases, dct):
    RawDictStreamable.__init__(cls,name, bases, dct)
    LimitedTypeList.__init__(cls,name, bases, dct)

  def __new__(cls, name, bases, dct):
    from RingerCore.Logger import Logger
    if Logger in bases:
      checkAttrOrSetDefault( "_streamerObj", dct, bases, LoggerLimitedTypeListRDS )
    else:
      checkAttrOrSetDefault( "_streamerObj", dct, bases, LimitedTypeListRDS )
    checkAttrOrSetDefault( "_cnvObj", dct, bases, LimitedTypeListRDC )
    t1 = RawDictStreamable.__new__(cls, name, bases, dct)
    name = t1.__name__
    bases = tuple(t1.mro())
    dct = t1.__dict__.copy()
    return LimitedTypeList.__new__(cls, name, bases, dct)

def inspect_list_attrs(var, nDepth, wantedType = None, tree_types = (list,tuple), dim = None, name = "", level = None ):
  """
  Check if list can be set into a LimitedTypeList of <wantedType> at the depth
  <nDepth>.
  
  Also make sure that its dimension is <dim>, otherwise spam it to <dim> if its
  previous size was 1.

  Use <name> to dimension name.

  <level> can be used to change the value of the logging level of the objects.
  """
  from copy import deepcopy
  if nDepth == 0:
    if level is not None and obj is not None:
      var.level = level
    if wantedType is not None:
      var = wantedType( var )
    # And that its size spans over last dim:
    if dim:
      lPar = len(var)
      if lPar == 1:
        var = wantedType( [ deepcopy(var) for _ in range(dim) ] )
      elif lPar != dim:
        raise RuntimeError("Number of dimensions equivalent to %s do not match specified value (is %d, should be %d)!" % (name, lPar, dim))
  else:
    from RingerCore.util import traverse
    for obj, idx, parent, _, _ in traverse( var
                                          , tree_types = tree_types
                                          , max_depth = nDepth
                                          ):
      if level is not None and obj is not None:
        obj.level = level
      if wantedType is not None:
        parent[idx] = wantedType(obj)
      # Make sure that its size spans over dim:
      if dim:
        lPar = len(parent[idx])
        if lPar == 1:
          parent[idx] = wantedType( [ deepcopy( parent[idx]) for _ in range(dim) ] )
        elif lPar != dim:
          raise RuntimeError("Number of dimensions equivalent to %s do not match specified value (is %d, should be %d)!" % (name, lPar, dim))
  return var
