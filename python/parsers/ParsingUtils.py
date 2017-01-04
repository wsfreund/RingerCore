__all__ = ['argparse','ArgumentParser','JobSubmitArgumentParser', 'JobSubmitNamespace']

from RingerCore.util import get_attributes
import re

try:
  import argparse
except ImportError:
  from RingerCore.parsers import __py_argparse as argparse

from RingerCore.Logger import Logger, LoggingLevel
from RingerCore.util import BooleanStr, EnumStringification

class _EraseGroup( Exception ):
  """
  Indicate that a group should be erased.
  """
  pass

class _ActionsContainer( object ):

  def add_argument(self, *args, **kwargs):
    if 'type' in kwargs and issubclass(kwargs['type'], EnumStringification):
      lType = kwargs['type']
      # Make sure that there will be registered the type and the action that
      # will be used for it:
      if not lType in self._registries['type']:
        self.register('type', lType, lType.retrieve)
      # Deal with the help option:
      help_str = kwargs.pop('help','').rstrip(' ')
      if not '.' in help_str[-1:]: help_str += '. '
      if help_str[-1:] != ' ': help_str += ' '
      help_str += "Possible options are: "
      from operator import itemgetter
      val = sorted(get_attributes( kwargs['type'], getProtected = False), key=itemgetter(1))
      help_str += str([v[0] for v in val])
      help_str += ', or respectively equivalent to the integers: '
      help_str += str([v[1] for v in val])
      kwargs['help'] = help_str
      # Deal with BooleanStr special case:
      if issubclass(lType, BooleanStr):
        if kwargs.pop('nargs','?') != '?':
          raise ValueError('Cannot specify nargs different from \'?\' when using boolean argument')
        kwargs['nargs'] = '?'
        kwargs['const'] = BooleanStr.retrieve( kwargs.pop('const','True') )
    argparse._ActionsContainer.add_argument(self, *args, **kwargs)

  def add_argument_group(self, *args, **kwargs):
    group = _ArgumentGroup(self, *args, **kwargs)
    self._action_groups.append(group)
    return group

  def add_mutually_exclusive_group(self, **kwargs):
    group = _MutuallyExclusiveGroup(self, **kwargs)
    self._mutually_exclusive_groups.append(group)
    return group

  def delete_arguments(self, *vars_, **kw):
    "Remove all specified arguments from the parser"
    # Remove arguments from the groups:
    popIdxs = []
    _visited_groups = kw.pop('_visited_groups',[])
    for idx, group in enumerate(self._action_groups):
      try:
        if group in _visited_groups:
          raise _EraseGroup()
        _visited_groups.append( group )
        group.delete_arguments( *vars_, _visited_groups = _visited_groups )
      except _EraseGroup:
        popIdxs.append(idx)
    for idx in reversed(popIdxs):
      #print 'deleting group:', self._action_groups[idx].title 
      self._action_groups.pop( idx )
    popIdxs = []
    # Repeat procedure for the mutually exclusive groups:
    _visited_mutually_exclusive_groups = kw.pop('_visited_mutually_exclusive_groups',[])
    for idx, group in enumerate(self._mutually_exclusive_groups):
      try:
        if group in _visited_mutually_exclusive_groups:
          raise _EraseGroup()
        _visited_mutually_exclusive_groups.append(group)
        group.delete_arguments( *vars_, _visited_mutually_exclusive_groups = _visited_mutually_exclusive_groups )
      except _EraseGroup:
        popIdxs.append(idx)
    for idx in reversed(popIdxs):
      #print 'deleting mutually exclusive group:', self._mutually_exclusive_groups[idx].title 
      self._mutually_exclusive_groups.pop( idx )
    # Treat our own actions:
    popIdxs = []
    for var in vars_:
      for idx, action in enumerate(self._actions):
        if action.dest == var:
          popIdxs.append( idx )
          popOptKeys = []
          for optKey, optAction in self._option_string_actions.iteritems():
            if optAction.dest == var:
              popOptKeys.append(optKey)
          for popOpt in reversed(popOptKeys):
            #print "(delete) poping key:", popOpt
            self._option_string_actions.pop(popOpt)
          break
    popIdxs = sorted(popIdxs)
    for idx in reversed(popIdxs):
      #print "(delete) popping action,", idx, self._actions[idx].dest
      self._actions.pop(idx)
    # Raise if we shouldn't exist anymore:
    if isinstance(self, (_MutuallyExclusiveGroup, _ArgumentGroup)) and \
       not self._group_actions and \
       not self._defaults:
       raise _EraseGroup()

  def suppress_arguments(self, **vars_):
    """
    Suppress all specified arguments from the parser by assigning a default
    value to them. It must be specified through a key, value pair, the key
    being the variable destination, and the value the value it should always
    take.
    """
    _visited_groups = vars_.pop('_visited_groups',[])
    for idx, group in enumerate(self._action_groups):
      if group in _visited_groups:
        #print 'already visited group:', group.title, "|(", idx, "/", len(self._action_groups), ")"
        continue
      _visited_groups.append(group)
      #print "supressing:", group.title, "|(", idx, "/", len(self._action_groups), ")"
      group.suppress_arguments( _visited_groups = _visited_groups, **vars_)
    _visited_mutually_exclusive_groups = vars_.pop('_visited_mutually_exclusive_groups',[])
    for idx, group in enumerate(self._mutually_exclusive_groups):
      if group in _visited_mutually_exclusive_groups:
        #print '(mutually) already visited group:', group.title, "|(", idx, "/", len(self._mutually_exclusive_groups), ")"
        continue
      _visited_mutually_exclusive_groups.append(group)
      #print "(mutually) supressing:", group.title, "|(", idx, "/", len(self._mutually_exclusive_groups), ")"
      group.suppress_arguments( _visited_mutually_exclusive_groups = _visited_mutually_exclusive_groups, **vars_)
    popIdxs = []
    for var, default in vars_.iteritems():
      for idx, action in enumerate(self._actions):
        if action.dest == var:
          popIdxs.append( idx )
          popOptKeys = []
          for optKey, optAction in self._option_string_actions.iteritems():
            if optAction.dest == var:
              popOptKeys.append(optKey)
          for popOpt in reversed(popOptKeys):
            #print "poping key:", popOpt
            self._option_string_actions.pop(popOpt)
          break
    popIdxs = sorted(popIdxs)
    for idx in reversed(popIdxs):
      #print "popping action,", idx, self._actions[idx].dest
      self._actions.pop(idx)
    # Set defaults:
    self.set_defaults(**vars_)

  def get_groups(self, **kw):
    """
    Returns a list containing all groups within this object
    """
    groups = self._action_groups
    groups.extend( self._mutually_exclusive_groups )
    return groups

  def make_adjustments(self):
    """
    Remove empty groups
    """
    groups = self.get_groups()
    toEliminate = set()
    for idx, group in enumerate(groups):
      if idx in toEliminate:
        continue
      if not group._group_actions:
        for key in group._defaults.keys():
          if key in self._defaults:
            group._defaults.pop(key)
        self.set_defaults(**group._defaults)
        toEliminate |= {idx,}
        continue
      # This seems not to be needed as the argparse deals with it:
      ##Make sure that we have all grouped arguments with common titles
      ##merged in only one group. This avoids having several properties 
      #sameTitleIdxs = [idx + qidx for qidx, qgroup in enumerate(groups[idx:]) if group.title == qgroup.title and qgroup is not group]
      #for sameTitleIdx in sameTitleIdxs:
      #  # Add actions:
      #  group._actions.extend([action for action in groups[sameTitleIdxs]._actions if action not in group._actions])
      #  # And optinal strings
      #  group._option_string_actions.update({item for item in groups[sameTitleIdxs]._option_string_actions if not item[0] in group._option_string_actions})
      #  # Sign it to be eliminated
      #  toEliminate |= {sameTitleIdx,}
    # Now eliminate the groups
    lActions = len(self._action_groups)
    for idx in reversed(list(toEliminate)):
      if idx < lActions:
        #print "(adjustments) eliminating:", self._action_groups[idx].title
        self._action_groups.pop(idx)
      else:
        #print "(adjustments) eliminating mutually exclusive:", self._mutually_exclusive_groups[idx].title
        self._mutually_exclusive_groups.pop(idx-lActions)

