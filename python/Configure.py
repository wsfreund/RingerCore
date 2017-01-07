__all__ = [ 'NotSetType', 'NotSet', 'Holder', 'StdPair'
          , 'EnumStringification', 'BooleanStr'
          , 'conditionalOption', 'GRID_ENV', 'retrieve_kw'
          , 'checkForUnusedVars', 'setDefaultKey' 
          , 'Configure', 'EnumStringificationOptionConfigure']

import os
GRID_ENV = int(os.environ.get('RCM_GRID_ENV',0))

class NotSetType( type ):
  def __bool__(self):
    return False
  __nonzero__ = __bool__
  def __repr__(self):
    return "<+NotSet+>"
  def __str__(self):
    return "<+NotSet+>"

class NotSet( object ): 
  """As None, but can be used with retrieve_kw to have a unique default value
  though all job hierarchy."""
  __metaclass__ = NotSetType

def retrieve_kw( kw, key, default = NotSet ):
  """
  Use together with NotSet to have only one default value for your job
  properties.
  """
  if not key in kw or kw[key] is NotSet:
    kw[key] = default
  return kw.pop(key)

def conditionalOption( argument, value ):
  """
  Returns argument + value option only when value is set.
  """
  return ( argument + " " + str(value) if not( type(value) in (list,tuple) ) and not( value in (None, NotSet) ) else \
      ( argument + " " + ' '.join([str(val) for val in value]) if value else '' ) )

class EnumStringification( object ):
  "Adds 'enum' static methods for conversion to/from string"

  _ignoreCase = False

  @classmethod
  def tostring(cls, val):
    "Transforms val into string."
    from RingerCore.util import get_attributes
    for k, v in get_attributes(cls, getProtected = False):
      if v==val:
        return k
    return None

  @classmethod
  def fromstring(cls, str_):
    "Transforms string into enumeration."
    if not cls._ignoreCase:
      return getattr(cls, str_, None)
    else:
      allowedValues = [attr for attr in get_attributes(cls) if not attr[0].startswith('_')]
      try:
        idx = [attr[0].upper() for attr in allowedValues].index(str_.upper().replace('-','_'))
      except ValueError:
        raise ValueError("%s is not in enumeration. Use one of the followings: %r" % (str_, allowedValues) )
      return allowedValues[idx][1]

  @classmethod
  def retrieve(cls, val):
    """
    Retrieve int value and check if it is a valid enumeration string or int on
    this enumeration class.
    """
    allowedValues = [attr for attr in get_attributes(cls) if not attr[0].startswith('_')]
    try:
      # Convert integer string values to integer, if possible:
      val = int(val)
    except ValueError:
      pass
    if type(val) is str:
      oldVal = val
      val = cls.fromstring(val)
      if val is None:
          raise ValueError("String (%s) does not match any of the allowed values %r." % \
              (oldVal, allowedValues))
    else:
      if not val in [attr[1] for attr in allowedValues]:
        raise ValueError(("Attempted to retrieve val benchmark "
            "with a enumeration value which is not allowed. Use one of the followings: "
            "%r") % allowedValues)
    return val

def checkForUnusedVars(d, fcn = None):
  """
    Checks if dict @d has unused properties and print them as warnings
  """
  for key in d.keys():
    if d[key] is NotSet: continue
    msg = 'Obtained not needed parameter: %s' % key
    if fcn:
      fcn(msg)
    else:
      print 'WARNING:%s' % msg

def setDefaultKey( d, key, val):
  "Adds key to dict if not available"
  if not key in d: d[key] = val

def get_attributes(o, **kw):
  """
    Return attributes from a class or object.
  """
  onlyVars = kw.pop('onlyVars', False)
  getProtected = kw.pop('getProtected', True)
  from RingerCore.Configure import checkForUnusedVars
  checkForUnusedVars(kw)
  import inspect
  return [(a[0] if onlyVars else a) for a in inspect.getmembers(o, lambda a:not(inspect.isroutine(a))) \
             if not(a[0].startswith('__') and a[0].endswith('__')) \
                and (getProtected or not( a[0].startswith('_') or a[0].startswith('__') ) ) ]

