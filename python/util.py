#coding: utf-8
__all__ = ['Include', 'include', 'str_to_class', 'Roc', 'calcSP',
           'csvStr2List', 'floatFromStr', 'geomean', 'get_attributes',
           'mean', 'mkdir_p', 'printArgs', 'reshape', 'reshape_to_array',
           'stdvector_to_list', 'trunc_at', 'progressbar',
           'select', 'timed', 'getFilters', 'start_after', 'appendToOutput',
           'apply_sort', 'scale10', 'measureLoopTime', 'keyboard', 'git_description',
           'is_tool', 'secureExtractNpItem', 'emptyArgumentsPrintHelp','cmd_exists', 
           'getParentVersion']

import re, os, __main__
import sys
import code
import types
import cPickle
import gzip
import inspect
import numpy as np

from RingerCore.Configure import NotSet, GRID_ENV

loadedEnvFile = False
def sourceEnvFile():
  """
    Emulate source new_env_file.sh on python environment.
  """
  try:
    from RingerCore.Logger import Logger
    logger = Logger.getModuleLogger(__name__)
    import os, sys
    global loadedEnvFile
    if not loadedEnvFile:
      with open(os.path.expandvars('$ROOTCOREBIN/../FastNetTool/cmt/new_env_file.sh'),'r') as f:
        lines = f.readlines()
        lineparser = re.compile(r'test "\$\{(?P<shellVar>[A-Z1-9]*)#\*(?P<addedPath>\S+)\}" = "\$\{(?P=shellVar)\}" && export (?P=shellVar)=\$(?P=shellVar):(?P=addedPath) || true')
        for line in lines:
          m = lineparser.match(line)
          if m:
            shellVar = m.group('shellVar')
            if shellVar != 'PYTHONPATH':
              continue
            addedPath = os.path.expandvars(m.group('addedPath'))
            if not addedPath:
              logger.warning("Couldn't retrieve added path on line \"%s\".", line)
              continue
            if not os.path.exists(addedPath):
              logger.warning("Couldn't find following path \"%s\".", addedPath)
              continue
            if not addedPath in os.environ[shellVar]:
              sys.path.append(addedPath)
              logger.info("Successfully added path: \"%s\".", line)
      loadedEnvFile=True
  except IOError:
    raise RuntimeError("Cannot find new_env_file.sh, did you forget to set environment or compile the package?")
  
def str_to_class(module_name, class_name):
  try:
    import importlib
  except ImportError:
    # load the module, will raise ImportError if module cannot be loaded
    m = __import__(module_name, globals(), locals(), class_name)
    # get the class, will raise AttributeError if class cannot be found
    c = getattr(m, class_name)
    return c
  # load the module, will raise ImportError if module cannot be loaded
  m = importlib.import_module(module_name)
  # get the class, will raise AttributeError if class cannot be found
  c = getattr(m, class_name)
  return c



def mkdir_p(path):
  import os, errno
  path = os.path.expandvars( path )
  try:
    if not os.path.exists( path ):
      os.makedirs(path)
  except OSError as exc: # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise

def csvStr2List( csvStr ):
  """
    Return a list from the comma separated values
    If input string starts with @, then it is assumed that the leading string
    an actual path and the content from the file is parsed.
  """
  # Treat comma separated lists:
  if type(csvStr) is str:
    # Treat files which start with @ as a comma separated list of files
    if csvStr.startswith('@'):
      with open( os.path.expandvars( csvStr[1:] ), 'r') as content_file:
        csvStr = content_file.read()
        csvStr = csvStr.replace('\n','')
        if csvStr.endswith(' '): csvStr = csvStr[:-1]
    csvStr = csvStr.split(',')
  # Make sure our confFileList is a list (just to be compatible for 
  if not type(csvStr) is list:
    csvStr = [csvStr]
  return csvStr

def is_tool(name):
  import subprocess
  try:
    devnull = open(os.devnull)
    subprocess.Popen([name], stdout=devnull, stderr=devnull).communicate()
  except OSError as e:
    if e.errno == os.errno.ENOENT:
      return False
  return True

