__all__ = ['createGitParser']

from RingerCore.parsers.ParsingUtils import ArgumentParser, argparse

###############################################################################
# Git configuration related objects
###############################################################################
class _ConfigureGitAction( argparse.Action ):

  def __init__( self
              , option_strings
              , configure
              , dest='_tag'
              , nargs=2
              , const=None
              , default=None
              , type=None
              , choices=None
              , required=False
              , help = argparse.SUPPRESS
              , metavar='TAG'):
    self.configure = configure
    super(_ConfigureGitAction, self).__init__( option_strings = option_strings
                                         , dest           = dest
                                         , nargs          = nargs
                                         , const          = const
                                         , default        = default
                                         , type           = type
                                         , choices        = choices
                                         , required       = required
                                         , help           = help
                                         , metavar        = metavar
                                         )

  def __call__(self, parser, namespace, value, option_string=None):
    # Make sure to configure moduleName first as configuring tag will log the
    # configuration object
    self.configure.moduleName = value[1]
    self.configure.tag = value[0]
    setattr(namespace, self.dest, value)

def createGitParser( configureObj, tagArgStr ):
  gitParser = ArgumentParser( prog = "", add_help = False)
  gitParser.add_argument( tagArgStr, dest='tag', action=_ConfigureGitAction, configure = configureObj )
  return gitParser
