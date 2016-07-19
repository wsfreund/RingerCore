__all__ = ['EnumStringification', 'BooleanStr', 'Holder', 'Include', 'include',
    'NotSet', 'NotSetType', 'str_to_class', 'Roc', 'SetDepth', 'calcSP',
    'checkForUnusedVars', 'conditionalOption', 'findFile',
    'csvStr2List', 'floatFromStr', 'geomean', 'get_attributes',
    'mean', 'mkdir_p', 'printArgs', 'reshape', 'reshape_to_array',
    'retrieve_kw', 'setDefaultKey', 'start_after',
    'stdvector_to_list', 'traverse','trunc_at', 'progressbar',
    'select', 'cat_files_py', 'WriteMethod', 'timed', 'getFilters',
    'apply_sort', 'scale10']

import re, os, __main__
import sys
import code
import types
import cPickle
import gzip
import inspect
import numpy as np

class NotSetType( type ):
  def __bool__(self):
    return False
  __nonzero__ = __bool__
  def __repr__(self):
    return "<+NotSet+>"
  def __str__(self):
    return "<+NotSet+>"

class NotSet( object ): 
  __metaclass__ = NotSetType

class Holder( object ):
  def __init__(self, obj):
    self.obj = obj
  def __call__(self):
    return self.obj

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
  
class EnumStringification( object ):
  "Adds 'enum' static methods for conversion to/from string"

  _ignoreCase = False

  @classmethod
  def tostring(cls, val):
    "Transforms val into string."
    for k, v in get_attributes(cls, getProtected = False):
      if v==val:
        return k
    return None

  @classmethod
  def fromstring(cls, str_):
    "Transforms string into enumeration."
    if not cls._ignoreCase:
      return getattr(cls, str_, None)
    else:
      allowedValues = [attr for attr in get_attributes(cls) if not attr[0].startswith('_')]
      try:
        idx = [attr[0].upper() for attr in allowedValues].index(str_.upper().replace('-','_'))
      except ValueError:
        raise ValueError("%s is not in enumeration. Use one of the followings: %r" % (str_, allowedValues) )
      return allowedValues[idx][1]

  @classmethod
  def retrieve(cls, val):
    """
    Retrieve int value and check if it is a valid enumeration string or int on
    this enumeration class.
    """
    allowedValues = [attr for attr in get_attributes(cls) if not attr[0].startswith('_')]
    try:
      # Convert integer string values to integer, if possible:
      val = int(val)
    except ValueError:
      pass
    if type(val) is str:
      oldVal = val
      val = cls.fromstring(val)
      if val is None:
          raise ValueError("String (%s) does not match any of the allowed values %r." % \
              (oldVal, allowedValues))
    else:
      if not val in [attr[1] for attr in allowedValues]:
        raise ValueError(("Attempted to retrieve val benchmark "
            "with a enumeration value which is not allowed. Use one of the followings: "
            "%r") % allowedValues)
    return val

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

class BooleanStr( EnumStringification ):
  _ignoreCase = True

  False = 0
  True = 1

  @staticmethod
  def treatVar(var,d, default = False):
    if var in d:
      if d[var] not in (None, NotSet):
        return BooleanStr.retrieve( d[var] )
      else:
        return d[var]
    else:
      return default



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