def get_attributes(o, **kw):
  """
    Return attributes from a class or object.
  """
  onlyVars = kw.pop('onlyVars', False)
  getProtected = kw.pop('getProtected', True)
  from RingerCore.Configure import checkForUnusedVars
  checkForUnusedVars(kw)
  return [(a[0] if onlyVars else a) for a in inspect.getmembers(o, lambda a:not(inspect.isroutine(a))) \
             if not(a[0].startswith('__') and a[0].endswith('__')) \
                and (getProtected or not( a[0].startswith('_') or a[0].startswith('__') ) ) ]

def printArgs(args, fcn = None):
  try:
    import pprint as pp
    if args:
      if not isinstance(args,dict):
        args_dict = vars(args)
      else:
        args_dict = args
      msg = 'Retrieved the following configuration:\n%s' % pp.pformat([(key, args_dict[key]) for key in sorted(args_dict.keys())])
    else:
      msg = 'Retrieved empty configuration!'
    if fcn:
      fcn(msg)
    else:
      print 'INFO:%s' % msg
  except ImportError:
    logger.info('Retrieved the following configuration: \n %r', vars(args))

def progressbar(it, count ,prefix="", size=60, step=1, disp=True, logger = None, level = None,
                no_bl = not(GRID_ENV or not(sys.stdout.isatty())), 
                measureTime = True):
  """
    Display progressbar.

    Input arguments:
    -> it: the iterations collection;
    -> count: total number of iterations on collection;
    -> prefix: the strings preceding the progressbar;
    -> size: number of chars to use on the progressbar;
    -> step: the number of iterations needed for updating;
    -> disp: whether to display progressbar or not;
    -> logger: use this logger object instead o sys.stdout;
    -> level: the output level used on logger;
    -> no_bl: whether to show messages without breaking lines;
    -> measureTime: display time measurement when completing progressbar task.
  """
  from RingerCore.Logger import LoggingLevel
  from logging import StreamHandler
  if level is None: level = LoggingLevel.INFO
  def _show(_i):
    x = int(size*_i/count) if count else 0
    if _i % (step if step else 1): return
    if logger:
      if logger.isEnabledFor(level):
        fn, lno, func = logger.findCaller() 
        record = logger.makeRecord(logger.name, level, fn, lno, 
                                   "%s|%s%s| %i/%i\r",
                                   (prefix, "█"*x, "-"*(size-x), _i, count,), 
                                   None, 
                                   func=func)
        record.nl = False
        # emit message
        logger.handle(record)
    else:
      sys.stdout.write("%s|%s%s| %i/%i\r" % (prefix, "█"*x, "-"*(size-x), _i, count))
      sys.stdout.flush()
  # end of (_show)
  # prepare for looping:
  try:
    if disp:
      if measureTime:
        from time import time
        start = time()
      # override emit to emit_no_nl
      if logger:
        if no_bl:
          from RingerCore.Logger import StreamHandler2
          prev_emit = []
          # TODO On python3, all we need to do is to change the Handler.terminator
          for handler in logger.handlers:
            if type(handler) is StreamHandler:
              stream = StreamHandler2( handler )
              prev_emit.append( handler.emit )
              setattr(handler, StreamHandler.emit.__name__, stream.emit_no_nl)
      _show(0)
    # end of (looping preparation)
    # loop
    try:
      for i, item in enumerate(it):
        yield item
        if disp: _show(i+1)
    except GeneratorExit:
      pass
    # end of (looping)
    # final treatments
    step = 1 # Make sure we always display last printing
    if disp:
      if measureTime:
        end = time()
      if logger:
        if no_bl:
          # override back
          for handler in logger.handlers:
            if type(handler) is StreamHandler:
              setattr( handler, StreamHandler.emit.__name__, prev_emit.pop() )
          _show(i+1)
        if measureTime:
          logger.log( level, "%s... finished task in %3fs.", prefix, end - start )
      else:
        if measureTime:
          sys.stdout.write("\n%s... finished task in %3fs.\n" % ( prefix, end - start) )
        else:
          sys.stdout.write("\n" )
        sys.stdout.flush()
  except (BaseException) as e:
    import traceback
    print traceback.format_exc()
    step = 1 # Make sure we always display last printing
    if disp:
      if logger:
        # override back
        if no_bl:
          for handler in logger.handlers:
            if type(handler) is StreamHandler:
              try:
                setattr( handler, StreamHandler.emit.__name__, prev_emit.pop() )
              except IndexError:
                pass
        try:
          _show(i+1)
        except NameError:
          _show(0)
        for handler in logger.handlers:
          if type(handler) is StreamHandler:
            handler.stream.flush()
      else:
        sys.stdout.write("\n")
        sys.stdout.flush()
    # re-raise:
    raise e
  # end of (final treatments)

