__all__ = ['LoggingLevel', 'Logger']

from RingerCore.util import EnumStringification
import logging

class LoggingLevel ( EnumStringification ):
  """
    A wrapper for logging levels, which allows stringification of known log
    levels.
  """
  VERBOSE = logging.DEBUG - 1
  DEBUG = logging.DEBUG
  INFO = logging.INFO
  WARNING = logging.WARNING
  ERROR = logging.ERROR
  FATAL = logging.CRITICAL

  @classmethod
  def toC(cls, val):
    val = LoggingLevel.retrieve( val ) 
    if val == cls.VERBOSE:
      val = 0
    else:
      val = val/10
    return val + 1 # There is NIL at 0, DEBUG is 2 and so on.

logging.addLevelName(LoggingLevel.VERBOSE, "VERBOSE")
logging.addLevelName(LoggingLevel.FATAL,    "FATAL" )

def verbose(self, message, *args, **kws):
  """
    Attempt to emit verbose message
  """
  if self.isEnabledFor(LoggingLevel.VERBOSE):
    self._log(LoggingLevel.VERBOSE, message, args, **kws) 

def fatal(self, message, *args, **kws):
  """
    Attempt to emit fatal message
  """
  if self.isEnabledFor(LoggingLevel.FATAL):
    self._log(LoggingLevel.FATAL, message, args, **kws) 

logging.Logger.verbose = verbose
logging.Logger.fatal = fatal

def getFormatter():
  class Formatter(logging.Formatter):
    black, red, green, yellow, blue, magenta, cyan, white = range(8)
    reset_seq = "\033[0m"
    color_seq = "\033[1;%dm"
    bold_seq = "\033[1m"
    colors = { 
							 'WARNING':  yellow,
							 'INFO':     green,
							 'DEBUG':    blue,
							 'CRITICAL': magenta,
							 'ERROR':    red,
							 'VERBOSE':  cyan
						 }

    def __init__(self, msg, use_color = False):
      logging.Formatter.__init__(self, msg)
      self.use_color = use_color

    def format(self, record):
      levelname = record.levelname
      name = record.name
      msg = record.msg
      if self.use_color and levelname in self.colors:
        msg_color = self.color_seq % (30 + self.colors[levelname]) + msg + self.reset_seq
        levelname_color = self.color_seq % (30 + self.colors[levelname]) + levelname + self.reset_seq
        name_color = self.color_seq % (30 + self.colors[levelname]) + name + self.reset_seq
        record.msg = msg_color
        record.levelname = levelname_color
        record.name = name_color
      return logging.Formatter.format(self, record)
  #formatter = Formatter("Py.%(name)-41.41s%(levelname)-14.14s %(message)s")
  formatter = Formatter("Py.%(name)-33.33s %(levelname)7.7s %(message)s")
  return formatter

# create console handler and set level to notset
def getConsoleHandler():
  import sys
  ch = logging.StreamHandler( sys.__stdout__ )
  ch.setLevel( logging.NOTSET ) #  Minimal level in which the ch will print
  # add formatter to ch
  ch.setFormatter(getFormatter())
  return ch

class Logger( object ):
  """
    Simple class for giving inherited classes logging capability as well as the
    possibility for being serialized by pickle.

    The logger states are not pickled. When unpickled, it will have to be
    manually configured or it will use default configuration.
  """

  _formatter = getFormatter()
  _ch = getConsoleHandler()

  @classmethod
  def getModuleLogger(cls, logName, logDefaultLevel = logging.INFO):
    """
      Retrieve logging stream handler using logName and add a handler
      to stdout if it does not have any handlers yet.

      Format logging stream handler to output in the same format used by Athena
      messages.
    """
    # Retrieve root logger
    rootLogger = logging.getLogger()
    rootHandlers = rootLogger.handlers
    for rH in rootHandlers:
      if isinstance(rH,logging.StreamHandler):
        rH.setFormatter(cls._formatter)
    # Retrieve the logger
    logger = logging.getLogger( logName )
    # Retrieve handles:
    handlers = logger.handlers
    if not cls._ch in handlers:
      # add ch to logger
      logger.addHandler(cls._ch)
    logger.setLevel( logDefaultLevel )
    return logger

  def __init__(self, d = {}, **kw ):
    """
      Retrieve from args the logger, or create it using default configuration.
    """
    d.update( kw )
    from RingerCore.util import retrieve_kw
    self._level = LoggingLevel.retrieve( retrieve_kw(d, 'level', LoggingLevel.INFO ) )
    self._logger = retrieve_kw(d,'logger', None)  or \
        Logger.getModuleLogger(self.__class__.__name__, self._level )
    self._logger.verbose('Initialiazing %s', self.__class__.__name__)

  def getLevel(self):
    return LoggingLevel.tostring( self._level )

  def setLevel(self, value):
    self._level = LoggingLevel.retrieve( value )
    self._logger.setLevel(self._level)

  level = property( getLevel, setLevel )

  def __getstate__(self):
    """
      Makes logger invisible for pickle
    """
    odict = self.__dict__.copy() # copy the dict since we change it
    del odict['_logger']         # remove logger entry
    return odict

  def __setstate__(self, dict):
    """
      Add logger to object if it doesn't have one:
    """
    self.__dict__.update(dict)   # update attributes
    try: 
      self._logger
    except AttributeError:
      self._logger = Logger.getModuleLogger(self.__module__)

    if self._logger is None: # Also add a logger if it is set to None
      self._logger = Logger.getModuleLogger(self.__module__)

del getConsoleHandler, getFormatter
