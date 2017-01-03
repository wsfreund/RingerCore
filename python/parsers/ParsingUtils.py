__all__ = ['argparse','JobSubmitArgumentParser', 'JobSubmitNamespace']

from RingerCore.util import get_attributes
import re

try:
  import argparse
except ImportError:
  from RingerCore.parsers import __py_argparse as argparse

from RingerCore.Logger import Logger

class _JobSubmitActionsContainer( object ):

  def add_job_submission_option(self, *l, **kw):
    kw['dest'] = self._getDest(*l)
    self.add_argument(*l, **kw)

  def add_job_submission_csv_option(self, *l, **kw):
    kw['dest'] = self._getDest( *l, extraSpec = '_CSV')
    if kw.pop('nargs','+') != '+':
      raise ValueError('Cannot specify nargs different from \'+\' when using csv option')
    kw['nargs'] = '+'
    if not 'default' in kw:
      kw['default'] = []
    self.add_argument(*l, **kw)

  def add_job_submission_option_group(self, *l, **kw):
    "Add a group of options that will be set if true or another group to be set when false"
    kw['dest'] = self._getDest( *l, extraSpec = '_Group')
    self.add_argument(*l, **kw)

  def add_job_submission_suboption(mainOption, suboption, *l, **kw):
    kw['dest'] = self._getDest(*[mainOption]) + ' ' + suboption
    self.add_argument(*l, **kw)

  def add_argument_group(self, *args, **kwargs):
    kwargs['prefix'] = self.prefix
    group = _JobSubmitArgumentGroup(self, *args, **kwargs)
    self._action_groups.append(group)
    return group

  def add_mutually_exclusive_group(self, **kwargs):
    kwargs['prefix'] = self.prefix
    group = _JobSubmitMutuallyExclusiveGroup(self, **kwargs)
    self._mutually_exclusive_groups.append(group)
    return group

  def _getDest(self, *l, **kw):
    extraSpec = kw.pop('extraSpec', '')
    search = [item.startswith('--') for item in l]
    if search and any(search):
      idx = search.index( True ) 
      try:
        return self.prefix + extraSpec + '__' + l[idx].lstrip('--')
      except AttributeError:
        raise AttributeError("Class (%s) prefix attribute was not specified." % self.__class__.__name__)
    else:
      search = [item.startswith('-') for item in l]
      if search and any(search):
        idx = search.index( True ) 
        try:
          return self.prefix + extraSpec + '_' + l[idx].lstrip('-')
        except AttributeError:
          raise AttributeError("Class (%s) prefix attribute was not specified." % self.__class__.__name__)
    return 


class JobSubmitArgumentParser( _JobSubmitActionsContainer, argparse.ArgumentParser ):
  """
  This class separate the options to be parsed in two levels:
    -> One group of options that will be used to specify the job submition;
    -> Another group which may be used for general purpose, usually
    used to specify the job parameters.

  The second group should use the standard add_argument method. The first group,
  however, should be created using the add_job_submission_option, they will be 
  added to a destination argument which will use a prefix specified through the
  'prefix' class attribute.
  """
  def __init__(self,*l,**kw):
    _JobSubmitActionsContainer.__init__(self)
    argparse.ArgumentParser.__init__(self,*l,**kw)
    try:
      self.add_argument('--dry-run', action='store_true',
          help = """Only print resulting command, but do not execute it.""")
    except argparse.ArgumentError:
      pass