def measureLoopTime(it, prefix = 'Iteration', prefix_end = '', 
                    logger = None, level = None, showLoopBenchmarks = True):
  from time import time
  if level is None:
    from RingerCore.Logger import LoggingLevel
    level = LoggingLevel.DEBUG
  start = time()
  for i, item in enumerate(it):
    lStart = time()
    yield item
    end = time()
    if showLoopBenchmarks:
      if logger:
        logger.log( level, '%s %d took %.2fs.', prefix, i, end - lStart)
      else:
        sys.stdout.write( level, '%s %d took %.2fs.\n' % ( prefix, i, end - lStart ) )
        sys.stdout.flush()
  if logger:
    logger.log( level, 'Finished looping (%s) in %.2fs.', prefix_end, end - start)
  else:
    sys.stdout.write( level, 'Finished looping (%s) in %.2fs.\n' % ( prefix_end, end - start) )
    sys.stdout.flush()


def select( fl, filters ):
  """
  Return a selection from fl maching f

  WARNING: This selection method retrieves the same string contained in fl
  if it matches two different filters.
  """
  ret = []
  for filt in filters:
    taken = filter(lambda obj: type(obj) in (str,unicode) and filt in obj, traverse(fl, simple_ret = True))
    ret.append(taken)
  if len(ret) == 1: ret = ret[0]
  return ret

def reshape( input ):
  #sourceEnvFile()
  import numpy as np
  return np.array(input.tolist())

def reshape_to_array( input ):
  import numpy as np
  return np.reshape(input, (1,np.product(input.shape)))[0]


def trunc_at(s, d, n=1):
  "Returns s truncated at the n'th (1st by default) occurrence of the delimiter, d."
  return d.join(s.split(d)[:n])

def start_after(s, d, n=1):
  "Returns s after at the n'th (1st by default) occurrence of the delimiter, d."
  return d.join(s.split(d)[n:])

#def stdvector(vecType, *argl):
#  from ROOT.std import vector
#  v = vector(vecType)
#  return v(*argl)

def stdvector_to_list(vec, size=None):
  if size:
    l=size*[0]
  else:
    l = vec.size()*[0]

  for i in range(vec.size()):
    l[i] = vec[i]
  return l

def floatFromStr(str_):
  "Return float from string, checking if float is percentage"
  if '%' in str_:
    return float(str_.strip('%'))*100.
  return float(str_)

class Include:
  def __call__(self, filename, globalz=None, localz=None, clean=False):
    "Simple routine to execute python script, possibly keeping global and local variables."
    searchPath = re.split( ',|' + os.pathsep, os.environ['PYTHONPATH'] )
    if '' in searchPath:
      searchPath[ searchPath.index( '' ) ] = str(os.curdir)
    from RingerCore.FileIO import findFile
    trueName = findFile(filename, searchPath, os.R_OK )
    gworkspace = {}
    lworkspace = {}
    if globalz: gworkspace.update(globalz)
    if localz: lworkspace.update(localz)
    if not clean:
      gworkspace.update(__main__.__dict__)
      lworkspace.update(__main__.__dict__)
    if trueName: 
      try:
        execfile(trueName, gworkspace, lworkspace)
      except NameError, e:
        if e == "name 'execfile' is not defined":
          Include.xfile(trueName, globalz, localz)
        else:
          raise e
    else:
      raise ImportError("Cannot include file: %s" % filename)

  @classmethod
  def xfile(cls, afile, globalz=None, localz=None):
    "Alternative to execfile for python3.0"
    with open(afile, "r") as fh:
      exec(fh.read(), globalz, localz)
include = Include()

def geomean(nums):
  return (reduce(lambda x, y: x*y, nums))**(1.0/len(nums))

def mean(nums):
  return (sum(nums)/len(nums))

