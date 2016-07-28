import os
import re
import textwrap
__all__ = ['GridNamespace',  'gridParser', 'inGridParser', 'ioGridParser', 'outGridParser']

from RingerCore.Logger import Logger
from RingerCore.util import get_attributes
from RingerCore.parsers.Logger import LoggerNamespace

try:
  import argparse
except ImportError:
  from RingerCore.parsers import __py_argparse as argparse

################################################################################
# Grid parser related objects
################################################################################
# Basic grid parser
gridParser = argparse.ArgumentParser(add_help = False)
gridParserGroup = gridParser.add_argument_group('GRID Arguments', '')
gridParserGroup.add_argument('--site',default = 'AUTO',
    help = "The site location where the job should run.",
    nargs='?', required = False,
    dest = 'grid_site')
grid_shortSites = 'ANALY_CERN_SHORT,ANALY_CONNECT_SHORT,ANALY_BNL_SHORT'
gridParserGroup.add_argument('--excludedSite', 
    #default = 'ANALY_CERN_CLOUD,ANALY_CERN_SHORT,ANALY_CONNECT_SHORT,ANALY_BNL_SHORT', # Known bad sites
    #default = 'ANALY_CERN_CLOUD,ANALY_SLAC,ANALY_CERN_SHORT,ANALY_CONNECT_SHORT,ANALY_BNL_SHORT,ANALY_BNL_EC2E1,ANALY_SWT2_CPB', # Known bad sites
    help = "The excluded site location.", nargs='?',
    required = False, dest = 'grid_excludedSite')
gridParserGroup.add_argument('--debug', default = '--skipScout',
    const='--express --debugMode --allowTaskDuplication --disableAutoRetry --useNewCode', dest='gridExpand_debug',
    help = "Submit GRID job on debug mode.", action='store_const',
    required = False )
gridParserGroup.add_argument('--nJobs', nargs='?', type=int,
    required = False, dest = 'grid_nJobs',
    help = """Number of jobs to submit.""")
gridParserGroup.add_argument('--excludeFile', nargs='?', 
    required = False, default = '"*.o,*.so,*.a,*.gch,Download/*,InstallArea/*"', dest = 'grid_excludeFile',
    help = """Files to exclude from environment copied to grid.""")
gridParserGroup.add_argument('--disableAutoRetry', action='store_true',
    required = False, dest = 'grid_disableAutoRetry',
    help = """Flag to disable auto retrying jobs.""")
gridParserGroup.add_argument('--followLinks', action='store_true',
    required = False, dest = 'grid_followLinks',
    help = """Flag to disable auto retrying jobs.""")
gridParserGroup.add_argument('--mergeOutput', action='store_true',
    required = False, dest = 'grid_mergeOutput',
    help = """Flag to enable merging output.""")
gridParserGroup.add_argument('--mergeScript', 
    required = False, dest = 'grid_mergeScript',
    help = """The script for merging the files. E.g.: 'your_merger.py -o %%OUT -i %%IN'""")
gridParserGroup.add_argument('--extFile', nargs='?',
    required = False, dest = 'grid_extFile', default='',
    help = """External file to add.""")
gridParserGroup.add_argument('--match', 
    required = False, dest = 'grid_match',
    help = """Use only files matching with given pattern.""")
gridParserGroup.add_argument('--antiMatch', 
    required = False, dest = 'grid_antiMatch',
    help = """Use all files but those matching with given pattern.""")
gridParserGroup.add_argument('--cloud', nargs='?',
    required = False, default=False, dest = 'grid_cloud',
    help = """The cloud where to submit the job.""")
gridParserGroup.add_argument('--nGBPerJob', nargs='?',
    required = False, dest = 'grid_nGBPerJob',
    help = """Maximum number of GB per job.""")
gridParserGroup.add_argument('--skipScout', action='store_true',
    required = False, dest = 'grid_skipScout',
    help = """Flag to disable auto retrying jobs.""")
gridParserGroup.add_argument('--memory', type=int,
    required = False, dest = 'grid_memory',
    help = """Needed memory to run in MB.""")
