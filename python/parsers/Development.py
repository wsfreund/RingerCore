__all__ = ['DevParser','devParser']

from RingerCore.parsers.ParsingUtils import ArgumentParser, argparse
from RingerCore.Configure import NotSet, Development, BooleanStr

###############################################################################
# Logger related objects
###############################################################################
class _RetrieveDevelopmentAction(argparse.Action):
  def __call__(self, parser, namespace, value, option_string=None):
    Development.set( value )
    setattr(namespace, self.dest, value)

def DevParser():
  devParser = ArgumentParser(add_help = False)
  devArgGroup = devParser.add_argument_group('Development arguments', '')
  devArgGroup.add_argument('--development', action=_RetrieveDevelopmentAction
      , type=BooleanStr, required = False, dest='development', default = NotSet
      , help = "Whether running development jobs." )
  return devParser
devParser = DevParser()