def calcSP( pd, pj ):
  """
    ret  = calcSP(x,y) - Calculates the normalized [0,1] SP value.
    effic is a vector containing the detection efficiency [0,1] of each
    discriminating pattern.  
  """
  from numpy import sqrt
  return sqrt(geomean([pd,pj]) * mean([pd,pj]))

class Roc(object):
  """
    Create ROC information holder
  """
  #from RingerCore.RawDictStreamable import RawDictStreamable
  #__metaclass__ = RawDictStreamable

  def __init__( self, label, input_, target = NotSet, numPts = 1000, npConst = NotSet ):
    """
			def ROC( output, target, label, numPts = 1000, npConst = npConstants() ):

      Input Parameters are:
         output -> The output space generated by the classifier.
         target -> The targets which should be returned by the classifier.
         label ->  A label to identify the ROC.
         numPts -> (1000) The number of points to generate the ROC.
         npConst -> (npConstants()) The number of points to generate the ROC.
    """
    from RingerCore.npConstants import npConstants
    if npConst is NotSet: npConst = npConstants()
    self.label = label
    if target is NotSet:
      self.spVec    = input_[0]
      self.detVec   = input_[1]
      self.faVec    = input_[2]
      self.cutVec   = input_[3]
    else:
      # We have to determine what is signal and noise from the datasets using
      # the targets:
      outSignal = input_[np.where(target == 1.)[1]]
      outNoise = input_[np.where(target == -1.)[1]]
      outSignal = np.sort(outSignal, kind='heapsort')
      outNoise  = np.sort(outNoise , kind='heapsort')
      self.cutVec = np.arange( -1., 1., 2. / ( numPts ) )
      self.detVec = npConst.fp_zeros( numPts )
      self.faVec  = npConst.fp_zeros( numPts )
      self.spVec  = npConst.fp_zeros( numPts )
      lenSig   = float( len(outSignal) )
      lenNoise = float( len(outNoise)  )
      for i in range( numPts ):
        self.detVec[i] = ( lenSig   - np.searchsorted( outSignal, self.cutVec[i] ) ) / lenSig
        self.faVec[i]  = ( lenNoise - np.searchsorted( outNoise,  self.cutVec[i] ) ) / lenNoise
        self.spVec[i]   = calcSP( self.detVec[i], 1. - self.faVec[i] )
    self.maxIdx = np.argmax(self.spVec)
    self.sp  = self.spVec  [ self.maxIdx ]
    self.det = self.detVec [ self.maxIdx ]
    self.fa  = self.faVec  [ self.maxIdx ]
    self.cut = self.cutVec [ self.maxIdx ]

#Helper function
def Roc_to_histogram(g, nsignal, nnoise):
  import numpy as np
  npoints = g.GetN()
  nsignalLastBin = 0
  nnoiseLastBin  = 0
  nsignalBin = np.array([0]*npoints)
  nnoiseBin = np.array([0]*npoints)
  totalSignal = totalNoise =0
  pd = g.GetY()
  fa = g.GetX()
  for np in range( npoints ):
    nsignalBin[np] = nsignal - int(pd[np]*nsignal) - nsignalLastBin
    nnoiseBin[np] = nnoise - int(fa[np]*nnoise) - nnoiseLastBin
    nsignalLastBin += nsignalBin[np]
    nnoiseLastBin += nnoiseBin[np]
    totalSignal += nsignalBin[np]
    totalNoise += nnoiseBin[np]
  #Loop over Receive Operating Curve

  signalTarget = 1
  noiseTarget = -1
  #Prepare the estimation output
  resolution = (signalTarget - noiseTarget)/float(npoints)
  binValue = noiseTarget
  signalOutput = []
  noiseOutput = []

  for np in range(npoints):
    signalOutput += nsignalBin[np]*[binValue]
    noiseOutput += nnoiseBin[np]*[binValue]
    binValue += resolution

  return signalOutput, noiseOutput

def keyboard():
  """ 
    Function that mimics the matlab keyboard command.
  """
  import pdb; pdb.set_trace()


def createRootParameter( type_name, name, value):
  from ROOT import TParameter
  return TParameter(type_name)(name,value)

def timed(f):
  def func(*args):
    import time
    start = time.time()
    ret = f(*args)
    took = time.time() - start
    print("%s took %f" % (f.__name__,took))
    return ret
  return func

