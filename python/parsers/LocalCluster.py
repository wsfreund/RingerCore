__all__ = [ 'lsfParser','pbsParser', 'LSFArgumentParser', 'PBSJobArgumentParser'
          , 'LocalClusterNamespace']

from RingerCore.Logger import Logger
from RingerCore.parsers.ClusterManager import ( JobSubmitArgumentParser, JobSubmitNamespace
                                              , clusterManagerParser, ClusterManager, AvailableManager
                                              , OptionRetrieve, BooleanOptionRetrieve, SubOptionRetrieve
                                              )
from RingerCore.util import get_attributes, EnumStringification, BooleanStr
from RingerCore.parsers.Logger import LoggerNamespace

class LSFArgumentParser( JobSubmitArgumentParser ):
  prefix = 'lsf'
class PBSJobArgumentParser( JobSubmitArgumentParser ):
  prefix = 'pbs'

pbsParser = PBSJobArgumentParser(description = 'Run job on local cluster using PBS/Torque',
                                 parents = [clusterManagerParser],
                                 conflict_handler = 'resolve')
pbsGroup = pbsParser.add_argument_group('PBS/Torque Arguments', '')
pbsGroup.add_job_submission_option('-Q','--queue',action='store', required = False,
                                    help = "Specify the job queue.")
import os
OMP_NUM_THREADS = int(os.environ.get('OMP_NUM_THREADS',1))
pbsGroup.add_job_submission_option( '--nodes', option='-l',suboption='nodes', action=SubOptionRetrieve, required = False
                                  , default = OMP_NUM_THREADS, type=int
                                  , help = "Specify the job number of nodes.")
pbsGroup.add_job_submission_option( '--walltime', option='-l', suboption='walltime', required = False
                                  , action=SubOptionRetrieve
                                  , help = "Specify the job wall time limit using format [hh:mm:ss].")
pbsGroup.add_job_submission_option( '--mem', option='-l', suboption='mem',action=SubOptionRetrieve
                                  , required = False
                                  , help = "Specify the job memory size.")
pbsGroup.add_job_submission_option( '-stdout', action='store', required = False
                                  , help = "Name of standard output file.")
pbsGroup.add_job_submission_option( '-stderr', action='store', required = False
                                  , help = "Name of standard output error file.")
pbsGroup.add_job_submission_option( '-V','--copy-environment', option = '-V', action=BooleanOptionRetrieve
                                  , required = False, type = BooleanStr
                                  , help = "Copy current environment to the job.")
pbsGroup.add_job_submission_option( '-M','--mail-address',action='store', required = False
                                  , help = "Specify mail address.")
pbsGroup.add_job_submission_option( '-D','--job-dependency',action='store', required = False
                                  , type = int
                                  , help = "Specifies that current job depends on other job.")
# Arguments which are not propagated to the job, but handle how to set it up
pbsGroup.add_argument('--debug', required = False, type = BooleanStr,
                      help = "Specify that this should be run on debug mode.")
pbsGroup.add_argument( '--nFiles', required = False
                     , default = None, type=int
                     , help = "Specify the job number of nodes.")

## TODO
lsfParser = None

################################################################################
## LocalClusterNamespace
class LocalClusterNamespace( JobSubmitNamespace ):
  """
    Improves argparser workspace object to support creating a string object
    with the input options.
  """

  def __init__(self, localCluster, **kw):
    self.localCluster = AvailableManager.retrieve( localCluster )
    if self.localCluster is ClusterManager.LSF:
      self.prefix = LSFArgumentParser.prefix
      prog = 'bsub'
    elif self.localCluster is ClusterManager.PBS:
      self.prefix = PBSJobArgumentParser.prefix
      prog = 'qsub'
    else:
      self._logger.fatal("Not implmeneted LocalClusterNamespace for cluster manager %s", AvailableManager.retrieve(self.localCluster), NotImplementedError)
    JobSubmitNamespace.__init__( self, prog = prog)

  def setExec(self, value):
    """
      Add the execution command on grid.
    """
    self.exec_ = value 

  def run(self):
    "Execute the command"
    full_cmd_str = self.prog + ' \\\n'
    full_cmd_str += self._parse_standard_args()
    full_cmd_str += self.parse_exec()
    full_cmd_str += self.parse_special_args()
    self._run_command(full_cmd_str)

  def parse_exec(self):
    full_cmd_str = ''
    # Add execute grid command if available
    if hasattr(self,'exec_'):
      full_cmd_str += self._formated_line( '--' )
      full_cmd_str += self.parseExecStr(self.exec_, addQuote = False)
    return full_cmd_str

  def parse_special_args(self):
    return ''