gridParserGroup.add_argument('--long', action='store_true',
    required = False, dest = 'grid_long',
    help = """Submit for long queue.""")
gridParserGroup.add_argument('--useNewCode', action='store_true',
    required = False, dest = 'grid_useNewCode',
    help = """Flag to disable auto retrying jobs.""")
gridParserGroup.add_argument('--dry-run', action='store_true',
    help = """Only print grid resulting command, but do not execute it.
            Used for debugging submission.""")
gridParserGroup.add_argument('--allowTaskDuplication', action='store_true',
    required = False, dest = 'grid_allowTaskDuplication',
    help = """Flag to disable auto retrying jobs.""")
mutuallyEx1 = gridParserGroup.add_mutually_exclusive_group( required=False )
mutuallyEx1.add_argument('-itar','--inTarBall', 
    metavar='InTarBall', nargs = '?', dest = 'grid_inTarBall',
    help = "The environemnt tarball for posterior usage.")
mutuallyEx1.add_argument('-otar','--outTarBall',
    metavar='OutTarBall',  nargs = '?', dest = 'grid_outTarBall',
    help = "The environemnt tarball for posterior usage.")
################################################################################
## Temporary classes only to deal with diamond inherit scheme
_inParser = argparse.ArgumentParser(add_help = False)
_inParserGroup = _inParser.add_argument_group('GRID Input Dataset Arguments', '')
_inParserGroup.add_argument('--inDS','-i', action='store', 
                       required = True, dest = 'grid_inDS',
                       help = "The input Dataset ID (DID)")
_inParserGroup.add_argument('--secondaryDSs', action='store', nargs='+',
                       required = False, dest = 'grid_secondaryDS',
                       help = "The secondary Dataset ID (DID), in the format name:nEvents:place")
_inParserGroup.add_argument('--forceStaged', action='store_true',
    required = False,  dest = 'grid_forceStaged', default = False,
    help = """Force files from primary DS to be staged to local
    disk, even if direct-access is possible.""")
_inParserGroup.add_argument('--forceStagedSecondary', action='store_true',
    required = False, dest = 'grid_forceStagedSecondary',
    help = """Force files from secondary DS to be staged to local
              disk, even if direct-access is possible.""")
_inParserGroup.add_argument('--reusableSecondary', nargs='?',
    required = False, dest = 'grid_reusableSecondary',
    help = """Allow reuse secondary dataset.""")
_inParserGroup.add_argument('--nFiles', nargs='?', type=int,
    required = False, dest = 'grid_nFiles',
    help = """Number of files to run.""")
_inParserGroup.add_argument('--nFilesPerJob', nargs='?', type=int,
    required = False, dest = 'grid_nFilesPerJob',
    help = """Number of files to run per job.""")
################################################################################
_outParser = argparse.ArgumentParser(add_help = False)
_outParserGroup = _inParser.add_argument_group('GRID Output Dataset Arguments', '')
_outParserGroup.add_argument('--outDS','-o', action='store', 
                        required = True, dest = 'grid_outDS',
                        help = "The output Dataset ID (DID)")
_outParserGroup.add_argument('--outputs', required = True, dest = 'grid_outputs',
    help = """The output format.""")
################################################################################
## Input and output grid parser
ioGridParser = argparse.ArgumentParser(add_help = False, 
                                       parents = [_inParser, _outParser, gridParser])

## Input grid parser
inGridParser = argparse.ArgumentParser(add_help = False, 
                                       parents = [_inParser, gridParser])

## Output grid parser
outGridParser = argparse.ArgumentParser(add_help = False, 
                                        parents = [_outParser, gridParser])
