__all__ = ['ProjectGit','RingerCoreGit','GitConfiguration']

import os
from RingerCore.Configure import Configure, RCM_GRID_ENV, cmd_exists, NotSet
from RingerCore.parsers.Git import createGitParser
from RingerCore.Logger import Logger

class GitConfiguration( Configure ):
  """
  This class should be used to create a singleton in each python module in
  order to capture its git tag
  """

  tag = property( Configure.get, Configure.set )

  def __init__( self
              , name
              , fname
              , tagArgStr = None
              , tagStr = '.*-?(\d+-)+\d+$'
              ):
    """
    -> fname: path pointing to the corresponding --git-dir of the module or any
    file within it;
    -> tagArgStr: in case a parser is to be created, then pass what should be
    the argument to be parsed;
    -> tagStr: the format of the tag object to be used as a re object.
    """
    self.name = name
    self._fname = fname
    self._parser = None
    self._tagStr = tagStr
    Configure.__init__(self)
    if tagArgStr: self._parser = createGitParser(self, tagArgStr)
    self._tagArgStr = tagArgStr

  def auto( self ):
    self._logger.debug("Using automatic configuration to retrieve git tag.")
    # Check in parser whether we can get the configuration
    if self._parser:
      args, argv = self._parser.parse_known_args()
      if args.tag not in (None, NotSet):
        import sys
        # Consume option
        sys.argv = sys.argv[:1] + argv
    if self.configured():
      self._logger.debug("Masked git tag version using parser.")
      return
    # If we failed to retrieve it using parser, we interrupt program on the
    # GRID and inform the user:
    if RCM_GRID_ENV:
      self._logger.fatal("Attempted to retrieve git directory while on CERN GRID!")
    # We couldn't get using parser, then we will retrieve it using the git command:
    self._moduleName, self._choice, self._path = self._git_description()

  def retrieve(self, val):
    if not isinstance(val, basestring):
      self._logger.fatal("Attempted to retrieve non string git tag: %s", val )
    return val

  @property
  def path(self):
    return self._path

  @property
  def moduleName(self):
    return self._moduleName

  @moduleName.setter
  def moduleName(self, value):
    if self.configured():
      self._logger.fatal("Cannot change moduleName after it is configured.")
    else:
      self._moduleName = value

  def _git_description( self, getModuleProject = False ):
    # FIXME: probably its needed to kill the git_version_cmd to avoid 
    # having the git.lock file kept until the end of job execution
    import re
    if not cmd_exists('git'):
      self._logger.warning("Couldn't find git commnad.")
    git_dir = os.path.realpath( self._fname )
    if os.path.isfile( git_dir ):
      git_dir = os.path.dirname( git_dir )
    # Protect against RootCore file arrangement
    if os.path.basename( git_dir ) == "python":
      git_dir = os.path.dirname( git_dir )
    git_dir = os.path.join( git_dir, '.git' )
    if os.path.isfile( git_dir ):
      old_dir = git_dir
      with open( git_dir ) as f:
        relative_path = f.readline().split(' ')[-1].strip('\n')
      git_dir = os.path.realpath( os.path.join( os.path.dirname( old_dir ), relative_path ) )
    import subprocess
    if getModuleProject: git_dir = os.path.abspath( os.path.join( os.path.dirname( git_dir ), '..' ) )
    # Strip any possible remaining .git directories:
    git_dir = re.sub('/.git(/modules)?/?$','',git_dir)
    git_dir_cmd = subprocess.Popen(["git", "--git-dir", git_dir, "rev-parse", "--show-toplevel"]
                                   , stdout=subprocess.PIPE, stderr=subprocess.PIPE
                                   , cwd=git_dir)
    (output, stderr) = git_dir_cmd.communicate()
    if git_dir_cmd.returncode:
      git_dir = os.path.join(git_dir, '.git')
      git_dir_cmd = subprocess.Popen(["git", "--git-dir", git_dir, "rev-parse", "--show-toplevel"]
                                     , stdout=subprocess.PIPE, stderr=subprocess.PIPE
                                     , cwd=git_dir)
      (output, stderr) = git_dir_cmd.communicate()
    # Strip casual .git in output
    output = re.sub('/.git$','',git_dir)
    # Assume that module path is the remaining output:
    module_path = output.rstrip('\n')
    if not os.path.isdir( module_path ):
      self._logger.warning("Couldn't determine git dir. Retrieved %s as input file and tested for %s as git dir", self._fname, git_dir, RuntimeWarning)
    module_name = os.path.basename( module_path )
    git_version_cmd = subprocess.Popen(["git", "--git-dir", git_dir, "describe"
                                      ,"--always","--dirty",'--tags'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, stderr) = git_version_cmd.communicate()
    tag = output.rstrip('\n')
    if git_version_cmd.returncode:
      self._logger.warning("git command failed with code %d. Error message returned was:\n%s", git_version_cmd.returncode, stderr, RuntimeWarning)
    if not module_name in tag:
      tag = module_name + '-' + tag
    return module_name, tag, module_path

  def is_clean(self):
    import re
    return bool(re.match(self._tagStr,self.tag))

  def dumpToParser(self):
    if not self._parser:
      self._logger.fatal("Attempted to get parser option, but no parser is "
                         "available. Make sure to add the tagArgStr to the "
                         "GitConfiguration object")
    return self._tagArgStr + " '" + self.moduleName + "' '" + self.tag + "'"

  #def __lt__(self, val):
  #  return self.get() < val

  #def __le__(self, val):
  #  return self.get() <= val

  #def __eq__(self, val):
  #  return self.get() == val

  #def __ne__(self, val):
  #  return self.get() != val

  #def __gt__(self, val):
  #  return self.get() > val

  #def __ge__(self, val):
  #  return self.get() >= val

class __ConfigureProjectGit( GitConfiguration ):
  """
  Project git retriever
  """

  def auto( self ):
    self._logger.debug("Using automatic configuration to retrieve git project version tag.")
    if self._parser:
      args, argv = self._parser.parse_known_args()
      if args.tag not in (None, NotSet):
        import sys
        # Consume option
        sys.argv = sys.argv[:1] + argv
    try:
      self._moduleName, self._choice, self._path = self._git_description( getModuleProject = True )
    except Exception, e:
      self._logger.warning('Couldn\'t identify the running project')
      self._moduleName = ''
      self._choice = ''
      self._path = ''

  # TODO if we can retrieve the module, then we get its git version using
  # _git_description
  #def moduleTag( self, moduleName ):

# This instance parse the git project version tag
ProjectGit = __ConfigureProjectGit( 'ProjectGit', __file__, tagArgStr='--project-info')
del __ConfigureProjectGit

# This instance parse the git version tag of the RingerCore module
RingerCoreGit = GitConfiguration( 'RingerCoreGit', __file__, tagArgStr='--ringer-core-info')

