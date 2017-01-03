import os
import re
import textwrap

__all__ = []
#__all__ = ['lsfParser','pbsParser','LocalClusterEnum', 'LocalClusterArgumentParser']

from RingerCore.Logger import Logger
from RingerCore.parsers.ParsingUtils import JobSubmitArgumentParser, JobSubmitNamespace
from RingerCore.util import get_attributes, EnumStringification
from RingerCore.parsers.Logger import LoggerNamespace

class LocalClusterEnum ( EnumStringification ):
  """
  Specify possible available local clusters.
  """
  LSF = 1
  PBS = 2
  Torque = 2

################################################################################
# Grid parser related objects
################################################################################

#class LocalClusterArgumentParser( JobSubmitArgumentParser ):
#  prefix = 'localCluster_'
#
#  def add_job_submission_suboption(mainOption, suboption, *l, **kw):
#    kw['dest'] = self._getDest(*[mainOption]) + ' ' + suboption
#    self.add_argument(*l, **kw)
#parser.add_argument_lc = types.MethodType(add_argument_lc, parser, argparse.ArgumentParser)
#
#pbsParser = LocalClusterArgumentParser(description = 'Run job on local cluster using PBS/Torque')
#pbsGroup = pbsParser.add_argument_group('PBS/Torque Arguments', '')
#pbsGroup.add_job_submission_option('-q',action='store', required = False,
#                                    help = "Specify the job queue.")
#import os
#OMP_NUM_THREADS = int(os.environ.get('OMP_NUM_THREADS',1))
#pbsGroup.add_job_submission_suboption('-l','nodes',action='store', required = False,
#                                      default = OMP_NUM_THREADS, type = int,
#                                      help = "Specify the job number of nodes.")
#pbsGroup.add_job_submission_suboption('-l','walltime',action='store', required = False,
#                                      default = None, 
#                                      help = "Specify the job wall time limit using format [hh:mm:ss].")
#pbsGroup.add_job_submission_suboption('-l','mem',action='store', required = False,
#                                      default = None, 
#                                      help = "Specify the job memory size.")
#pbsGroup.add_job_submission_option('-o',action='store', required = False,
#                                   help = "Name of standard output file.")
#pbsGroup.add_job_submission_option('-e',action='store', required = False,
#                                   help = "Name of standard output error file.")
#pbsGroup.add_job_submission_option('-V','--copy-environment',action='store', required = False,
#                                   help = "Copy current environment to the job.")
#pbsGroup.add_job_submission_option('-M','--mail-address',action='store', required = False,
#                                   help = "Specify mail address.")
#pbsGroup.add_job_submission_option('-d','--job-dependency',action='store', required = False,
#                                   type = int,
#                                   help = "Specifies that current job depends on other job.")
#
## TODO
#lsfParser = None