class ArgumentParser( _ActionsContainer, argparse.ArgumentParser ):
  """
  This class has the following extra features over the original ArgumentParser:

  -> add_boolean_argument: This option can be used to declare an argument which
  may be declared as a radio button, that is, simply:
     --option
  where it will be set to True, or also specifying its current status through the
  following possible ways:
     --option True
     --option true
     --option 1
     --option 0
     --option False
     --option false

  -> When type is a EnumStringification, it will automatically transform the input
  value using retrieve;
  """

  def __init__(self,*l,**kw):
    _ActionsContainer.__init__(self)
    argparse.ArgumentParser.__init__(self,*l,**kw)
    self.register('type', BooleanStr, BooleanStr.retrieve)
    if 'parents' in kw:
      parents = kw['parents']
      for parent in parents:
        for key, reg in parent._registries.iteritems():
          if not key in self._registries:
            self._registries[key] = reg
          else:
            for key_act, act in reg.iteritems():
              if not key_act in self._registries[key]:
                self.register(key, key_act, act)


class _JobSubmitActionsContainer( _ActionsContainer ):

  def add_job_submission_option(self, *l, **kw):
    kw['dest'], kw['metavar'] = self._getDest(*l)
    self.add_argument(*l, **kw)

  def add_job_submission_csv_option(self, *l, **kw):
    kw['dest'], kw['metavar'] = self._getDest( *l, extraSpec = '_CSV')
    if kw.pop('nargs','+') != '+':
      raise ValueError('Cannot specify nargs different from \'+\' when using csv option')
    kw['nargs'] = '+'
    if not 'default' in kw:
      kw['default'] = []
    self.add_argument(*l, **kw)

  def add_job_submission_option_group(self, *l, **kw):
    "Add a group of options that will be set if true or another group to be set when false"
    kw['dest'], kw['metavar'] = self._getDest( *l, extraSpec = '_Group')
    self.add_argument(*l, **kw)

  def add_job_submission_suboption(mainOption, suboption, *l, **kw):
    kw['dest'], kw['metavar'] = self._getDest(*[mainOption])[0] + ' ' + suboption, suboption.upper()
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
        return self.prefix + extraSpec + '__' + l[idx].lstrip('--'), l[idx].lstrip('--').upper()
      except AttributeError:
        raise AttributeError("Class (%s) prefix attribute was not specified." % self.__class__.__name__)
    else:
      search = [item.startswith('-') for item in l]
      if search and any(search):
        idx = search.index( True ) 
        try:
          return self.prefix + extraSpec + '_' + l[idx].lstrip('-'), l[idx].lstrip('-').upper()
        except AttributeError:
          raise AttributeError("Class (%s) prefix attribute was not specified." % self.__class__.__name__)
    return 


