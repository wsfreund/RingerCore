__all__ = ['LoggingLevel', 'Logger']

from RingerCore.util import EnumStringification
import logging

class LoggingLevel ( EnumStringification ):
  """
    A wrapper for logging levels, which allows stringification of known log
    levels.
  """
  VERBOSE  = logging.DEBUG - 1
  DEBUG    = logging.DEBUG
  INFO     = logging.INFO
  WARNING  = logging.WARNING
  ERROR    = logging.ERROR
  CRITICAL = logging.CRITICAL
  FATAL    = logging.CRITICAL

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

# This won't handle print and sys.stdout, but most of the cases are handled.
_nl = True

class StreamHandler2( logging.StreamHandler ):
  """
  Just in case we need a bounded method for emiting without newlines.
  """

  def __init__(self, handler):
    """
    Copy ctor
    """
    logging.StreamHandler.__init__(self)
    self._name = handler._name
    self.level = handler.level
    self.formatter = handler.formatter
    self.stream = handler.stream
    # We use stream as carrier b/c other handlers may complicate things

  def emit_no_nl(self, record):
    """
    Monkey patching to emit a record without newline.
    """
    #print '\n record', record
    #print '\n record.__dict__', record.__dict__
    try:
      nl = record.nl
    except AttributeError:
      nl = True
    try:
      msg = self.format(record)
      stream = self.stream
      global _nl
      fs = ''
      if nl and not _nl:
        fs += '\n'
      _nl = nl
      fs += '%s'
      if nl: fs += '\n'
      if not logging._unicode: #if no unicode support...
        stream.write(fs % msg)
      else:
        try:
          if (isinstance(msg, unicode) and
            getattr(stream, 'encoding', None)):
            ufs = u'%s'
            try:
              stream.write(ufs % msg)
            except UnicodeEncodeError:
              #Printing to terminals sometimes fails. For example,
              #with an encoding of 'cp1251', the above write will
              #work if written to a stream opened or wrapped by
              #the codecs module, but fail when writing to a
              #terminal even when the codepage is set to cp1251.
              #An extra encoding step seems to be needed.
              stream.write((ufs % msg).encode(stream.encoding))
          else:
            stream.write(fs % msg)
        except UnicodeError:
          stream.write(fs % msg.encode("UTF-8"))
      self.flush()
    except (KeyboardInterrupt, SystemExit):
      raise
    except:
      self.handleError(record)


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
      if not(hasattr(record,'nl')): 
        record.nl = True
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

    Logger will keep its logging level even after unpickled.
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
        # This may not be the desired behavior in some cases, but this fixes
        # the streamer created by ipython notebook
        import sys
        if rH.stream is sys.stderr:
          rH.stream = sys.stdout
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

  def __setstate__(self, d):
    """
      Add logger to object if it doesn't have one:
    """
    self.__dict__.update(d)   # update attributes
    try: 
      if self._logger is None: # Also add a logger if it is set to None
        self._logger = Logger.getModuleLogger(self.__class__.__name__, self._level )
    except AttributeError:
      self._logger = Logger.getModuleLogger(self.__module__, self._level)
    self._logger.setLevel( self._level )


del getConsoleHandler, getFormatter