# Remove temp classes
del _inParser, _outParser
################################################################################
## GridNamespace
# Make sure to use GridNamespace specialization for the used package when
# parsing arguments.
class GridNamespace( LoggerNamespace, Logger ):
  """
    Improves argparser workspace object to support creating a string object
    with the input options.
  """

  #noNumyPySites = ['ANALY_SWT2_CPB','ANALY_BNL_EC2E1']

  def __init__(self, prog = 'prun', **kw):
    Logger.__init__( self, kw )
    LoggerNamespace.__init__( self, **kw )
    self.prog = prog

  def __call__(self):   
    self.run_cmd()

  def setBExec(self, value):
    """
      Add a build execute command.
    """
    if len(value) > 0 and value[0] != '"':
      value = '"' + value
    if value[-1] != '"':
      value += '"'
    self.bexec = value 

  def setExec(self, value):
    """
      Add the execution command on grid.
    """
    if len(value) < 1 or value[0] != '"':
      value = '"' + value
    if len(value) < 2 or value[-1] != '"':
      value += '"'
    self.exec_ = value 

  def pre_download(self):
    """
      Packages which need special libraries downloads to install should inherit
      from this class and overload this method to download needed libraries.
    """
    pass

  def extFile(self):
    """
      Return a comma separated list of extFiles needed by this GridNamespace.
    """
    return ''

  def __run(self, str_):
    """
      Run the command
    """
    self.pre_download()
    workDir=os.path.expandvars("$ROOTCOREBIN/..")
     # We need to cd to this dir so that prun accepts the submission
    os.chdir(workDir)
    os.system(str_)

  def nSpaces(self):
    return len(self.prog) + 1
    
  def run_cmd(self):
    """
      Execute parsed arguments.
    """
    # Try to change our level if we have an output_level option:
    try:
      self.setLevel( self.output_level )
    except AttributeError:
      pass
    # Add program to exec and build exec if available
    full_cmd_str = self.prog + (' --bexec ' + self.bexec if hasattr(self,'bexec') else '') + ' \\\n'
    # The number of spaces to add to each following option to improve readability:
    nSpaces = self.nSpaces()
    # Add execute grid command if available
    if hasattr(self,'exec_'):
      full_cmd_str += (' ' * nSpaces) + '--exec' + ' \\\n'
      exec_str = [textwrap.dedent(l) for l in self.exec_.split('\n')]
      exec_str = [l for l in exec_str if l not in (';','"','')]
      if exec_str[-1][-2:] != ';"': 
        exec_str[-1] += ';"' 
      for i, l in enumerate(exec_str):
        if i == 0:
          moreSpaces = 2
        else:
          moreSpaces = 4
        full_cmd_str += (' ' * (nSpaces + moreSpaces) ) + l + ' \\\n'
    # Add needed external files:
    if self.extFile() and not self.extFile() in self.grid_extFile:
      if len(self.grid_extFile):
        self.grid_extFile += ','
      self.grid_extFile += self.extFile()
    if self.grid_long:
      if self.grid_excludedSite:
        for shortSite in grid_shortSites.split(','):
          if not shortSite in self.grid_excludedSite:
            self.grid_excludedSite += ',' + shortSite
      else:
        self.grid_excludedSite = grid_shortSites
    # Add extra arguments
    for name, value in get_attributes(self):
      if 'grid_' in name:
        name = name.replace('grid_','--')
        if name == '--outDS' and len(value) > 132:
          raise ValueError(('Size of --outDS is larger (%d) than 132 char, '
              'the maximum value allowed by CERN grid. '
              'Container name is valid until: %s') % (len(value), value[:132]))
      elif 'gridExpand_' in name:
        if value:
          name = value
          value = True
        else:
          continue
      else:
        continue
      tVal = type(value)
      if tVal == bool and value:
        full_cmd_str += (' ' * nSpaces) + name + ' \\\n'
      elif value:
        if isinstance(value, list):
          full_cmd_str += (' ' * nSpaces) + name + '=' + ','.join(value) + ' \\\n'
        else:
          full_cmd_str += (' ' * nSpaces) + name + '=' + str(value) + ' \\\n'
    # Now we show command:
    self._logger.info("Command:\n%s", full_cmd_str)
    full_cmd_str = re.sub('\\\\ *\n','', full_cmd_str )
    full_cmd_str = re.sub(' +',' ', full_cmd_str)
    self._logger.debug("Command without spaces:\n%s", full_cmd_str)
    # And run it:
    if not self.dry_run:
      self.__run(full_cmd_str)
      pass



