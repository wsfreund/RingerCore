__all__ = ['LoggerNamespace', 'loggerParser']

from RingerCore.parsers.ParsingUtils import ArgumentParser, argparse
from RingerCore.Logger import ( LoggingLevel, Logger, )
from RingerCore.Configure import masterLevel

###############################################################################
# Logger related objects
###############################################################################
class _RetrieveOutputLevelAction(argparse.Action):
  def __call__(self, parser, namespace, value, option_string=None):
    masterLevel.set( value )
    self.level = value
    namespace.level = value
    setattr(namespace, self.dest, value)

loggerParser = ArgumentParser(add_help = False)
logOutput = loggerParser.add_argument_group('Logging arguments', '')
logOutput.add_argument('--output-level', action=_RetrieveOutputLevelAction,
    type=LoggingLevel, required = False, dest='_level', default = LoggingLevel.INFO,
    metavar = 'LEVEL', help = "The output level for the main logger." )
# TODO Add a destination file for logging messages
#parser.add_argument(
#        '--log', default=sys.stdout, type=argparse.FileType('w'),
#            help='the file where the sum should be written')
#args = parser.parse_args()
#args.log.write('%s' % sum(args.integers))
#args.log.close()
# OR use logging itself


###############################################################################
## LoggerNamespace
# Just for backward compatibility
LoggerNamespace = argparse.Namespace
if not hasattr(argparse.Namespace, 'output_level'):
  # Decorate Namespace with output_level property which is the same as
  # the level property for backward compatibility and to not confuse 
  # users of the logger parser that there is a property output-level but 
  # it should be retrieved through level.
  # We do this on the original class to simplify usage, as there will be 
  # no need to specify a different namespace for parsing the arguments.
  def _getOutputLevel(self):
    try:
      return self.level
    except AttributeError:
      try:
        return self._level
      except AttributeError:
        return masterLevel()

  def _setOutputLevel(self, value):
    try:
      self.level = value
    except AttributeError:
      try:
        self._level = value
      except AttributeError:
        raise AttributeError("Namespace does not have any level property. Make sure to add the loggerParser as a parent in the RingerCore.parsers submodule.")
  argparse.Namespace.output_level = property( _getOutputLevel , _setOutputLevel)
