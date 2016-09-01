scipy_tgz_file="$DEP_AREA/scipy.tgz"
scipy_install_path="$INSTALL_AREA/scipy"; scipy_install_path_bslash="$INSTALL_AREA_BSLASH/scipy"

test -d "$scipy_install_path/site-packages" && add_to_env PYTHONPATH "$scipy_install_path/site-packages"

if ! python -c "import scipy.io" > /dev/null 2>&1; then

  test -z "$SCIPY" && echo "WARN: scipy is not installed, please install it with pip/easy_install." && return;

  source "$ROOTCOREBIN/../RingerCore/cmt/check_install_setup_tools.sh" || { echo "Couldn't install setup-tools which is a dependency for scipy." && return 1; }
  source "$ROOTCOREBIN/../RingerCore/cmt/check_install_cython.sh" || { echo "Couldn't install Cython and it is a dependency for scipy!" && return 1; }
  source "$ROOTCOREBIN/../RingerCore/cmt/check_install_numpy.sh" || { echo "Couldn't install numpy and it is a dependency for scipy!" && return 1; }

  # Protect against corrupt files:
  if test ! -f "$scipy_tgz_file" -o \
             "$(md5sum -b "$scipy_tgz_file" 2> /dev/null | cut -f1 -d ' ')" != "9c6bc68693d7307acffce690fe4f1076"; then
    echo "Downloading \"${scipy_tgz_file}\"..."
    scipy_afs_path="/afs/cern.ch/user/w/wsfreund/public/misc/scipy.tar.gz"
    if test -f $scipy_afs_path; then
      cp "$scipy_afs_path" "$scipy_tgz_file"
    else
      if test  "$RCM_GRID_ENV" -eq "1"; then
        echo "Cannot reach scipy source files. Cannot download it from grid." && exit 1;
      fi
      curl -s -L -o "$scipy_tgz_file" "https://github.com/scipy/scipy/archive/v0.18.0-1.tar.gz" \
        || { echo "Couldn't download scipy!" && return 1; }
    fi
  fi

  echo "installing scipy..."
  scipy_source_tmp_dir=$(mktemp -d)
  if test "$arch" = "macosx64"; then
    echo -n "extracting files... " && scipy_folder=$(tar xfzv "$scipy_tgz_file" -C $scipy_source_tmp_dir  2>&1 ) \
        && echo "done" \
        || { echo "Couldn't extract scipy files!" && exit 1; }
  else
    echo -n "extracting files... " && scipy_folder=$(tar xfzv "$scipy_tgz_file" --skip-old-files -C $scipy_source_tmp_dir ) \
        && echo "done" \
        || { echo "Couldn't extract scipy files!" && exit 1; }
  fi
  test -z "$scipy_folder" && { echo "Couldn't extract scipy!" && return 2;}
  if test "$arch" = "macosx64"; then
    scipy_folder=$(echo ${scipy_folder} | sed "s#x # #" | tr '\n' ' ' | cut -f2 -d ' ')
    scipy_folder=$scipy_source_tmp_dir/${scipy_folder%%\/*};
  else
    scipy_folder=$(echo "$scipy_folder" | cut -f1 -d ' ' )
    scipy_folder="$scipy_source_tmp_dir/${scipy_folder%%\/*}";
  fi
  if test -e "$scipy_install_path"; then
    rm -r "$scipy_install_path" \
      || { echo "Couldn't remove old installed scipy. Please remove it manually on path \"$scipy_install_path\" and try again." && return 1; }
  fi
  mkdir -p "$scipy_install_path"
  cd "$scipy_folder"; lib_scipy_install_folder="$scipy_install_path/lib/$PYTHON_LIB_VERSION/site-packages/"
  mkdir -p "$lib_scipy_install_folder"
  export PYTHONPATH="$lib_scipy_install_folder:$PYTHONPATH"
  echo -n "compiling scipy... "
  python setup.py install --prefix "$scipy_install_path" --install-lib=$lib_scipy_install_folder > /dev/null \
    || { echo "Couldn't install scipy." && test "$RCM_GRID_ENV" -eq "1" && return 1;}
  echo "done"
  cd - > /dev/null
  mv $(find $scipy_install_path -name "site-packages" -type d) "$scipy_install_path"
  rm -r $(find $scipy_install_path  -maxdepth 1 -mindepth 1 -not -name "site-packages" -a -not -name "bin")
  rm -r $scipy_source_tmp_dir
fi

test -d "$scipy_install_path"                                  && export scipy_install_path_bslash
test -d "$scipy_install_path/site-packages"                    && add_to_env_file    PYTHONPATH   "$scipy_install_path_bslash/site-packages"

source "$NEW_ENV_FILE"
