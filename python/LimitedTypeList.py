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

    In case a class inherits from another classes that declare _acceptedTypes 
    and it does not declare this class attribute, then the first base class
    _acceptedTypes will be used.

    If none of the inherited classes define the __init__ method, the list 
    init method will be used. In case you have a inherited class with __init__
    method (case where the base class has __metaclass__ set to LimitedTypeList)
    and want to enforce that this class will use their own __init__ method, then
    set _useLimitedTypeList__init__ to True. If you do so, then the __init__ you declare
    will be overridden by the LimitedTypeList.
  """

  # TODO Add boolean to flag if the class can hold itself

  def __new__(cls, name, bases, dct):
    if not any( [ issubclass(base, list) for base in bases ] ):
      bases = (list,) + bases 
    import inspect
    import sys
    hasBaseInit = any([hasattr(base,'__init__') for base in bases if base.__name__ not in 
                                                                    ("list", "object", "Logger", "LoggerStreamable",)])
    for localFcnName, fcn in inspect.getmembers( sys.modules[__name__], inspect.isfunction):
      m = _lMethodSearch.match(localFcnName)
      if m:
        fcnName = m.group(1)
        if not fcnName in dct:
          if hasBaseInit and fcnName == '__init__' and not dct.get('_useLimitedTypeList__init__', False):
            continue
          dct[fcnName] = fcn
    return type.__new__(cls, name, bases, dct)

  def __init__(cls, name, bases, dct):
    ## Take care to _acceptedTypes be in the right specification
    if not '_acceptedTypes' in dct:
      for base in bases:
        if hasattr(base, '_acceptedTypes'):
          acceptedTypes = base._acceptedTypes
          break
      dct['_acceptedTypes'] = acceptedTypes
    else:
      acceptedTypes = dct['_acceptedTypes']
    if not type(acceptedTypes) is tuple:
      raise ValueError("_acceptedTypes must be declared as a tuple.")
    if not acceptedTypes:
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

#def _LimitedTypeList__pop(self, index = -1):
#  """
#    Default append method
#  """
#  if self.__class__.__name__ == "_TexObjectContextManager":
#    print ":: poping ", repr(self[index]), " from TexObjectContextManager ::"
#    import traceback
#    print "STACK:", ''.join(traceback.format_stack())
#  list.pop(self, index)
#
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

# Uncomment this in case you want to have LimitedTypeLists Specifying its type
#def _LimitedTypeList____str__(self):
#  """
#    Default __str__ method
#  """
#  return '< ' + self.__class__.__name__ + list.__str__(self) + ' >'

#def _LimitedTypeList____repr__(self):
#  """
#    Default __repr__ method
#  """
#  return '< ' + self.__class__.__name__ + list.__repr__(self) + ' >'

def _LimitedTypeList____iadd__( self, var, *args ):
  """
    Default __iadd__ method
  """
#  if self.__class__.__name__ == "_TexObjectContextManager":
#    print ":: adding ", repr(var), " to TexObjectContextManager ::"
#    import traceback
#    print "STACK:", ''.join(traceback.format_stack())
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

from RingerCore.RawDictStreamable import ( RawDictStreamable, RawDictStreamer
                                         , RawDictCnv, LoggerRawDictStreamer
                                         , checkAttrOrSetDefault )

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
    self._logger.verbose("Added property items to %s with the following list: %r"
                        , obj.__class__.__name__
                        , obj.__dict__['items'])
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

  ignoreAttrs = {'items',}

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

def inspect_list_attrs(var, nDepth, wantedType = None, tree_types = (list,tuple), dim = None, name = "", level = None, deepcopy = False, allowSpan = True ):
  """
  Check if list can be set into a LimitedTypeList of <wantedType> at the depth
  <nDepth>.
  
  Make sure that its dimension of <nDepth> is <dim>. If <allowSpan> is set, then 
  the only exception to throwing RuntimeError is when <nDepth> dimension is 1, where
  it will be spanned to have dimension size of <dim> by copying this element using
  <deepcopy> to determine whether to deepcopy element or do a standard copy.

  Use <name> to determine dimension name, this will be used in case of throwing.

  <level> can be used to change the value of the logging level of the objects.
  """
  dcopy = deepcopy; from copy import copy, deepcopy
  if nDepth == 0:
    if level is not None and obj is not None:
      var.level = level
    if dim is not None:
      # And that its size spans over last dim:
      lPar = len(var)
      if allowSpan and lPar == 1:
        if dim > 1: var = [ deepcopy( var[0] ) if dcopy else copy( var[0] ) for _ in range(dim) ]
      elif lPar != dim:
        raise RuntimeError("Number of dimensions equivalent to %s do not match specified value (is %d, should be %d)!" % (name, lPar, dim))
    if wantedType is not None and type(var) is not wantedType:
      var = wantedType( var )
  else:
    from RingerCore.LoopingBounds import traverse
    for obj, idx, parent, _, _ in traverse( var
                                          , tree_types = tree_types
                                          , max_depth = nDepth
                                          ):
      if level is not None and obj is not None:
        obj.level = level
      # Make sure that its size spans over dim:
      if dim is not None:
        lPar = len(parent[idx])
        if allowSpan and lPar == 1:
          if dim > 1: parent[idx] = [ deepcopy( obj[0] ) if dcopy else copy( obj[0] ) for _ in range(dim) ]
        elif lPar != dim:
          raise RuntimeError("Number of dimensions equivalent to %s do not match specified value (is %d, should be %d)!" % (name, lPar, dim))
        #else: # lPar == 1 and dim == 1:
      if wantedType is not None and type(parent[idx]) is not wantedType:
        parent[idx] = wantedType(parent[idx])
  if deepcopy:
    from copy import deepcopy
    var = deepcopy( var )
  return var
