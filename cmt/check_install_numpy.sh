numpy_tgz_file="$DEP_AREA/numpy.tgz"
numpy_install_path="$INSTALL_AREA/numpy"; numpy_install_path_bslash="$INSTALL_AREA_BSLASH/numpy"

INSTALL_NUMPY=0

source "$ROOTCOREBIN/../RootCoreMacros/retrieve_python_info.sh" --numpy-info \
    || { echo "Couldn't load python information." && exit 1;}

# Check if we need to install numpy:
if test -n "$PYTHON_NUMPY_PATH"; then
  # No need to install it...
  echo "no need to install numpy."
  if test -n "$RINGERCORE_DBG_LEVEL"; then
    echo "found numpy path as: $PYTHON_NUMPY_PATH"
  fi
  test "$NUMPY_LCG" -eq "1" && add_to_env_file PYTHONPATH "$PYTHON_NUMPY_PATH" \
                            && echo "Using LCG numpy." && return 0;
  test "$PYTHON_NUMPY_PATH" != "$(readlink -f "$numpy_install_path/site-packages")/" \
       && echo "using system numpy." \
       && return 0;
  # If we get here, then environment must be local, we will only add it the environment file.
else
  # Otherwise we need to install
  INSTALL_NUMPY=1
fi


if test "$INSTALL_NUMPY" -eq "1"; then

  # Cython is a dependency for numpy.
  source "$ROOTCOREBIN/../RingerCore/cmt/check_install_cython.sh" || { echo "Couldn't install Cython and it is a dependency for numpy!" && return 1; }

  numpy_version="1.10.4"

  # Protect against corrupt files:
  if test \( ! -f "$numpy_tgz_file" \) -o \
    \( "$(md5sum -b "$numpy_tgz_file" 2> /dev/null | cut -f1 -d ' ')" != "3cb325c3dff03b5bc15206c757a26116" \) ; then
    echo "downloading ${numpy_tgz_file}..."
    numpy_afs_path="/afs/cern.ch/user/w/wsfreund/public/misc/numpy.tgz"
    if test -f $numpy_afs_path; then
      cp "$numpy_afs_path" "$numpy_tgz_file"
    else
      if test  "$RCM_GRID_ENV" -eq "1"; then
        echo "cannot reach numpy source files. Cannot download it from grid." && exit 1;
      fi
      curl -L -s -o "$numpy_tgz_file" "https://github.com/numpy/numpy/archive/v${numpy_version}.tar.gz" \
        || { echo "couldn't download numpy!" && return 1; }
    fi
  fi

  echo "installing numpy..."
  numpy_source_tmp_dir=$(mktemp -d)
  if test "$arch" = "macosx64"; then
    echo -n "extracting files... " && numpy_folder=$(tar xfzv "$numpy_tgz_file" -C $numpy_source_tmp_dir  2>&1 ) \
        && echo "done" \
        || { echo "Couldn't extract numpy files!" && exit 1; }
  else
    echo -n "extracting files... " && numpy_folder=$(tar xfzv "$numpy_tgz_file" --skip-old-files -C $numpy_source_tmp_dir  2> /dev/null) \
        && echo "done" \
        || { echo "Couldn't extract numpy files!" && exit 1; }
  fi
  test -z "$numpy_folder" && { echo "couldn't extract numpy!" && return 2;}
  if test "$arch" = "macosx64"; then
    numpy_folder=$(echo ${numpy_folder} | sed "s#x # #" | tr '\n' ' ' | cut -f2 -d ' ')
    numpy_folder=$numpy_source_tmp_dir/${numpy_folder%%\/*};
  else
    numpy_folder=$(echo "$numpy_folder" | cut -f1 -d ' ' )
    numpy_folder="$numpy_source_tmp_dir/${numpy_folder%%\/*}";
  fi
  if test -e "$numpy_install_path"; then
    rm -r "$numpy_install_path" \
      || { echo "couldn't remove old installed numpy. Please remove it manually on path \"$numpy_install_path\" and try again." && return 1; }
  fi
  mkdir -p "$numpy_install_path"
  cd "$numpy_folder"; tmp_numpy_install_folder="$numpy_install_path/lib/$PYTHON_LIB_VERSION/site-packages/"
  mkdir -p "$tmp_numpy_install_folder"
  export PYTHONPATH="$tmp_numpy_install_folder:$PYTHONPATH"
  echo -n "compiling numpy... "
  python setup.py install --prefix "$numpy_install_path" > /dev/null 2>/dev/null || { echo "Couldn't install numpy." && cd - > /dev/null && return 1;}
  echo "done"
  cd - > /dev/null
  mv $(find $numpy_install_path -name "site-packages" -type d) "$numpy_install_path"
  rm -r $(find $numpy_install_path  -maxdepth 1 -mindepth 1 -not -name "site-packages" -a -not -name "bin")
  rm -r $numpy_source_tmp_dir
fi

set -x
test -d "$numpy_install_path"                                  && export numpy_install_path_bslash
test -d "$numpy_install_path/bin"                              && add_to_env_file   PATH        "$numpy_install_path_bslash/bin"
test -d "$numpy_install_path/site-packages"                    && add_to_env_file   PYTHONPATH  "$numpy_install_path_bslash/site-packages"
test -d "$numpy_install_path/site-packages/numpy/core/include" && add_to_env_file   CPATH       "$numpy_install_path_bslash/site-packages/numpy/core/include"
set +x

source "$NEW_ENV_FILE"
