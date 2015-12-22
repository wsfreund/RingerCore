
arch=`root-config --arch`
if test "$arch" = "macosx64"
then
  include_marker="-I"
  include_system_marker="-isystem"
else
  include_marker="-I"
  include_system_marker="-isystem"
fi

PYTHON_EXEC_PATH=`which python`
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

export PYTHON_LIB_VERSION
export PYTHON_VERSION_NUM
export PYTHON_INCLUDE_PATH
export PYTHON_EXEC_PATH
