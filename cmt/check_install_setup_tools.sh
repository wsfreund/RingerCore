setuptools_tgz_file="$DEP_AREA/setuptools.tgz"
setuptools_install_path="$INSTALL_AREA/setuptools"; setuptools_install_path_bslash="$INSTALL_AREA_BSLASH/setuptools"

test -d "$setuptools_install_path/site-packages" && add_to_env PYTHONPATH "$setuptools_install_path/site-packages"

if ! python -c "import setuptools" > /dev/null 2>&1; then
  # Protect against corrupt files:
  if test ! -f "$setuptools_tgz_file" -o \
             "$(md5sum -b "$setuptools_tgz_file" 2> /dev/null | cut -f1 -d ' ')" != "0744ee90ad266fb117d59f94334185d0"; then
    echo "Downloading \"${setuptools_tgz_file}\"..."
    setuptools_afs_path="/afs/cern.ch/user/w/wsfreund/public/misc/setuptools.tar.gz"
    if test -f $setuptools_afs_path; then
      cp "$setuptools_afs_path" "$setuptools_tgz_file"
    else
      if test  "$RCM_GRID_ENV" -eq "1"; then
        echo "Cannot reach setuptools source files. Cannot download it from grid." && exit 1;
      fi
      curl -s -L -o "$setuptools_tgz_file" "https://pypi.python.org/packages/32/3c/e853a68b703f347f5ed86585c2dd2828a83252e1216c1201fa6f81270578/setuptools-26.1.1.tar.gz" \
        || { echo "Couldn't download setuptools!" && return 1; }
    fi
  fi

  echo "installing setuptools..."
  setuptools_source_tmp_dir=$(mktemp -d)
  if test "$arch" = "macosx64"; then
    echo -n "extracting files... " && setuptools_folder=$(tar xfzv "$setuptools_tgz_file" -C $setuptools_source_tmp_dir  2>&1 ) \
        && echo "done" \
        || { echo "Couldn't extract setuptools files!" && exit 1; }
  else
    echo -n "extracting files... " && setuptools_folder=$(tar xfzv "$setuptools_tgz_file" --skip-old-files -C $setuptools_source_tmp_dir ) \
        && echo "done" \
        || { echo "Couldn't extract setuptools files!" && exit 1; }
  fi
  test -z "$setuptools_folder" && { echo "Couldn't extract setuptools!" && return 2;}
  if test "$arch" = "macosx64"; then
    setuptools_folder=$(echo ${setuptools_folder} | sed "s#x # #" | tr '\n' ' ' | cut -f2 -d ' ')
    setuptools_folder=$setuptools_source_tmp_dir/${setuptools_folder%%\/*};
  else
    setuptools_folder=$(echo "$setuptools_folder" | cut -f1 -d ' ' )
    setuptools_folder="$setuptools_source_tmp_dir/${setuptools_folder%%\/*}";
  fi
  if test -e "$setuptools_install_path"; then
    rm -r "$setuptools_install_path" \
      || { echo "Couldn't remove old installed setuptools. Please remove it manually on path \"$setuptools_install_path\" and try again." && return 1; }
  fi
  mkdir -p "$setuptools_install_path"
  cd "$setuptools_folder"; lib_setuptools_install_folder="$setuptools_install_path/lib/$PYTHON_LIB_VERSION/site-packages/"
  mkdir -p "$lib_setuptools_install_folder"
  export PYTHONPATH="$lib_setuptools_install_folder:$PYTHONPATH"
  echo -n "compiling setuptools... "
  python setup.py install --prefix "$setuptools_install_path" --install-lib=$lib_setuptools_install_folder > /dev/null \
    || { echo "Couldn't install setuptools." && return 1;}
  echo "done"
  cd - > /dev/null
  mv $(find $setuptools_install_path -name "site-packages" -type d) "$setuptools_install_path"
  rm -r $(find $setuptools_install_path  -maxdepth 1 -mindepth 1 -not -name "site-packages" -a -not -name "bin")
  rm -r $setuptools_source_tmp_dir
fi

test -d "$setuptools_install_path"                                  && export setuptools_install_path_bslash
test -d "$setuptools_install_path/site-packages"                    && add_to_env_file    PYTHONPATH   "$setuptools_install_path_bslash/site-packages"

source "$NEW_ENV_FILE"
