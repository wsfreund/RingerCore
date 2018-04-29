__all__ = [ 'NotSetType', 'NotSet', 'Holder', 'StdPair'
          , 'EnumStringification', 'BooleanStr'
          , 'conditionalOption', 'RCM_GRID_ENV', 'retrieve_kw'
          , 'checkForUnusedVars', 'setDefaultKey' 
          , 'Configure', 'EnumStringificationOptionConfigure'
          , 'MasterLevel', 'masterLevel', 'RCM_NO_COLOR', 'OMP_NUM_THREADS'
          , 'cmd_exists', 'LimitedTypeOptionConfigure', 'CastToTypeOptionConfigure'
          , 'Development'
          ]

import os, multiprocessing
RCM_GRID_ENV = int(os.environ.get('RCM_GRID_ENV',0))
RCM_NO_COLOR = int(os.environ.get('RCM_NO_COLOR',1))
OMP_NUM_THREADS = int(os.environ.get('OMP_NUM_THREADS',multiprocessing.cpu_count()))

def cmd_exists(cmd):
  """
  Check whether command exists.
  Taken from: http://stackoverflow.com/a/28909933/1162884
  """
  import subprocess
  return subprocess.call("type " + cmd, shell=True, 
      stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

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
  return ( argument + " " + str(value) if not( type(value) in (list,tuple) ) and not( value in (None, NotSet,'') ) else \
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

  @classmethod
  def sretrieve(cls, val):
    "Return enumeration equivalent value in string if it is a valid enumeration code."
    return cls.tostring(cls.retrieve(val))

  @classmethod
  def optionList(cls):
    from operator import itemgetter
    return [v for v in sorted(get_attributes( cls, getProtected = False), key=itemgetter(1))]

  @classmethod
  def stringList(cls):
    from operator import itemgetter
    return [v[0] for v in sorted(get_attributes( cls, getProtected = False), key=itemgetter(1))]

  @classmethod
  def intList(cls):
    from operator import itemgetter
    return [v[1] for v in sorted(get_attributes( cls, getProtected = False), key=itemgetter(1))]

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
  def __init__(self, obj = None, replaceable = True):
    self._obj = obj
    self._replaceable = replaceable
  def __call__(self):
    return self._obj
  def isValid(self):
    return self._obj not in (None, NotSet)
  def set(self, value):
    if self._replaceable or not self.isValid():
      self._obj = value
    else:
      raise RuntimeError("Cannot replace held object.")

class StdPair( object ): 
  """
  A simple object pair holder
  """
  def __init__(self, a, b):
    self.first  = a
    self.second = b
  def __call__(self):
    return (self.first, self.second)

from RingerCore.Logger import Logger

class Configure( Logger ):
  """
  Improves job property configuration by making its choice in sync for all modules.
  """

  # This property set whether this class can only be configured once or not
  allowReconfigure = False
  # When this property is set, you must implement a method auto which will be
  # called every time the instance get is used
  alwaysAutoConfigure = False
  # If this option is set, user can manually set the option which will disable
  # alwaysAutoConfigure option
  allowManualConfigure = True

  def __init__(self, **kw):
    self._choice = NotSet
    if not hasattr(self,'name'):
      self.name = self.__class__.__name__.lstrip('_')
      self.name = self.name.replace('Configure','')
    Logger.__init__( self, kw, logName = self.name )

  def get( self ):
    if self.configured():
      return self._choice
    else:
      self.check_configure()
      return self._choice

  def set( self, val ):
    if val not in (NotSet, None):
      if not self.allowManualConfigure:
        if hasattr(self, '_logger'):
          self._fatal("Cannot manually change choice value")
        else:
          raise RuntimeError("Cannot manually change choice value")
      if self.alwaysAutoConfigure:
        self.alwaysAutoConfigure = False
        if hasattr(self, '_logger'): self._debug("Disabled auto configuration for %s due to manual value setup.", self.name)
      value = self.retrieve( val )
      if not self.allowReconfigure and self.configured():
        self._warning("Attempted to reconfigure %s.",  self.name)
      newChoice = value
      if newChoice != self._choice:
        self._choice = newChoice
        test_result = self.test() 
        if test_result is not None and not test_result:
          if hasattr(self, '_logger'):
            self._fatal("%s test failed.", self.name )
          else:
            raise RuntimeError('%s test failed', self.name )
        if hasattr(self, '_logger'):
          self._info('%s was set to %s', self.name, str(self), extra={'color':'0;34'} ) 
      elif hasattr(self, '_logger'):
        self._verbose('Ignored setting to same value. (Previous|New): (%s|%s)', self._choice, val ) 
    elif hasattr(self, '_logger'):
      self._debug('Called %s set method with empty value.', self.name )
    return self._choice

  def retrieve(self, val):
    """
    Overload this method to implement special case when retrieving the configuration
    """
    return val

  def test( self ):
    "Overload to implement some test if needed"
    return True

  def configured( self ):
    if self._choice in (NotSet, None) or self.alwaysAutoConfigure:
      return False
    return True

  def check_configure( self ):
    """Check whether this class is configured, raise otherwise except when it can
    auto-configure itself"""
    if not self.configured():
      self._autoconfiguration() 
    else:
      self._fatal("%s was not configured.", self.name )

  def parser_set( self, value ):
    """ Special method for parsers to use Configure classes: set value and return self."""
    self.set( value )
    return self

  class __retrieve: pass
  def __call__( self, value = __retrieve ):
    if value is self.__class__.__retrieve:
      return self.get()
    else:
      return self.set( value )

  def __nonzero__( self ):
    return bool(self.get())

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
      if not self.configured() and not self.alwaysAutoConfigure:
        self._logger.fatal( "Autoconfiguration failed for %s", self.name )
    else:
      self._logger.fatal( 'Class %s cannot auto-configure itself.', self.name )
    # Make sure that the autoconfiguration set choice to a valid option
    self._choice = self.retrieve( self._choice )

  def __str__( self ):
    return str(self._choice)

  def __repr__( self ):
    return '%s[%s](%s)' % (self.name
                          , ','.join( [ 'ALWAYS_AUTO' if self.alwaysAutoConfigure else ('CAN_AUTO' if hasattr(self,'auto') else 'MANUAL_ONLY') ]
                                    + (['CAN_RECONFIGURE' if self.allowReconfigure else 'CANNOT_RECONFIGURE'] if not self.alwaysAutoConfigure else [])
                                    + (['ALLOW_MANUAL' if self.allowManualConfigure else 'NO_MANUAL_CONFIG'] if self.alwaysAutoConfigure else []) 
                                    )
                          , self)

class LimitedTypeOptionConfigure( Configure ):
  """
  Configure specialization which accepts only values with types specified by _acceptedTypes.
  """
  def __init__(self, **kw):
    Configure.__init__( self, **kw )
    self._acceptedTypesAvailable()

  def test(self):
    return isinstance( self, self._acceptedTypes )

  def retrieve( self, val ):
    if not isinstance(val, self._acceptedTypes):
      self._fatal("Attempted to set %s to a value (%s) which is not of _acceptedTypes: %r", self.name, self._acceptedTypes)
    return val

  def _acceptedTypesAvailable(self):
    if not hasattr(self, '_acceptedTypes'):
      self._fatal( "Class %s does not have _acceptedTypes value. Please, make sure to add it."
                        , self.name
                        , TypeError )
    elif not isinstance(self._acceptedTypes, tuple) or not all([isinstance(t,type) for t in self._acceptedTypes]):
      self._fatal( "_acceptedTypes must be a tuple of types")

class CastToTypeOptionConfigure( Configure ):
  """
  This configurable will attempt to recast option to _castType
  """
  def __init__(self, **kw):
    Configure.__init__( self, **kw )
    self._castTypeAvailable()

  def test(self):
    return isinstance( self(), self._castType )

  def retrieve( self, val ):
    if not isinstance(val, self._castType ):
      val = self._castType( val )
    return val

  def _castTypeAvailable(self):
    if not hasattr(self, '_castType'):
      self._fatal( "Class %s does not have _castType value. Please, make sure to add it."
                        , self.name
                        , TypeError )
    elif not isinstance(self._castType, type):
      self._fatal( "Cast type set (%r) is not an instance of type", self._castType)

class EnumStringificationOptionConfigure( LimitedTypeOptionConfigure ):
  """
  LimitedTypeOptionConfigure specialization for EnumStringification options.
  """

  def __init__(self, **kw):
    Configure.__init__( self, **kw )
    self._acceptedTypesAvailable()

  def retrieve( self, val ):
    return self._enumType.retrieve( val )

  def test( self ):
    return True

  def _acceptedTypesAvailable(self):
    if not hasattr(self, '_enumType'):
      self._fatal( "Class %s does not have _enumType value. Please, make sure to add it."
                        , self.name
                        , TypeError )
    elif not issubclass(self._enumType, EnumStringification):
      self._fatal( "Accepted type is not a subclass of EnumStringification" )

  def __str__( self ):
    if self.configured():
      return self._enumType.tostring( self.get() )
    else:
      return str(self._choice)

  def __repr__( self ):
    return self.name + "(" + self._enumType.tostring( self.get() ) + ")"

from RingerCore.Logger import LoggingLevel

import logging
def _mutedLogger(self, value = None ):
  value = LoggingLevel.MUTE
  logging.Logger.setLevel(self, value )
  try:
    self._ringercore_logger_parent._level = value
  except AttributeError:
    pass


class _ConfigureMasterLevel( EnumStringificationOptionConfigure ):
  """
  Master switch for all loggers
  """

  # NOTE: To end circular import, master level configures it self to INFO
  # message level in start-up, only afterwards it will configure itself to
  # masterlevel

  _enumType = LoggingLevel
  # It is possible to reconfigure the master level
  allowReconfigure = True

  level = property( EnumStringificationOptionConfigure.get, EnumStringificationOptionConfigure.set )

  def __init__(self, **kw):
    self.handledLoggers = []
    self.mutedLoggers = []
    # Force ourself to start configuration with INFO level to avoid using
    # ourself to configure our own level, which will lead into circular import
    # This will be configured after auto, so all MasterLevel debug/verbose
    # messages will only show after auto is called
    kw['level'] = LoggingLevel.INFO
    EnumStringificationOptionConfigure.__init__(self, **kw)
    # Add us to be handled by ourself
    self.handledLoggers.append( self._logger )

  def auto(self):
    import argparse
    simpleParser = argparse.ArgumentParser(add_help = False)
    simpleParser.add_argument('--output-level', required = False, dest='level', default = None)
    args, argv = simpleParser.parse_known_args()
    # We don't consume the option so that other parsers can also retrieve the
    # logging level
    if args.level in (None, NotSet):
      args.level = LoggingLevel.INFO
    self.set( args.level )

  def retrieve(self, val):
    val = EnumStringificationOptionConfigure.retrieve( self, val )
    if val != self._choice:
      for logger in self.handledLoggers:
        if logger.name not in self.mutedLoggers:
          logger.setLevel( val )
    return val

  def handle(self, logger):
    if logger.name in self.mutedLoggers:
      self._mute( logger )
    else:
      logger.setLevel( self.level )
    self.handledLoggers.append( logger )

  def unhandle(self, logger):
    try:
      while True:
        self.handledLoggers.pop( self.handledLoggers.index( logger ) )
    except (KeyError, ValueError):
      pass

  def mute(self, logName):
    self.mutedLoggers.append(logName)
    values = [logger.name for logger in self.handledLoggers]
    try:
      idx = values.index(logName)
      self._mute( self.handledLoggers[idx] )
    except ValueError:
      pass

  def _mute(self, logger):
    import types
    logger.setLevel( LoggingLevel.MUTE )
    logger.setLevel = types.MethodType( _mutedLogger, logger )

MasterLevel = Holder( _ConfigureMasterLevel() )

masterLevel = MasterLevel()

class _ConfigureDevelopment( EnumStringificationOptionConfigure ):
  """
  Defines whether jobs are run in development mode
  """

  _enumType = BooleanStr

  value = property( EnumStringificationOptionConfigure.get, EnumStringificationOptionConfigure.set )

  def __init__(self, **kw):
    EnumStringificationOptionConfigure.__init__(self, **kw)

  def auto(self):
    import argparse
    simpleParser = argparse.ArgumentParser(add_help = False)
    simpleParser.add_argument('--development', required=False, action='store_true')
    args, argv = simpleParser.parse_known_args()
    # We don't consume the option so that other parsers can also retrieve the
    # logging level
    if args.development in (None, NotSet):
      args.development = False
    self.set( args.development )

Development = _ConfigureDevelopment()
