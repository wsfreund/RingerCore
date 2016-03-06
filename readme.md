
# Ringer framework: RingerCore package

This package contains a series of base functionalities for the Ringer framework and its packages. Its contents are considered implementation details and this documentation should be useful only for developers.



<h1 id="tocheading">Table of Contents</h1>
<div id="toc"></div>

# Installation

This package cannot be installed by itself. Please take a look on the projects which have other dependencies needed by this package:

 - [RingerTuning](https://github.com/wsfreund/RingerTuning) [recommended]: this project contains only the packages needed for tuning the discriminators;
 - [RingerProject](https://github.com/joaoVictorPinto/RingerProject): Use this git repository, however, if you want to install all packages related to the Ringer algorithm.

## Compile time flags

Currently, it is available the following flag:

- `--with-ringercore-dbg-level`: When specified, it will be compiled on debug mode.

# Package Organization

The package is organized as a standard RootCore package, namely:


```python
%%bash
echo "Module '$(pwd)' folders are:"
find -L . -type d -maxdepth 1 -not -name ".*"
```

    Module '/afs/cern.ch/user/w/wsfreund/Ringer/xAODRingerOfflinePorting/RingerTPFrameWork/RingerCore' folders are:
    ./RingerCore
    ./cmt
    ./python
    ./Root


Most of the provided functionalities are written in python. However, a simple adaptation of the Athena framework logging system is also available to be used in C++. Next, we enter in details about what is provided by the package.

## Python provided functionalities

The package contains the following python modules:


```python
%%bash
find -L ./python -maxdepth 2 -mindepth 1 -not -name "*.pyc" -a -not -name "__init__.py"
```

    ./python/LimitedTypeList.py
    ./python/argparse.py
    ./python/Logger.py
    ./python/util.py
    ./python/Parser.py
    ./python/OldLogger.py
    ./python/npConstants.py
    ./python/FileIO.py
    ./python/LoopingBounds.py


The `argparse` is the python standard argparse module, but it was used on python 2.6 legacy releases. The `OldLogger` provides compatibility with legacy files. More details about the other modules are given below.

### LimitedTypeList

The `LimitedTypeList` is a class factory that create lists being limited to accept objects that inherit of certain types. When an object of other type is added to the list, an exception of type `NotAllowedType` is thrown. Consider the example:



```python
from RingerCore.LimitedTypeList import LimitedTypeList
IntList = LimitedTypeList(
    "IntList", (),
    {'_acceptedTypes' : (int,)})
intList = IntList([1,2,3,4])
print intList
intList += [5,6]
print intList
intList.append(7)
print intList

intList.append(8.)
```

    [1, 2, 3, 4]
    [1, 2, 3, 4, 5, 6]
    [1, 2, 3, 4, 5, 6, 7]



    ---------------------------------------------------------------------------

    NotAllowedType                            Traceback (most recent call last)

    <ipython-input-3-ad80b0d5b22e> in <module>()
         10 print intList
         11 
    ---> 12 intList.append(8.)
    

    /afs/cern.ch/user/w/wsfreund/Ringer/xAODRingerOfflinePorting/RingerTPFrameWork/RootCoreBin/python/RingerCore/LimitedTypeList.pyc in _LimitedTypeList__append(self, var)
         57   # This is default overload for list append, checking if item is accepted
         58   if not isinstance(var, self._acceptedTypes):
    ---> 59     raise NotAllowedType( self, var, self._acceptedTypes)
         60   list.append(self,var)
         61 


    NotAllowedType: Attempted to add to IntList an object (type=<type 'float'>) which is not an instance from the allowedTypes: (<type 'int'>,)!


In the previous, we used the __init__ method for building the `IntList`. We repeat previous example using a more readable code:


```python
from RingerCore.LimitedTypeList import LimitedTypeList

class FloatList:
    __metaclass__ = LimitedTypeList
    _acceptedTypes = (float,)
    
floatList = FloatList([1.,2.,3.,4.])
print floatList
floatList.append(5)
print floatList
```

    [1.0, 2.0, 3.0, 4.0]



    ---------------------------------------------------------------------------

    NotAllowedType                            Traceback (most recent call last)

    <ipython-input-4-48ceeba11e54> in <module>()
          7 floatList = FloatList([1.,2.,3.,4.])
          8 print floatList
    ----> 9 floatList.append(5)
         10 print floatList


    /afs/cern.ch/user/w/wsfreund/Ringer/xAODRingerOfflinePorting/RingerTPFrameWork/RootCoreBin/python/RingerCore/LimitedTypeList.pyc in _LimitedTypeList__append(self, var)
         57   # This is default overload for list append, checking if item is accepted
         58   if not isinstance(var, self._acceptedTypes):
    ---> 59     raise NotAllowedType( self, var, self._acceptedTypes)
         60   list.append(self,var)
         61 


    NotAllowedType: Attempted to add to FloatList an object (type=<type 'int'>) which is not an instance from the allowedTypes: (<type 'float'>,)!


More complex classes can be created, with their own methods. Examples can be found in the [TuningTools.PreProc](https://github.com/wsfreund/TuningTools/blob/master/python/PreProc.py) module.

### Logger

This module provide the logging capabilities emulating Athena messaging system. The same levels provided by the Athena logging system are available (in decreasing verbosity order: VERBOSE, DEBUG, INFO, WARNING, FATAL).

The logging level is determined via the `LoggingLevel` "enumeration" class. It is an [`EnumStringification`](#enumstringification) class, so the values can be easily be parsed from the command line.

Meanwhile the `Logger` class adds the `self._logger` property and the level property for its inherited classes. A logger object can also be retrieved via the class method `Logger.getModuleLogger` when it is needed to use it without any object. The following example ilustrate both usage cases. 

*The logging system is also compatible with IPython notebook (jupyter), as shown in the next example. Please note, however, that the jupyter messaging system causes miss-synchronization with the print command and the messages captured from the logging module.*



```python
from RingerCore.Logger import LoggingLevel, Logger

mainLogger = Logger.getModuleLogger("mainLogger", LoggingLevel.INFO)

mainLogger.info("Starting example printing an INFO message.")
mainLogger.debug("A message ignored by the messaging system.")
mainLogger.warning("Previous message was ignored because logger level is set to INFO.")

mainLogger.level = LoggingLevel.DEBUG

mainLogger.debug("A message not ignored anymore by the messaging system.")
mainLogger.level = LoggingLevel.VERBOSE
mainLogger.verbose("Verbose messages can also be used.")
mainLogger.fatal("As well as fatal messages.")

class MyClass( Logger ):
    def __init__(self, **kw):
        Logger.__init__(self, kw)
    def fcn(self, input_):
        self._logger.verbose("Started executing MyClass.fcn(%d)", input_)
        self._logger.info("Input value was: %d", input_)
        self._logger.verbose("Successfully finished executing MyClass.fcn(%d)", input_)
        
myInst = MyClass()
myInst.fcn(2)
mainLogger.info('Current output level is: %s', myInst.level)
print 'Current output level is: ', myInst.level
myInst.level = LoggingLevel.VERBOSE
mainLogger.info('Changed mainLogger output level to: %s', myInst.level)
print 'Changed mainLogger output level to: ', myInst.level
myInst.fcn(2)
```

    Py.mainLogger                           INFO Starting example printing an INFO message.
    Py.mainLogger                        WARNING Previous message was ignored because logger level is set to INFO.
    Py.mainLogger                          DEBUG A message not ignored anymore by the messaging system.
    Py.mainLogger                        VERBOSE Verbose messages can also be used.
    Py.mainLogger                          FATAL As well as fatal messages.
    Py.MyClass                              INFO Input value was: 2
    Py.mainLogger                           INFO Current output level is: INFO
    Py.mainLogger                           INFO Changed mainLogger output level to: VERBOSE
    Py.MyClass                           VERBOSE Started executing MyClass.fcn(2)
    Py.MyClass                              INFO Input value was: 2
    Py.MyClass                           VERBOSE Successfully finished executing MyClass.fcn(2)
    Current output level is:  INFO
    Changed mainLogger output level to:  VERBOSE


### LoopingBounds

The `LoopingBounds` module provides the following classes:


```python
from RingerCore import LoopingBounds
import inspect
print [name for name, obj in inspect.getmembers(LoopingBounds, inspect.isclass) if obj.__module__ == "RingerCore.LoopingBounds"]
```

    ['LoopingBounds', 'MatlabLoopingBounds', 'PythonLoopingBounds', 'SeqLoopingBounds']


The `LoopingBounds` class is the base class for the other three classes. The `MatlabLoopingBounds` and `SeqLoopingBounds` are the same object and represents the list of indexes when it is entered a looping sequence in the matlab (using the `0:2:8` matlab notation, exchanging the `:` by `,` in the its constructor) and the last one emulates the unix `seq` command, which results in the same sequence from the matlab.

The `PythonLoopingBounds`, however, results in different looping indices when using the same bounds used in the Matlab or seq commands, as it emulates the python `range` function.

Use the module functions `transformToMatlabBounds` or `transformToPythonBounds` to transform the looping bounds objects to other types.

The main usage of these module is to let user inform the looping index sequence however it prefers, and them loop upon it. It can also save space, as the raw object can be saved with only the raw looping arguments passed to the constructor, and the object can be reconstructed independent on how the user informed it.

Next follows an example showing these behaviors.



```python
from RingerCore.LoopingBounds import *

print 'A matlab list as specified 1:3'
matlab1 = MatlabLoopingBounds(3)
print type(matlab1)
print matlab1.list()

print 'Python range(3)'
python1 = PythonLoopingBounds(3)
print type(python1)
print python1.list()

print 'Transforming python range(3) to MatlabLoopingBounds instance'
matlab_from_python1 = transformToMatlabBounds(python1)
print type(matlab_from_python1)
print matlab_from_python1.list()
```

    A matlab list as specified 1:3
    <class 'RingerCore.LoopingBounds.MatlabLoopingBounds'>
    [1, 2, 3]
    Python range(3)
    <class 'RingerCore.LoopingBounds.PythonLoopingBounds'>
    [0, 1, 2]
    Transforming python range(3) to MatlabLoopingBounds instance
    <class 'RingerCore.LoopingBounds.MatlabLoopingBounds'>
    [0, 1, 2]



```python
# Work with more complex objects:
print 'Matlab list -4:-2:-8'
matlab2 = MatlabLoopingBounds(-4,-2,-8)
print type(matlab2)
print matlab2.list()

python_from_matlab2 = transformToPythonBounds(matlab2)
print 'Transformed into PythonLoopingBounds instance'
print type(python_from_matlab2)
print python_from_matlab2.list()

python2 = PythonLoopingBounds(-4,-2,-8)
print 'Python range(-4,-2,-8)'
print type(python2)
print python2.list()

matlab_from_python2 = transformToMatlabBounds(python2)
print 'Transformed into MatlabLoopingBounds instance'
print type(matlab_from_python2)
print matlab_from_python2.list()
```

    Matlab list -4:-2:-8
    <class 'RingerCore.LoopingBounds.MatlabLoopingBounds'>
    [-4, -6, -8]
    Transformed into PythonLoopingBounds instance
    <class 'RingerCore.LoopingBounds.PythonLoopingBounds'>
    [-4, -6, -8]
    Python range(-4,-2,-8)
    <class 'RingerCore.LoopingBounds.PythonLoopingBounds'>
    [-4, -6]
    Transformed into MatlabLoopingBounds instance
    <class 'RingerCore.LoopingBounds.MatlabLoopingBounds'>
    [-4, -6]



```python
print 'It is also possible to retrieve the original entered arguments:'
print python2.getOriginalVec()
print 'Python range(-4,-2,-8) is string represented as: ', str(python2)

print 'The string can also be formated to include some identification flag for the bounds, e.g.:'
print "PythonLoopingBounds(5,10).formattedString('s'):", PythonLoopingBounds(5,10).formattedString('s')
```

    It is also possible to retrieve the original entered arguments:
    [-4, -2, -8]
    Python range(-4,-2,-8) is string represented as:  l-006.u-004
    The string can also be formated to include some identification flag for the bounds, e.g.:
    PythonLoopingBounds(5,10).formattedString('s'): sl0005.su0009


### Parser

Provides default parsers to be used to create python executables. Currently, it provides the following parsers:

- gridParser: Provides most argument options as the panda executable command `prun`, but without specifying an input or an output;
- inGridParser: Extends `gridParser` to allow user to also specify input dataset;
- outGridParser: Extends `gridParser` to allow user to also specify output dataset;
- ioGridParser: Extends `gridParser` to allow user to also specify both input and output datasets;
- loggerParser: Provides logging options to be provided to the `LoggingLevel` class and to be distributed over the `Logger` instances.

Consider, for instance, that you want to create an python module that can be executed by the user and can capture the gridParser and loggerParser arguments. This can be done as follows:


```python
try:
  import argparse
except ImportError:
  from RingerCore import argparse

from RingerCore.Parser import loggerParser, gridParser
parser = argparse.ArgumentParser(add_help = False,
                                 description = 'A parser that provides gridParser and loggerParser arguments.',
                                 parents = [gridParser, loggerParser],
                                 conflict_handler = 'resolve')

parser.print_help()
```

    usage: __main__.py [--site [GRID_SITE]] [--excludedSite [GRID_EXCLUDEDSITE]]
                       [--debug] [--nJobs [GRID_NJOBS]]
                       [--excludeFile [GRID_EXCLUDEFILE]] [--disableAutoRetry]
                       [--extFile [GRID_EXTFILE]]
                       [--maxNFilesPerJob [GRID_MAXNFILESPERJOB]]
                       [--cloud [GRID_CLOUD]] [--nGBPerJob [GRID_NGBPERJOB]]
                       [--skipScout] [--memory GRID_MEMORY] [--long]
                       [--useNewCode] [--dry-run] [--allowTaskDuplication]
                       [-itar [InTarBall] | -otar [OutTarBall]]
                       [--output-level {DEBUG,ERROR,FATAL,INFO,VERBOSE,WARNING}]
    
    A parser that provides gridParser and loggerParser arguments.
    
    optional arguments:
      --site [GRID_SITE]    The site location where the job should run.
      --excludedSite [GRID_EXCLUDEDSITE]
                            The excluded site location.
      --debug               Submit GRID job on debug mode.
      --nJobs [GRID_NJOBS]  Number of jobs to submit.
      --excludeFile [GRID_EXCLUDEFILE]
                            Files to exclude from environment copied to grid.
      --disableAutoRetry    Flag to disable auto retrying jobs.
      --extFile [GRID_EXTFILE]
                            External file to add.
      --maxNFilesPerJob [GRID_MAXNFILESPERJOB]
                            Maximum number of files per job.
      --cloud [GRID_CLOUD]  The cloud where to submit the job.
      --nGBPerJob [GRID_NGBPERJOB]
                            Maximum number of GB per job.
      --skipScout           Flag to disable auto retrying jobs.
      --memory GRID_MEMORY  Needed memory to run in MB.
      --long                Submit for long queue.
      --useNewCode          Flag to disable auto retrying jobs.
      --dry-run             Only print grid resulting command, but do not execute
                            it. Used for debugging submission.
      --allowTaskDuplication
                            Flag to disable auto retrying jobs.
      -itar [InTarBall], --inTarBall [InTarBall]
                            The environemnt tarball for posterior usage.
      -otar [OutTarBall], --outTarBall [OutTarBall]
                            The environemnt tarball for posterior usage.
      --output-level {DEBUG,ERROR,FATAL,INFO,VERBOSE,WARNING}
                            The output level for the main logger


With this combination, many different parsers can be easily created by mixing the provided parsers with other specific parsers attending the needs for your own job. Available usage examples can be seen on [`createData.py`](https://github.com/wsfreund/TuningTools/blob/master/scripts/standalone/createData.py), [`createTuningJobFiles.py`](https://github.com/wsfreund/TuningTools/blob/master/scripts/standalone/createTuningJobFiles.py) etc. In some cases, you might want to make some options unavailable for the user, an example on how to do this can be seen on [`runGRIDtuning.py`](https://github.com/wsfreund/TuningTools/blob/master/scripts/grid_scripts/runGRIDtuning.py).

This module also provides some namespaces that should be used when parsing arguments using the loggerParser and the grid parsers. In the first case, make sure to pass the `LoggerNamespace` to the parser `parse_args` method. When using the grid parsers, the `GridNamespace` should be used. It provides methods for setting the `bexec`, `exec` job arguments. The last also inherits from the LoggerNamespace, so it can also handle the logger parser arguments. 


*Consider taking a look at [`runGRIDtuning.py`](https://github.com/wsfreund/TuningTools/blob/master/scripts/grid_scripts/runGRIDtuning.py) to observe a more detailed working code using `GridNamespace`.*


```python
from RingerCore.Logger import LoggingLevel, Logger
logger = Logger.getModuleLogger("logger", LoggingLevel.INFO)

from RingerCore.Parser import ioGridParser, GridNamespace

args = ioGridParser.parse_args(['--dry-run','--inDS','user.wsfreund.some.inds',
                                '--outDS','user.wsfreund.some.outds','--skipScout',
                                '--outputs','*.root' ], 
                               namespace=GridNamespace('prun'))
args.setExec("""source ./setrootcore.sh;
                {someJob} input_to_the_job
             """.format( someJob = "\$ROOTCOREBIN/user_scripts/SomePackage/some_script.py"))

args.run_cmd()
```

    Py.GridNamespace                        INFO Command:
    prun \
         --exec \
           "source ./setrootcore.sh; \
             \$ROOTCOREBIN/user_scripts/SomePackage/some_script.py input_to_the_job;" \
         --skipScout \
         --excludeFile="*.o,*.so,*.a,*.gch" \
         --excludedSite=ANALY_CERN_CLOUD,ANALY_SLAC,ANALY_CERN_SHORT,ANALY_CONNECT_SHORT,ANALY_BNL_SHORT,ANALY_BNL_EC2E1,ANALY_SWT2_CPB \
         --inDS=user.wsfreund.some.inds \
         --outDS=user.wsfreund.some.outds \
         --outputs=*.root \
         --site=AUTO \
         --skipScout \
    


### npConstants

This class allows to bypass the numpy defaults for the `order` and `dtype` and use new defaults. 


```python
from RingerCore.npConstants import npConstants
import inspect
print(inspect.getdoc(npConstants))
```

    This class is used by dependent packages to armonize numpy flags. Currently
    it can be used obtain armonization in the following information:
      - fortran/c representation;
        o dtype: retrieves floating point string used on numpy
      - dimensions:
        o access: access numpy indexes
        o shape: return shape using npat and nobs
        o odim: retrieves the observations axis index
        o pdim: retrieves the patterns axis index
      - floating point data type:
        o fp_dtype: retrieves floating point dtype used on numpy
      - integer data types:
        o int_dtype: common integer dtype
        o scounter_dtype: short integer dtype to use as counter
        o flag_dtype: the integer to use on flags (usually only -1,0,1 are
        flagged)


Several different numpy configurations can be set and changed accordingly depending on how it is needed to work with the data representation. E.g.:


```python
from RingerCore.npConstants import npConstants
import numpy as np
npDefault1 = npConstants( useFortran = True,
                          fp_dtype   = np.float64,
                          int_dtype  = np.int64 )
npDefault1

```




    npConstants(fp_dtype=dtype('float64'),int_dtype=dtype('int64'),scounter_dtype=dtype('uint8'),flag_dtype=dtype('int8'),order=F)




```python
from RingerCore.npConstants import npConstants
import numpy as npb
npDefault2 = npConstants( useFortran = False,
                          fp_dtype   = np.float32,
                          int_dtype  = np.int32 )
npDefault2
```




    npConstants(fp_dtype=dtype('float32'),int_dtype=dtype('int32'),scounter_dtype=dtype('uint8'),flag_dtype=dtype('int8'),order=C)




```python
npCurrent = npDefault1

print "Using npDefault1"
zeros = npCurrent.int_zeros(npCurrent.shape(npat=2,nobs=4))
print zeros
print zeros.flags
print zeros.dtype
print "Accessing pattern index 1: ", zeros[npCurrent.access(pidx=1)]
print "Accessing observation index 2: ", zeros[npCurrent.access(oidx=2)]
print "====="
```

    Using npDefault1
    [[0 0 0 0]
     [0 0 0 0]]
      C_CONTIGUOUS : False
      F_CONTIGUOUS : True
      OWNDATA : True
      WRITEABLE : True
      ALIGNED : True
      UPDATEIFCOPY : False
    int64
    Accessing pattern index 1:  [0 0 0 0]
    Accessing observation index 2:  [0 0]
    =====



```python
npCurrent = npDefault2

print "Using npDefault2"
zeros = npCurrent.int_zeros(npCurrent.shape(npat=2,nobs=4))
print zeros
print zeros.flags
print zeros.dtype
print "Accessing pattern index 1: ", zeros[npCurrent.access(pidx=1)]
print "Accessing observation index 2: ", zeros[npCurrent.access(oidx=2)]
print "====="
```

    Using npDefault2
    [[0 0]
     [0 0]
     [0 0]
     [0 0]]
      C_CONTIGUOUS : True
      F_CONTIGUOUS : False
      OWNDATA : True
      WRITEABLE : True
      ALIGNED : True
      UPDATEIFCOPY : False
    int32
    Accessing pattern index 1:  [0 0 0 0]
    Accessing observation index 2:  [0 0]
    =====


### FileIO

This module provides three main methods. The `save` and `load` methods which can be used to respectively simplify writing and reading files. They can handle `Pickle` and `numpy` file formats, which might be compressed or not. Consider the following example:


```python
from RingerCore.FileIO import save
import numpy as np
help(save)

# Pickle files
someList = [1,2,3,4]
outputFile = save(someList,'someList')
print 'Saved "%s" file.' % outputFile
outputFile = save(someList,'someList',compress=False)
print 'Saved uncompressed file %s.' % outputFile

# Numpy files
array = np.array(someList)
array2 = np.arange(10)
outputFile = save(array,'numpy_file',protocol='save')
print 'Saved "%s" file.' % outputFile
outputFile = save({'array' : array, 'array2' : array2},'numpy_filez',protocol='savez')
print 'Saved "%s" file.' % outputFile
outputFile = save({'array' : array, 'array2' : array2},'numpy_filez_compressed',protocol='savez_compressed')
print 'Saved "%s" file.' % outputFile
```

    Help on function save in module RingerCore.FileIO:
    
    save(o, filename, **kw)
        Save an object to disk.
    
    Saved "someList.pic.gz" file.
    Saved uncompressed file someList.pic.
    Saved "numpy_file" file.
    Saved "numpy_filez" file.
    Saved "numpy_filez_compressed" file.



```python
%%bash
ls -lh *.pic *.gz *.npz *.npy
```

    -rw-r--r-- 1 wsfreund zp 112 Mar  6 07:18 numpy_file.npy
    -rw-r--r-- 1 wsfreund zp 386 Mar  6 07:18 numpy_filez_compressed.npz
    -rw-r--r-- 1 wsfreund zp 484 Mar  6 07:18 numpy_filez.npz
    -rw-r--r-- 1 wsfreund zp  16 Mar  6 07:18 someList.pic
    -rw-r--r-- 1 wsfreund zp  49 Mar  6 07:18 someList.pic.gz



```python
from RingerCore.FileIO import load
help(load)

someList = load('someList.pic')
print 'someList loaded from someList.pic: ', someList
someList = load('someList.pic.gz')
print 'someList loaded from someList.pic.gz: ', someList
array = load('numpy_file.npy')
print 'array loaded from numpy_file.npy: ', array
f = load('numpy_filez.npz')
print 'array loaded from numpy_filez.npz: ', f['array']
print 'array2 loaded from numpy_filez.npz: ', f['array2']
f = load('numpy_filez_compressed.npz')
print 'array loaded from numpy_filez_compressed.npz: ', f['array']
print 'array2 loaded from numpy_filez_compressed.npz: ', f['array2']
```

    Help on function load in module RingerCore.FileIO:
    
    load(filename, decompress='auto')
        Loads an object from disk
    
    someList loaded from someList.pic:  [1, 2, 3, 4]
    someList loaded from someList.pic.gz:  [1, 2, 3, 4]
    array loaded from numpy_file.npy:  [1 2 3 4]
    array loaded from numpy_filez.npz:  [1 2 3 4]
    array2 loaded from numpy_filez.npz:  [0 1 2 3 4 5 6 7 8 9]
    array loaded from numpy_filez_compressed.npz:  [1 2 3 4]
    array2 loaded from numpy_filez_compressed.npz:  [0 1 2 3 4 5 6 7 8 9]


Finally, an utilitary module method is provided which allows recursively expanding system folders to retrieve files within it. It is available under the name of `expandFolders`.

### util

This module provide utilities miscellanea. Some of those are covered here:


#### EnumStringification

This class allows emulating a python enumeration and easy transformation from string to int or vice versa through the methods `tostring` and `fromstring`. Its method `retrieve` makes sure that the used string or value is valid within the enumeration and returns the corresponding enumeration integer.

In the next example we show usage for a case sensitive EnumStringification:


```python
from RingerCore.util import EnumStringification

class SomeEnum( EnumStringification ):
    val1 = 1
    val2 = 2
    
val = SomeEnum.val1
print val
val = SomeEnum.retrieve("val1")
print val
val = SomeEnum.retrieve("val2")
print val

print SomeEnum.tostring(val)

print SomeEnum.fromstring("val1")

val = SomeEnum.retrieve("Val2")
```

    1
    1
    2
    val2
    1



    ---------------------------------------------------------------------------

    ValueError                                Traceback (most recent call last)

    <ipython-input-20-17288deedc28> in <module>()
         16 print SomeEnum.fromstring("val1")
         17 
    ---> 18 val = SomeEnum.retrieve("Val2")
    

    /afs/cern.ch/user/w/wsfreund/Ringer/xAODRingerOfflinePorting/RingerTPFrameWork/RootCoreBin/python/RingerCore/util.pyc in retrieve(cls, val)
         79       if val is None:
         80           raise ValueError("String (%s) does not match any of the allowed values %r." % \
    ---> 81               (oldVal, allowedValues))
         82     else:
         83       if not val in [attr[1] for attr in allowedValues]:


    ValueError: String (Val2) does not match any of the allowed values [('val1', 1), ('val2', 2)].


However, the match case may not be the desired behavior. In those cases, set the `_ignoreCase` property to True, as follows:


```python
from RingerCore.util import EnumStringification

class IgnoreCaseEnum( EnumStringification ):
    _ignoreCase = True
    val1 = 1
    vAl2 = 2
    
val = IgnoreCaseEnum.retrieve("Val2")
print val

# It is also possible to convert to the defined string spelling, via
print IgnoreCaseEnum.tostring(IgnoreCaseEnum.fromstring("VAL2"))
```

    2
    vAl2


#### retrieve_kw and NotSet

When used in conjunction, allows to bypass default configuration retrieved on higher level classes and assure that the lower level classes default configuration will be used. This is quite important to make sure that only one default value will be available in the python code and that it is not needed to change all references to that property through all python codes. Take a look on [`python/CreateData.py`](https://github.com/wsfreund/TuningTools/tree/master/python/CreateData.py) and [`python/FilterEvents.py`](https://github.com/wsfreund/TuningTools/tree/master/python/FilterEvents.py) `__call__` methods to see an usage example.


#### checkForUnusedVars

Used to print remaining keywords on dictionaries. Usually used to display warnings of unused keywords:


```python
from RingerCore.util import checkForUnusedVars

def someFcn(**kw):
    arg1 = kw.pop('arg1', None)
    arg2 = kw.pop('arg2', None)
    checkForUnusedVars(kw)

someFcn(arg0=0,arg1=1,arg2=2,arg3=3)
```

    WARNING:Obtained not needed parameter: arg0
    WARNING:Obtained not needed parameter: arg3


#### traverse

It is used to loop over the individual objects upon multiple iterable objects and possibly changing the looping object. Consider the examples:


```python
# Read every object contained in the iterables (list, tuple) 
# This could be considered zero-level "iterable objects" in the iterable list
from RingerCore.util import traverse
a = [[[1,2,3],[2,3],[3,4,5,6]],[[[4,7],[]],[6]],7]
for obj in traverse(a,(list, tuple),0): print obj
# obj is: (holden object, index in parent iterable, parent iterable, level, depth)
```

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


Now let's loop over the iterables and change their holden values:


```python
# Read every object contained in the iterables (list, tuple) 
# This could be considered zero-level "iterable objects" in the iterable list
from RingerCore.util import traverse
a = [[[1,2,3],[2,3],[3,4,5,6]],[[[4,7],[]],[6]],7]
for _, idx, parent, _, _ in traverse(a,(list, tuple),0): parent[idx] = "Changed"
a
```




    [[['Changed', 'Changed', 'Changed'],
      ['Changed', 'Changed'],
      ['Changed', 'Changed', 'Changed', 'Changed']],
     [[['Changed', 'Changed'], []], ['Changed']],
     'Changed']



Instead looping over all objects in the iterable list, we may want to loop over some iterables keeping some "depth":


```python
# Read every "first level" iterables of type (list, tuple) in the iterable list
from RingerCore.util import traverse
a = [[[1,2,3],[2,3],[3,4,5,6]],[[[4,7],[]],[6]],7]
for obj in traverse(a,(list, tuple),1): print obj
```

    ([1, 2, 3], 0, [[1, 2, 3], [2, 3], [3, 4, 5, 6]], 1, 3)
    ([2, 3], 0, [[1, 2, 3], [2, 3], [3, 4, 5, 6]], 1, 3)
    ([3, 4, 5, 6], 0, [[1, 2, 3], [2, 3], [3, 4, 5, 6]], 1, 3)
    ([4, 7], 0, [[4, 7], []], 1, 4)
    ([6], 0, [[[4, 7], []], [6]], 1, 3)
    ([[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 2, None, 1, 1)



```python
# Read every "second level" iterables of type (list, tuple) in the iterable list
from RingerCore.util import traverse
a = [[[1,2,3],[2,3],[3,4,5,6]],[[[4,7],[]],[6]],7]
for obj in traverse(a,(list, tuple),2): print obj
```

    ([[1, 2, 3], [2, 3], [3, 4, 5, 6]], 0, [[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 2, 2)
    ([[4, 7], []], 0, [[[4, 7], []], [6]], 2, 3)
    ([[[4, 7], []], [6]], 1, [[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 2, 2)



```python
# Read every "third level" iterables of type (list, tuple) in the iterable list
from RingerCore.util import traverse
a = [[[1,2,3],[2,3],[3,4,5,6]],[[[4,7],[]],[6]],7]
for obj in traverse(a,(list, tuple),3): print obj
```

    ([[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 0, None, 3, 1)



```python
# Read every "fourth level" iterables of type (list, tuple) in the iterable list
from RingerCore.util import traverse
a = [[[1,2,3],[2,3],[3,4,5,6]],[[[4,7],[]],[6]],7]
for obj in traverse(a,(list, tuple),4): print obj
```

    ([[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 1, None, 4, 1)



```python
# Read every "fifth level" iterables of type (list, tuple) in the iterable list
from RingerCore.util import traverse
a = [[[1,2,3],[2,3],[3,4,5,6]],[[[4,7],[]],[6]],7]
for obj in traverse(a,(list, tuple),5): print obj
```

## C++ provided functionalities

The most important C++ functionality provided is available in the [`RingerCore/MsgStream.h`](https://github.com/wsfreund/RingerCore/blob/master/RingerCore/MsgStream.h) file. It is based on Athena framework's MsgStream, but does not need the Gaudi infrastructure. The name was changed to `MsgStreamMirror` as it cannot have the same name from the Asg class, otherwise it would generate conflicts when running PyROOT.

It also provided the macros which emulate the same behavior on Athena:

```
MSG_DEBUG(msg)
MSG_INFO(msg)
MSG_WARNING(msg)
MSG_ERROR(msg)
MSG_FATAL(msg)
```

Finally, to have access to those macros on your classes, make sure to inherit from `MsgService`, also defined in this file. In case that multiple inherited classes must use this service, and it is wanted the messaging system to display the most derived class name, overwrite the `IMsgService` constructor to use the most inherited class name. E.g.:

```C++
/** 
 * Supose A -> B 
 * then:
 **/

class A : public MsgService
{
    A()
      : IMsgService("A"),
        MsgService(MSG::INFO)
      {;}
};

class B : public A
{
    B()
      : IMsgService("B"),
        A()
      {;}
};

```

<script type="text/javascript">
    show=true;
    function toggle(){
        if (show){
            $('div.input').hide();
        }else{
            $('div.input').show();
        }
        show = !show
    }
$.getScript('https://kmahelona.github.io/ipython_notebook_goodies/ipython_notebook_toc.js')
</script>
<a href="javascript:toggle()" target="_self"></a>
