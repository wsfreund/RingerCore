source $ROOTCOREBIN/../RingerCore/cmt/base_env.sh || { echo "Couldn't load base shell environment." && exit 1; }

PYTHON_EXEC_PATH=`pyenv whence --path python 2>/dev/null || which python`
PYTHON_EXEC_PATH=`readlink -f $PYTHON_EXEC_PATH`
PYTHON_INCLUDE_CANDIDATES=${PYTHON_EXEC_PATH//bin\/python*/include\/}
PYTHON_INCLUDE_CANDIDATES=`find $PYTHON_INCLUDE_CANDIDATES -name "python?.?" -type d` # pick only last result
PYTHON_VERSION_NUM=0
for candidate in $PYTHON_INCLUDE_CANDIDATES
do
  version=`basename $candidate`
  candidateVNUM=${version//python/}
  candidateVNUM=${candidateVNUM//./}
  if test "$candidateVNUM" -ge "$PYTHON_VERSION_NUM"
  then
    PYTHON_LIB_VERSION=$version
    vNUM=$candidateVNUM
  fi
done
PYTHON_INCLUDE_PATH=""
for candidate in $PYTHON_INCLUDE_CANDIDATES
do
  if test "`basename $candidate`" = $PYTHON_LIB_VERSION
  then
    if test -e $candidate/import.h -o -e $candidate/pyconfig.h
    then
      PYTHON_INCLUDE_PATH="$PYTHON_INCLUDE_PATH $include_marker$candidate"
    fi
  fi
done

PYTHON_NUMPY_PATH=$(python -c "import numpy; path=numpy.__file__; print path[:path.find('numpy')]") 2> /dev/null

# Add numpy to python path and to include path if we are using afs:
if test "x$PYTHON_NUMPY_PATH" = "x" -a -e /afs/cern.ch/sw/lcg/external/pyanalysis/ 
then
  PYTHON_NUMPY_PATH=`find /afs/cern.ch/sw/lcg/external/pyanalysis/ -maxdepth 1 -name "*$PYTHON_LIB_VERSION" | tail -1`
  PYTHON_NUMPY_PATH=$PYTHON_NUMPY_PATH/$rootCmtConfig/lib/$PYTHON_LIB_VERSION/site-packages/
  INCLUDE_NUMPY="$include_system_marker$PYTHON_NUMPY_PATH/numpy/core/include"
else
  if test -e $PYTHON_NUMPY_PATH/numpy/core/include; then
    INCLUDE_NUMPY="$include_system_marker$PYTHON_NUMPY_PATH/numpy/core/include"
  else
    if test -e /usr/include/numpy; then
      INCLUDE_NUMPY="$include_system_marker/usr/include/numpy"
    fi
  fi
fi

export PYTHON_LIB_VERSION
export PYTHON_VERSION_NUM
export PYTHON_INCLUDE_PATH
export PYTHON_EXEC_PATH
