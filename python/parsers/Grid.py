import os
import re
__all__ = ['GridNamespace',  'gridParser', 'inGridParser', 'ioGridParser', 'outGridParser']

from RingerCore.Logger import Logger
from RingerCore.parsers.Logger import LoggerNamespace
from RingerCore.parsers.ParsingUtils import JobSubmitArgumentParser, JobSubmitNamespace

################################################################################
# Grid parser related objects
################################################################################
class GridJobArgumentParser( JobSubmitArgumentParser ):
  prefix = 'grid'

# Basic grid parser
gridParser = GridJobArgumentParser(add_help = False)
gridParserGroup = gridParser.add_argument_group('GRID Arguments', '')
gridParserGroup.add_job_submission_option('--site',default = 'AUTO',
    help = "The site location where the job should run.",
    required = False,)
grid__shortSites = 'ANALY_CERN_SHORT,ANALY_CONNECT_SHORT,ANALY_BNL_SHORT'
gridParserGroup.add_job_submission_option('--excludedSite', 
    #default = 'ANALY_CERN_CLOUD,ANALY_CERN_SHORT,ANALY_CONNECT_SHORT,ANALY_BNL_SHORT', # Known bad sites
    #default = 'ANALY_CERN_CLOUD,ANALY_SLAC,ANALY_CERN_SHORT,ANALY_CONNECT_SHORT,ANALY_BNL_SHORT,ANALY_BNL_EC2E1,ANALY_SWT2_CPB', # Known bad sites
    help = "The excluded site location.", 
    required = False, )
gridParserGroup.add_job_submission_option_group('--debug', default = '--skipScout',
    const='--express --debugMode --allowTaskDuplication --disableAutoRetry --useNewCode',
    help = "Submit GRID job on debug mode.", action='store_const',
    required = False )
gridParserGroup.add_job_submission_option('--nJobs', type=int,
    required = False, help = """Number of jobs to submit.""")
gridParserGroup.add_job_submission_option('--excludeFile', 
    required = False, default = '"*.o,*.so,*.a,*.gch,Download/*,InstallArea/*"',
    help = """Files to exclude from environment copied to grid.""")
gridParserGroup.add_job_submission_option('--disableAutoRetry', action='store_true',
    required = False,
    help = """Flag to disable auto retrying jobs.""")
gridParserGroup.add_job_submission_option('--followLinks', action='store_true',
    required = False,
    help = """Flag to disable auto retrying jobs.""")
gridParserGroup.add_job_submission_option('--mergeOutput', action='store_true',
    required = False,
    help = """Flag to enable merging output.""")
#gridParserGroup.add_job_submission_option('--mergeScript', 
#    required = False, 
#    help = """The script for merging the files. E.g.: 'your_merger.py -o %%OUT -i %%IN'""")
gridParserGroup.add_job_submission_option('--extFile', 
    required = False, default='',
    help = """External file to add.""")
gridParserGroup.add_job_submission_option('--match', 
    required = False, 
    help = """Use only files matching with given pattern.""")
gridParserGroup.add_job_submission_option('--antiMatch', 
    required = False,
    help = """Use all files but those matching with given pattern.""")
gridParserGroup.add_job_submission_option('--cloud', 
    required = False, default=False,
    help = """The cloud where to submit the job.""")
gridParserGroup.add_job_submission_option('--nGBPerJob', 
    required = False,
    help = """Maximum number of GB per job.""")
gridParserGroup.add_job_submission_option('--skipScout', action='store_true',
    required = False,
    help = """Flag to disable auto retrying jobs.""")
gridParserGroup.add_job_submission_option('--memory', type=int,
    required = False,
    help = """Needed memory to run in MB.""")
gridParserGroup.add_job_submission_option('--long', action='store_true',
    required = False,
    help = """Submit for long queue.""")
gridParserGroup.add_job_submission_option('--useNewCode', action='store_true',
    required = False,
    help = """Flag to disable auto retrying jobs.""")
gridParserGroup.add_job_submission_option('--allowTaskDuplication', action='store_true',
    required = False,
    help = """Flag to disable auto retrying jobs.""")
gridParserGroup.add_job_submission_option('--crossSite', 
    required = False, type=int,
    help = """Split jobs over many sites.""")
