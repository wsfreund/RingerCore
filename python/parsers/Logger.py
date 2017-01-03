__all__ = ['LoggerNamespace', 'loggerParser']

try:
  import argparse
except ImportError:
  from RingerCore.parsers import __py_argparse as argparse

from RingerCore.util import EnumStringification, get_attributes

###############################################################################
# Logger related objects
###############################################################################
from RingerCore.Logger import LoggingLevel, Logger
loggerParser = argparse.ArgumentParser(add_help = False)
logOutput = loggerParser.add_argument_group('Loggging arguments', '')
logOutput.add_argument('--output-level', 
    default = LoggingLevel.tostring( LoggingLevel.INFO ), 
    type=str, required = False, dest = '_outputLevel',
    help = "The output level for the main logger. Options are: " + \
        str( get_attributes( LoggingLevel, onlyVars = True, getProtected = False ) ))
###############################################################################
## LoggerNamespace
# When using logger parser parent, make sure to use LoggerNamespace when
# retrieving arguments
class LoggerNamespace( argparse.Namespace ):
  """
    Namespace for dealing with logger parser properties
  """
  def __init__(self, **kw):
    argparse.Namespace.__init__( self, **kw )

  @property
  def output_level(self):
    if '_outputLevel' in self.__dict__:
      return LoggingLevel.retrieve( self.__dict__['_outputLevel'] )
    else:
      return LoggingLevel.INFO

  def __call__(self):
    try:
      self.setLevel( self.output_level )
    except AttributeError:
      pass
###############################################################################


