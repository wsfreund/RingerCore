__all__ = [ 'argparse','ArgumentParser', 'ArgumentError', 'BooleanRetrieve']

from RingerCore.util import get_attributes
import re, textwrap, argparse

ArgumentError = argparse.ArgumentError

from RingerCore.Configure import BooleanStr, EnumStringification, Configure

class BooleanRetrieve( argparse.Action ):

  def __init__( self
              , dest = None
              , option_strings = []
              , nargs=None
              , const=None
              , default=None
              , type=None
              , choices=None
              , required=False
              , help=None
              , metavar=None ):
    super(BooleanRetrieve, self).__init__( option_strings = option_strings
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
    if value is None:
      value = self.const if self.const is not None else True
    else:
      value = BooleanStr.retrieve( value )
    setattr(namespace, self.dest, value)

class _EraseGroup( Exception ):
  """
  Indicate that a group should be erased.
  """
  pass

class _ActionsContainer( object ):

  def add_argument(self, *args, **kwargs):
    if 'type' in kwargs:
      lType = kwargs['type']
      if isinstance(lType,type):
        if issubclass(lType, EnumStringification):
          # Deal with the help option:
          help_str = ' '.join(textwrap.wrap(kwargs.pop('help','')))
          if not '.' in help_str[-2:]: help_str += '. '
          if help_str[-1:] != ' ': help_str += ' '
          # Append possible options
          help_str += """Possible options, that can equivalently be input either
          as a string %s or an integer as in the template (Option, 0), are: """ % ("(case insensitive)" if lType._ignoreCase else "(case sensitive)")
          help_str += str(kwargs['type'].optionList()).strip("[]").replace("'","").replace('),',');')
          kwargs['help'] = help_str
          # Deal with BooleanStr special case:
          if issubclass(lType, BooleanStr):
            # Accept it not to be specified
            if kwargs.pop('nargs','?') != '?':
              raise ValueError('Cannot specify nargs different from \'?\' when using boolean argument')
            kwargs['nargs'] = '?'
            if not 'default' in kwargs:
              kwargs['default'] = False
            if not 'action' in kwargs:
              del kwargs['type']
              kwargs['action'] = BooleanRetrieve
            else:
              if not lType in self._registries['type']: self.register('type', lType, lType.retrieve)
          else:
            # Make sure that there will be registered the type and the action that
            # will be used for it:
            if not lType in self._registries['type']:
              self.register('type', lType, lType.retrieve)
        elif issubclass(lType, Configure):
          # Start a default Configure instance
          cConf = lType()
          kwargs['type'] = cConf
          if not 'default' in kwargs: kwargs['default'] = cConf
          if not cConf in self._registries['type']: self.register('type', cConf, cConf.parser_set)
      else: # not an instance of type
        if isinstance(lType, Configure):
          kwargs['type'] = lType
          if not 'default' in kwargs: kwargs['default'] = lType
          if not lType in self._registries['type']: self.register('type', lType, lType.parser_set )
    if 'help' in kwargs and isinstance(kwargs['help'],basestring) and kwargs.get('default',None) is not argparse.SUPPRESS:
      kwargs['help'] = kwargs['help'].rstrip(' \n')
      if not(kwargs['help'].endswith('.') or kwargs['help'].endswith('. ')): kwargs['help'] += '. '
      if kwargs['help'].endswith('.'): kwargs['help'] += ' '
      default = kwargs.get('default', None)
      if 'type' in kwargs and isinstance(lType,type) and issubclass(lType, EnumStringification):
        kwargs['help'] += 'Default value is: %s.' % ( lType.tostring(default) if default is not None else None )
      elif 'type' in kwargs and ( ( isinstance(lType,type) and issubclass(lType, Configure) ) or isinstance(lType,Configure) ):
        kwargs['help'] += 'Default value is: %r.' % default
      else:
        kwargs['help'] += 'Default value is: %s.' % default
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
    if ( isinstance(self, (_MutuallyExclusiveGroup, _ArgumentGroup)) and
         not self._group_actions and
         not self._defaults ):
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
        #for key in group._defaults.keys():
        #  if key in self._defaults:
        #    group._defaults.pop(key)
        #self.set_defaults(**group._defaults)
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
        self._action_groups.pop(idx)
      else:
        self._mutually_exclusive_groups.pop(idx-lActions)

class ArgumentParser( _ActionsContainer, argparse.ArgumentParser ):
  """
  This class has the following extra features over the original ArgumentParser:

  -> When type is a EnumStringification, it will automatically transform the input
  value using retrieve;
  """

  def __init__(self,*l,**kw):
    _ActionsContainer.__init__(self)
    if 'parents' in kw:
      for p in kw['parents']:
        if not isinstance(p, argparse.ArgumentParser):
          raise ValueError("Attempted to add parents of non argparse.ArgumentParser type: %r", p)
      #from copy import copy
      #kw['parents'] = [copy(p) for p in kw['parents']]
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

  def error(self, message):
    """
    Raise ArgumentError instead of exiting
    """
    raise ArgumentError( None, message )

  def _print_message(self, message, file=None):
    from RingerCore.Logger import Logger
    logger = Logger.getModuleLogger( self.__class__.__name__ )
    if message:
      logger.info('\n' + message)

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