mutuallyEx1 = gridParserGroup.add_mutually_exclusive_group( required=False )
mutuallyEx1.add_job_submission_option('-itar','--inTarBall', 
    metavar='InTarBall', 
    help = "The environemnt tarball for posterior usage.")
mutuallyEx1.add_job_submission_option('-otar','--outTarBall',
    metavar='OutTarBall',  
    help = "The environemnt tarball for posterior usage.")
################################################################################
## Temporary classes only to deal with diamond inherit scheme
_inParser = GridJobArgumentParser(add_help = False)
_inParserGroup = _inParser.add_argument_group('GRID Input Dataset Arguments', '')
_inParserGroup.add_job_submission_option('--inDS','-i', action='store', 
                       required = True,
                       help = "The input Dataset ID (DID)")
_inParserGroup.add_job_submission_csv_option('--secondaryDSs', action='store', nargs='+',
                       required = False, 
                       help = "The secondary Dataset ID (DID), in the format name:nEvents:place")
_inParserGroup.add_job_submission_option('--forceStaged', action='store_true',
    required = False, default = False,
    help = """Force files from primary DS to be staged to local
    disk, even if direct-access is possible.""")
_inParserGroup.add_job_submission_option('--forceStagedSecondary', action='store_true',
    required = False,
    help = """Force files from secondary DS to be staged to local
              disk, even if direct-access is possible.""")
_inParserGroup.add_job_submission_option('--reusableSecondary', 
    required = False,
    help = """Allow reuse secondary dataset.""")
_inParserGroup.add_job_submission_option('--nFiles', type=int,
    required = False,
    help = """Number of files to run.""")
_inParserGroup.add_job_submission_option('--nFilesPerJob', type=int,
    required = False,
    help = """Number of files to run per job.""")
################################################################################
_outParser = GridJobArgumentParser(add_help = False)
_outParserGroup = _inParser.add_argument_group('GRID Output Dataset Arguments', '')
_outParserGroup.add_job_submission_option('--outDS','-o', action='store', 
                        required = True,
                        help = "The output Dataset ID (DID)")
_outParserGroup.add_job_submission_csv_option('--outputs', required = True,
    help = """The output format.""")
################################################################################
## Input and output grid parser
ioGridParser = GridJobArgumentParser(add_help = False, 
                                     parents = [_inParser, _outParser, gridParser],
                                     conflict_handler = 'resolve')

## Input grid parser
inGridParser = GridJobArgumentParser(add_help = False, 
                                     parents = [_inParser, gridParser],
                                     conflict_handler = 'resolve')

## Output grid parser
outGridParser = GridJobArgumentParser(add_help = False, 
                                      parents = [_outParser, gridParser],
                                      conflict_handler = 'resolve')
# Remove temp classes
del _inParser, _outParser

class LargeDIDError(ValueError):
  def __init__(self, in_):
    ValueError.__init__(self, ('Size of --outDS is larger (%d) than 132 char, '
                        'the maximum value allowed by CERN grid. '
                        'Current DID is valid until: %s') % (len(in_), in_[:132]))