class BooleanStr( EnumStringification ):
  _ignoreCase = True

  False = 0
  True = 1

  @staticmethod
  def treatVar(var,d, default = False):
    if var in d:
      if d[var] not in (None, NotSet):
        return BooleanStr.retrieve( d[var] )
      else:
        return d[var]
    else:
      return default

class Holder( object ):
  """
  A simple object holder
  """
  def __init__(self, obj):
    self.obj = obj
  def __call__(self):
    return self.obj

class StdPair( object ): 
  """
  A simple object pair holder
  """
  def __init__(self, a, b):
    self.first  = a
    self.second = b
  def __call__(self):
    return (self.first, self.second)

from RingerCore.RawDictStreamable import Logger
class Configure( Logger ):
  """
  Improves job property configuration by making its choice in sync for all modules.
  """

  def __init__(self, **kw):
    self._choice = NotSet
    Logger.__init__( self, kw )

  def get( self ):
    if self.configured():
      return self._choice
    else:
      self.check_configure()
      return self._choice

  def set( self, val ):
    if self.configured():
      self._logger.fatal("Attempted to configure %s twice.", self.__class__.__name__)
    if val is not NotSet:
      self._choice = self.retrieve(val)
    result = self.test() 
    if result is not None and not self.test():
      self._logger.fatal("%s test failed.", self.__class__.__name__)

  def retrieve(self, val):
    """
    Overload this method to implement special case when retrieving the configuration
    """
    return val

  def test( self ):
    "Overload to implement some test if needed"
    return True

  def configured( self ):
    if self._choice is NotSet:
      return False
    return True

  def check_configure( self ):
    " Check if configured, if not, run auto-configuration. "
    if not self.configured():
      if hasattr(self,'auto'): 
        self.auto()
        return
    self._logger.fatal("%s was not configured.", self.__class__.__name__)

  def __call__( self ):
    return self.get()

  def __nonzero__( self ):
    "Check whether we are configured"
    return self.configured()

  def __lt__(self, val):
    return self.get() < val

  def __le__(self, val):
    return self.get() <= val

  def __eq__(self, val):
    return self.get() == val

  def __ne__(self, val):
    return self.get() != val

  def __gt__(self, val):
    return self.get() > val

  def __ge__(self, val):
    return self.get() >= val

  def _autoconfiguration(self):
    if hasattr(self,'auto'):
      self.auto()
    else:
      self._logger.fatal( 'Class %s cannot auto-configure itself.'
                        , self.__class__.__name__ )
    # Make sure that the autoconfiguration set choice to a valid option
    self._choice = self.retrieve( self._choice )

  def __str__( self ):
    return str(self._choice)

  def __repr__( self ):
    return self.__class__.__name__.lstrip('_') + "(" + str( self ) + ")"


class EnumStringificationOptionConfigure( Configure ):
  """
  Configure specialization for EnumStringification options.
  """

  def __init__(self, **kw):
    Configure.__init__( self, **kw )
    self._enumTypeAvailable()

  def retrieve( self, val ):
    return self._enumType.retrieve( val )

  def _enumTypeAvailable(self):
    if not hasattr(self, '_enumType'):
      self._logger.fatal( "Class %s does not have _enumType value. Please, make sure to add it."
                        , self.__class__.__name__
                        , TypeError )

  def __str__( self ):
    self._enumTypeAvailable()
    if self:
      return self._enumType.tostring( self.get() )
    else:
      return str(self._choice)

  def __repr__( self ):
    self._enumTypeAvailable()
    return self.__class__.__name__.lstrip('_') + "(" + self._enumType.tostring( self.get() ) + ")"