def getFilters( filtFinder, objs, idxs = None, printf = None):
  """
    Get filters using filter finder
  """
  filt = filtFinder
  if hasattr(filtFinder,'__call__'):
    if type(filtFinder) is type:
      filtFinder = filtFinder()
    filt = filtFinder( objs )
    #Retrieve only the bin IDx selected by arg
    if idxs is not None:
      try:
        filt = [filt[idx] for idx in idxs]
      except IndexError:
        raise IndexError('This bin index does not exist.')
      if printf is not None:
        printf('Analyzing only the bin index %r', idxs)
    printf('Found following filters: %r', filt)
  return filt

def apply_sort( inputCollection, sortedIdx ):
  """
    Returns inputCollection sorted accordingly to sortedIdx
  """
  return [inputCollection[idx] for idx in sortedIdx]

def scale10( num ):
  """
    Returns the scale 10 power index of num
  """
  import math
  return math.ceil(math.log10(abs(num))) if num else 0

def appendToOutput( o, cond, what):
  """
  When multiple outputs are configurable, use this method to append to output in case some option is True.
  """
  if cond:
    if type(o) is tuple: o = o + (what,)
    else: o = o, what
  return o

def secureExtractNpItem( npArray ):
  try:
    return npArray.item()
  except AttributeError:
    return npArray


def emptyArgumentsPrintHelp(parser):
  """
  If user do not enter any argument, print help
  """
  import sys
  if len(sys.argv)==1:
    from RingerCore.Logger import _getFormatter
    sys.stdout.write(_getFormatter().color_seq % { 'color' : _getFormatter().colors['INFO']})
    #mainLogger = Logger.getModuleLogger( __name__)
    #mainLogger.write = mainLogger.info
    #parser.print_help(file = mainLogger)
    parser.print_help()
    sys.stdout.write(_getFormatter().reset_seq)
    parser.exit(1)

def cmd_exists(cmd):
  """
  Check whether command exists.
  Taken from: http://stackoverflow.com/a/28909933/1162884
  """
  import subprocess
  return subprocess.call("type " + cmd, shell=True, 
      stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def git_description( init_fname ):
  if not cmd_exists('git'):
    raise RuntimeError("Couldn't find git commnad.")
  git_dir = os.path.dirname(os.path.realpath( init_fname ))
  if os.path.basename( git_dir ) == "python":
    # Protect against RootCore architeture
    git_dir = os.path.dirname( git_dir )
  git_dir = os.path.join( git_dir, '.git' )
  if os.path.isfile( git_dir ):
    old_dir = git_dir
    with open( git_dir ) as f:
      relative_path = f.readline().split(' ')[-1].strip('\n')
    git_dir = os.path.realpath( os.path.join( os.path.dirname( old_dir ), relative_path ) )
  if not os.path.isdir( git_dir ):
    raise RuntimeError("Couldn't determine git dir. Retrieved %s as input file and tested for %s as git dir", init_fname, git_dir)
  import subprocess
  git_version_cmd = subprocess.Popen(["git", "--git-dir", git_dir, "describe"
                                    ,"--always","--dirty",'--tags'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  (output, stderr) = git_version_cmd.communicate()
  output = output.rstrip('\n')
  if git_version_cmd.returncode:
    raise RuntimeError("git command failed with code %d. Error message returned was:\n%s", git_version_cmd.returncode, stderr)
  return output

def getParentVersion( init_fname ):
  if not cmd_exists('git'):
    raise RuntimeError("Couldn't find git commnad.")
  git_dir = os.path.dirname(os.path.realpath( init_fname ))
  if os.path.basename( git_dir ) == "python":
    # Protect against RootCore architeture
    git_dir = os.path.dirname( git_dir )
  git_dir = os.path.join( git_dir, '.git' )
  if not os.path.exists( git_dir ):
    raise RuntimeError("Couldn't determine git dir. Retrieved %s as input file and tested for %s as git dir", init_fname, git_dir)
  parent_dir = os.path.abspath( os.path.join( os.path.dirname( git_dir ), '..' ) )
  if os.path.isdir( parent_dir ):
    try:
      return parent_dir, git_description( parent_dir )
    except RuntimeError, e:
      return None, e
  return None, None