class JobSubmitNamespace( Logger, argparse.Namespace ):

  def __init__(self, prog = None, **kw):
    Logger.__init__( self, kw )
    if prog is not None:
      self.prog = prog
    else:
      try:
        self.prog = self.__class__.prog
      except AttributeError:
        raise AttributeError("Not specified class (%s) prog attribute!" % self.__class__.__name__)
    try:
      self.prefix = self.__class__.ParserClass.prefix
    except AttributeError:
      raise AttributeError("Not specified class (%s) ParserClass attribute!" % self.__class__.__name__)
    argparse.Namespace.__init__( self )

  def __call__(self):
    full_cmd_str = self.prog + ' \\\n'
    full_cmd_str += self.parse_exec()
    full_cmd_str += self.parse_special_args()
    full_cmd_str += self._parse_standard_args()
    self._run_command(full_cmd_str)

  def parse_exec(self):
    "Overload this method to specify how the exec command string should be written."
    return ''

  def parse_special_args(self):
    "Overload this method treat special parameters."
    return ''

  def has_job_submission_option(self, option):
    try:
      self._find_job_submission_option(option)
      return True
    except KeyError:
      return False

  def get_job_submission_option(self, option):
    return getattr(self, self._find_job_submission_option(option))

  def set_job_submission_option(self, option, val):
    return setattr(self, self._find_job_submission_option(option), val)

  def append_to_job_submission_option(self, option, val):
    try:
      from RingerCore.LimitedTypeList import LimitedTypeList
      if hasattr(val,'__metaclass__') and issubclass(val.__metaclass__, LimitedTypeList):
        attr = self.get_job_submission_option(option)
        attr += val
      elif isinstance(val, (tuple,list)):
        self.get_job_submission_option(option).extend(val)
      else:
        self.get_job_submission_option(option).append(val)
    except AttributeError, e:
      raise TypeError('Option \'%s\' is not a collection. Details:\n%s' % (option,e))

  def _find_job_submission_option(self, option):
    import re
    search = re.compile('^' + self.prefix + '(_.+)?_{1,2}' + option + '$')
    matches = [key for key in get_attributes(self, onlyVars = True) if bool(search.match( key ))]
    lMatches = len(matches)
    if lMatches > 1:
      self._logger.warning("Found more than one match for option %s, will return first match. Matches are: %r.", option, matches)
    elif lMatches == 0:
      self._logger.fatal("Cannot find job submission option: %s", option, KeyError)
    return matches[0]

  def parseExecStr(self, execStr):
    retStr = ''
    import textwrap
    execStr = [textwrap.dedent(l) for l in execStr.split('\n')]
    execStr = [l for l in execStr if l not in (';','"','')]
    if execStr[-1][-2:] != ';"': 
      if execStr[-1][-1] == '"':
        execStr[-1] = execStr[-1][:-1] + ';"'
      else:
        execStr[-1] += ';"' 
    for i, l in enumerate(execStr):
      if i == 0:
        moreSpaces = 2
      else:
        moreSpaces = 4
      retStr += self._formated_line( l, moreSpaces = moreSpaces )
    return retStr

  def run(self, str_):
    """
      Run the command
    """
    os.system(str_)

  def _nSpaces(self):
    "Specify the base number of spaces after entering the command."
    return len(self.prog) + 1

  def _formated_line(self, line, moreSpaces = 0 ):
    return (' ' * (self._nSpaces() + moreSpaces) ) + line + ' \\\n'
    
  def _parse_standard_args(self):
    """
    Here we deal with the standard arguments
    """
    cmd_str = ''
    nSpaces = self._nSpaces()
    # Add extra arguments
    for name, value in get_attributes(self):
      csv = False
      if name.startswith(self.prefix):
        name = name.replace(self.prefix,'',1)
        if name.startswith('_Group'):
          if value:
            name = value
            value = True
          else:
            continue
        elif name.startswith('_CSV'):
          csv = True
          name = name.replace('_CSV','',1)
        name = name[:2].replace('_', '-') + name[2:]
      else:
        continue
      tVal = type(value)
      if tVal == bool and value:
        cmd_str +=  self._formated_line( name )
      elif value:
        if isinstance(value, list):
          if csv:
            cmd_str +=  self._formated_line( name + '=' + ','.join( [str(v) for v in value]) )
          else:
            cmd_str +=  self._formated_line( name + '=' + ' '.join( [str(v) for v in value]) )
        else:
          cmd_str +=  self._formated_line( name + '=' + str(value) )
    return cmd_str

  def _run_command(self, full_cmd_str):
    # We show command:
    self._logger.info("Command:\n%s", full_cmd_str)
    full_cmd_str = re.sub('\\\\ *\n','', full_cmd_str )
    full_cmd_str = re.sub(' +',' ', full_cmd_str)
    self._logger.debug("Command without spaces:\n%s", full_cmd_str)
    # And run it:
    if not self.dry_run:
      self.run(full_cmd_str)
      pass


class _JobSubmitArgumentGroup( _JobSubmitActionsContainer, argparse._ArgumentGroup ):
  def __init__(self, *args, **kw):
    self.prefix = kw.pop('prefix')
    _JobSubmitActionsContainer.__init__(self)
    argparse._ArgumentGroup.__init__(self,*args,**kw)

class _JobSubmitMutuallyExclusiveGroup( _JobSubmitActionsContainer, argparse._MutuallyExclusiveGroup ):
  def __init__(self, *args, **kw):
    self.prefix = kw.pop('prefix')
    _JobSubmitActionsContainer.__init__(self)
    argparse._MutuallyExclusiveGroup.__init__(self,*args,**kw)