def get_attributes(o, **kw):
  """
    Return attributes from a class or object.
  """
  onlyVars = kw.pop('onlyVars', False)
  getProtected = kw.pop('getProtected', True)
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
                no_bl = not(int(os.environ.get('RCM_GRID_ENV',0))) ):
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
  """
  from RingerCore.Logger import LoggingLevel
  from logging import StreamHandler
  if level is None: level = LoggingLevel.INFO
  def _show(_i):
    x = int(size*_i/count)
    if _i % step: return
    if logger:
      if logger.isEnabledFor(level):
        fn, lno, func = logger.findCaller() 
        record = logger.makeRecord(logger.name, level, fn, lno, 
                                   "%s[%s%s] %i/%i\r",
                                   (prefix, "#"*x, "."*(size-x), _i, count,), 
                                   None, 
                                   func=func)
        record.nl = False
        # emit message
        logger.handle(record)
    else:
      sys.stdout.write("%s[%s%s] %i/%i\r" % (prefix, "#"*x, "."*(size-x), _i, count))
      sys.stdout.flush()
  # end of (_show)
  # prepare for looping:
  try:
    if disp: 
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
    for i, item in enumerate(it):
      yield item
      if disp: _show(i+1)
    # end of (looping)
    # final treatments
    step = 1 # Make sure we always display last printing
    if disp:
      end = time()
      if logger:
        if no_bl:
          # override back
          for handler in logger.handlers:
            if type(handler) is StreamHandler:
              setattr( handler, StreamHandler.emit.__name__, prev_emit.pop() )
          _show(i+1)
        logger.log( level, "%s... finished task in %3fs.", prefix, end - start )
      else:
        sys.stdout.write("\n%s... finished task in %3fs.\n", prefix, end - start )
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

def select( fl, filters ):
  """
  Return a selection from fl maching f

  WARNING: This selection method retrieves the same string contained in fl
  if it matches two different filters.
  """
  ret = []
  for filt in filters:
    taken = filter(lambda obj: type(obj) is str and filt in obj, traverse(fl, simple_ret = True))
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


def conditionalOption( argument, value ):
  return ( argument + " " + str(value) if not( type(value) in (list,tuple) ) and not( value in (None, NotSet) ) else \
      ( argument + " " + ' '.join([str(val) for val in value]) if value else '' ) )

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

def findFile( filename, pathlist, access ):
  """
     Find <filename> with rights <access> through <pathlist>.
     Author: Wim Lavrijsen (WLavrijsen@lbl.gov)
     Copied from 'atlas/Control/AthenaCommon/python/Utils/unixtools.py'
  """

  # special case for those filenames that already contain a path
  if os.path.dirname( filename ):
    if os.access( filename, access ):
      return filename

  # test the file name in all possible paths until first found
  for path in pathlist:
    f = os.path.join( path, filename )
    if os.access( f, access ):
      return f

  # no such accessible file avalailable
  return None  

class Include:
  def __call__(self, filename, globalz=None, localz=None, clean=False):
    "Simple routine to execute python script, possibly keeping global and local variables."
    searchPath = re.split( ',|' + os.pathsep, os.environ['PYTHONPATH'] )
    if '' in searchPath:
      searchPath[ searchPath.index( '' ) ] = str(os.curdir)
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

def calcSP( pd, pf ):
  """
    ret  = calcSP(x,y) - Calculates the normalized [0,1] SP value.
    effic is a vector containing the detection efficiency [0,1] of each
    discriminating pattern.  
  """
  from numpy import sqrt
  return sqrt(geomean([pd,pf]) * mean([pd,pf]))

class Roc(object):
  """
    Create ROC information holder
  """

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




class SetDepth(Exception):
  def __init__(self, value):
    self.depth = value

def traverse(o, tree_types=(list, tuple),
    max_depth_dist=0, max_depth=np.iinfo(np.uint64).max, 
    level=0, idx=0, parent=None,
    simple_ret=False):
  """
  Loop over each holden element. 
  Can also be used to change the holden values, e.g.:

  a = [[[1,2,3],[2,3],[3,4,5,6]],[[[4,7],[]],[6]],7]
  for obj, idx, parent in traverse(a): parent[idx] = 3
  [[[3, 3, 3], [3, 3], [3, 3, 3, 3]], [[[3, 3], []], [3]], 3]

  Examples printing using max_depth_dist:

  In [0]: for obj in traverse(a,(list, tuple),0,simple_ret=False): print obj
  (1, 0, [1, 2, 3], 0, 3)
  (2, 1, [1, 2, 3], 0, 3)
  (3, 2, [1, 2, 3], 0, 3)
  (2, 0, [2, 3], 0, 3)
  (3, 1, [2, 3], 0, 3)
  (3, 0, [3, 4, 5, 6], 0, 3)
  (4, 1, [3, 4, 5, 6], 0, 3)
  (5, 2, [3, 4, 5, 6], 0, 3)
  (6, 3, [3, 4, 5, 6], 0, 3)
  (4, 0, [4, 7], 0, 4)
  (7, 1, [4, 7], 0, 4)
  (6, 0, [6], 0, 3)
  (7, 2, [[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 0, 1) 

  In [1]: for obj in traverse(a,(list, tuple),1): print obj
  ([1, 2, 3], 0, [[1, 2, 3], [2, 3], [3, 4, 5, 6]], 1, 3)
  ([2, 3], 0, [[1, 2, 3], [2, 3], [3, 4, 5, 6]], 1, 3)
  ([3, 4, 5, 6], 0, [[1, 2, 3], [2, 3], [3, 4, 5, 6]], 1, 3)
  ([4, 7], 0, [[4, 7], []], 1, 4)
  ([6], 0, [[[4, 7], []], [6]], 1, 3)
  ([[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 2, None, 1, 1)

  In [2]: for obj in traverse(a,(list, tuple),2,simple_ret=False): print obj
  ([[1, 2, 3], [2, 3], [3, 4, 5, 6]], 0, [[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 2, 2)
  ([[4, 7], []], 0, [[[4, 7], []], [6]], 2, 3)
  ([[[4, 7], []], [6]], 1, [[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 2, 2)

  In [3]: for obj in traverse(a,(list, tuple),3): print obj
  ([[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 0, None, 3, 1)

  In [4]: for obj in traverse(a,(list, tuple),4): print obj
  ([[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 1, None, 4, 1)

  In [5]: for obj in traverse(a,(list, tuple),5): print obj
  <NO OUTPUT>

  """
  if isinstance(o, tree_types):
    level += 1
    # FIXME Still need to test max_depth
    if level > max_depth:
      if simple_ret:
        yield o
      else:
        yield o, idx, parent, 0, level
      return
    skipped = False
    isDict = isinstance(o, dict)
    if isDict:
      loopingObj = o.iteritems()
    else:
      loopingObj = enumerate(o)
    for idx, value in loopingObj:
      try:
        for subvalue, subidx, subparent, subdepth_dist, sublevel in traverse(value, tree_types, max_depth_dist, max_depth, level, idx, o ):
          if subdepth_dist == max_depth_dist:
            if skipped:
              subdepth_dist += 1
              break
            else:
              if simple_ret:
                yield subvalue
              else:
                yield subvalue, subidx, subparent, subdepth_dist, sublevel 
          else:
            subdepth_dist += 1
            break
        else: 
          continue
      except SetDepth, e:
        if simple_ret:
          yield o
        else:
          yield o, idx, parent, e.depth, level
        break
      if subdepth_dist == max_depth_dist:
        if skipped:
          subdepth_dist += 1
          break
        else:
          if simple_ret:
            yield o
          else:
            yield o, idx, parent, subdepth_dist, level
          break
      else:
        if level > (max_depth_dist - subdepth_dist):
          raise SetDepth(subdepth_dist+1)
  else:
    if simple_ret:
      yield o
    else:
      yield o, idx, parent, 0, level

def setDefaultKey( d, key, val):
  if not key in d: d[key] = val

def retrieve_kw( kw, key, default = NotSet ):
  if not key in kw or kw[key] is NotSet:
    kw[key] = default
  return kw.pop(key)

def checkForUnusedVars(d, fcn = None):
  """
    Checks if dict @d has unused properties and print them as warnings
  """
  for key in d.keys():
    if d[key] is NotSet: continue
    msg = 'Obtained not needed parameter: %s' % key
    if fcn:
      fcn(msg)
    else:
      print 'WARNING:%s' % msg

def keyboard():
  """ 
    Function that mimics the matlab keyboard command.
  """
  import pdb; pdb.set_trace()


def createRootParameter( type_name, name, value):
  from ROOT import TParameter
  return TParameter(type_name)(name,value)

class WriteMethod( EnumStringification ):
  """
    Specificate how to write files on cat_files_py
  """
  _ignoreCase = True
  Readlines = 0
  Read = 1
  ShUtil = 2

def timed(f):
  def func(*args):
    import time
    start = time.time()
    ret = f(*args)
    took = time.time() - start
    print("%s took %f" % (f.__name__,took))
    return ret
  return func

@timed
def cat_files_py(flist, ofile, op, logger = None, level = None):
  """
    cat files using python.

    taken from: https://gist.github.com/dimo414/2993381
  """
  op = WriteMethod.retrieve( op )
  if not isinstance(flist, (list, tuple)):
    flist = [flist]
  from RingerCore.Logger import LoggingLevel
  if level is None: level = LoggingLevel.INFO
  with open(ofile, 'wb') as out:
    for fname in progressbar(flist, len(flist), prefix="Merging: ", 
														 disp = True if logger is not None else False, step = 10,
														 logger = logger, level = level ):
      with open(fname,'rb') as f:
        if op is WriteMethod.Readlines:
          out.writelines(f.readlines())
        elif op is WriteMethod.Read:
          out.write(f.read())
        elif op is WriteMethod.ShUtil:
          import shutil
          shutil.copyfileobj(f, out)

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
