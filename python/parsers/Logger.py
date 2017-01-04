__all__ = ['LoggerNamespace', 'loggerParser']

from RingerCore.parsers.ParsingUtils import ArgumentParser, argparse

###############################################################################
# Logger related objects
###############################################################################
#class _RetrieveOutputLevelAction(argparse.Action):
#  def __call__(self, parser, namespace, values, option_string=None):
#    setattr(namespace, self.dest, values)

from RingerCore.Logger import LoggingLevel, Logger
loggerParser = ArgumentParser(add_help = False)
logOutput = loggerParser.add_argument_group('Loggging arguments', '')
logOutput.add_argument('--output-level', #action=_RetrieveOutputLevelAction,
    default = LoggingLevel.tostring( LoggingLevel.INFO ), 
    type=LoggingLevel, required = False, dest='_level',
    help = "The output level for the main logger." )

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
      raise AttributeError("Namespace does not have any level property. Make sure to add the loggerParser as a parent in the RingerCore.parsers submodule.")
  def _setOutputLevel(self, value):
    try:
      self.level = value
    except AttributeError:
      raise AttributeError("Namespace does not have any level property. Make sure to add the loggerParser as a parent in the RingerCore.parsers submodule.")
  import types
  argparse.Namespace.output_level = property( _getOutputLevel , _setOutputLevel)