class JobSubmitArgumentParser( _JobSubmitActionsContainer, ArgumentParser ):
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
    ArgumentParser.__init__(self,*l,**kw)
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
    import os
    self.fcn = os.system

  def __call__(self):
    "Execute the command"
    self.run()

  def run(self):
    "Execute the command"
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
      self.fcn(full_cmd_str)
      pass

class _ArgumentGroup( _ActionsContainer, argparse._ArgumentGroup ):
  def __init__(self, *args, **kw):
    _ActionsContainer.__init__(self)
    argparse._ArgumentGroup.__init__(self,*args,**kw)
    self.register('type', BooleanStr, BooleanStr.retrieve)

class _MutuallyExclusiveGroup( _ActionsContainer, argparse._MutuallyExclusiveGroup ):
  def __init__(self, *args, **kw):
    _ActionsContainer.__init__(self)
    argparse._MutuallyExclusiveGroup.__init__(self,*args,**kw)
    self.register('type', BooleanStr, BooleanStr.retrieve)

class _JobSubmitArgumentGroup( _JobSubmitActionsContainer, _ArgumentGroup ):
  def __init__(self, *args, **kw):
    self.prefix = kw.pop('prefix')
    _JobSubmitActionsContainer.__init__(self)
    _ArgumentGroup.__init__(self,*args,**kw)

class _JobSubmitMutuallyExclusiveGroup( _JobSubmitActionsContainer, _MutuallyExclusiveGroup ):
  def __init__(self, *args, **kw):
    self.prefix = kw.pop('prefix')
    _JobSubmitActionsContainer.__init__(self)
    _MutuallyExclusiveGroup.__init__(self,*args,**kw)