################################################################################
## GridNamespace
# Make sure to use GridNamespace specialization for the used package when
# parsing arguments.
class GridNamespace( LoggerNamespace, JobSubmitNamespace ):
  """
    Improves argparser workspace object to support creating a string object
    with the input options.
  """

  #noNumyPySites = ['ANALY_SWT2_CPB','ANALY_BNL_EC2E1']

  prog = 'prun'
  ParserClass = GridJobArgumentParser

  def __init__(self, prog = None, **kw):
    LoggerNamespace.__init__( self, **kw )
    JobSubmitNamespace.__init__( self, prog = prog)

  def __call__(self):
    LoggerNamespace.__call__(self)
    JobSubmitNamespace.__call__(self)

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

  def setMergeExec(self, value):
    """
      Add the merge execution command on grid.
    """
    if len(value) < 1 or value[0] != '"':
      value = '"' + value
    if len(value) < 2 or value[-1] != '"':
      value += '"'
    self.mergeExec = value 

  def extFile(self):
    """
      Return a comma separated list of extFiles needed by this GridNamespace.
    """
    return ''

  def run(self, str_):
    """
      Run the command
    """
    self.pre_download()
    workDir=os.path.expandvars("$ROOTCOREBIN/..")
     # We need to cd to this dir so that prun accepts the submission
    os.chdir(workDir)
    os.system(str_)

  def parse_exec(self):
    full_cmd_str = ''
    # Add execute grid command if available
    if hasattr(self,'bexec'):
      full_cmd_str += self._formated_line( '--bexec' )
      full_cmd_str += self.parseExecStr(self.bexec)
    if hasattr(self,'exec_'):
      full_cmd_str += self._formated_line( '--exec' )
      full_cmd_str += self.parseExecStr(self.exec_)
    if hasattr(self,'mergeExec'):
      full_cmd_str += self._formated_line( '--mergeScript' )
      full_cmd_str += self.parseExecStr(self.mergeExec)
    return full_cmd_str

  def parse_special_args(self):
    if hasattr(self,'mergeExec'):
      if not(hasattr(self,'grid__mergeOutput')) or not(self.grid__mergeOutput):
        self.grid__mergeOutput = True
    if hasattr(self, 'grid__outDS'):
      value = self.grid__outputs
      if len(value) > 132:
        raise LargeDIDError(value)
      if hasattr(self, 'grid__outputs'):
        for output in self.grid__outputs.split(','):
          oList = output.split(':')
          if len(oList) == 2:
            did = value + '_' + oList[0].replace('"','')
            if len(did) > 132:
              raise LargeDIDError(did)
          else:
            if '*' in output and not output.endswith('.tgz'): output += '.tgz'
            did = value + '_' + output.replace('*','XYZ').replace('"','')
            if len(did) > 132:
              raise LargeDIDError(did)
    if self.extFile() and not self.extFile() in self.grid__extFile:
      # FIXME This will fail b/c not all permutations will be tested in grid__extFile
      if len(self.grid__extFile):
        self.grid__extFile += ','
      self.grid__extFile += self.extFile()
    if self.grid__long:
      if self.grid_excludedSite:
        for shortSite in grid__shortSites.split(','):
          if not shortSite in self.grid__excludedSite:
            self.grid__excludedSite += ',' + shortSite
      else:
        self.grid__excludedSite = grid__shortSites
    return ''


  def check_retrieve(self, filename, md5sum, dlurl):
    filename = os.path.expandvars(filename)
    basefile = os.path.basename(filename)
    dirname = os.path.dirname( filename )
    from RingerCore.FileIO import checkFile
    if not checkFile(filename, md5sum):
      self._logger.info('Downloading %s to avoid doing it on server side.', basefile)
      import urllib
      if not os.path.isdir( dirname ):
        from RingerCore import mkdir_p
        mkdir_p( dirname )
      urllib.urlretrieve(dlurl, filename=filename)
    else:
      self._logger.info('%s already downloaded.',filename)

  def pre_download(self):
    """
      Packages which need special libraries downloads to install should inherit
      from this class and overload this method to download needed libraries.
    """
    self.check_retrieve("$ROOTCOREBIN/../Downloads/boost.tgz"
                       ,"5a5d5614d9a07672e1ab2a250b5defc5"
                       ,"http://sourceforge.net/projects/boost/files/boost/1.58.0/boost_1_58_0.tar.gz"
                       )
    self.check_retrieve("$ROOTCOREBIN/../Downloads/cython.tgz"
                       ,"890b494a12951f1d6228c416a5789554"
                       ,"https://pypi.python.org/packages/c6/fe/97319581905de40f1be7015a0ea1bd336a756f6249914b148a17eefa75dc/Cython-0.24.1.tar.gz"
                       )
    self.check_retrieve("$ROOTCOREBIN/../Downloads/numpy.tgz"
                       ,"3cb325c3dff03b5bc15206c757a26116"
                       ,"https://github.com/numpy/numpy/archive/v1.10.4.tar.gz"
                       #,"http://sourceforge.net/projects/numpy/files/NumPy/1.10.4/numpy-1.10.4.tar.gz/download"
                       )
    self.check_retrieve("$ROOTCOREBIN/../Downloads/setuptools.tgz"
                       ,"0744ee90ad266fb117d59f94334185d0"
                       ,"https://pypi.python.org/packages/32/3c/e853a68b703f347f5ed86585c2dd2828a83252e1216c1201fa6f81270578/setuptools-26.1.1.tar.gz"
                       )
    self.check_retrieve("$ROOTCOREBIN/../Downloads/scipy.tgz"
                       ,"9c6bc68693d7307acffce690fe4f1076"
                       ,"https://github.com/scipy/scipy/archive/v0.18.0-1.tar.gz"
                       )

