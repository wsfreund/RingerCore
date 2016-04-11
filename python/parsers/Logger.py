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
    type=str, required = False, choices = get_attributes(LoggingLevel, onlyVars = True, getProtected = False),
    help = "The output level for the main logger")
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

  def __getattr__(self, attr):
    if not 'output_level' in self.__dict__ and attr == 'output_level':
      return LoggingLevel.INFO
    else:
      return self.__dict__[attr]
###############################################################################


