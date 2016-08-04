cython_tgz_file="$DEP_AREA/cython.tgz"
cython_install_path="$INSTALL_AREA/cython"; cython_install_path_bslash="$INSTALL_AREA_BSLASH/cython"

test -d "$cython_install_path/site-packages" && add_to_env PYTHONPATH "$cython_install_path/site-packages"

if ! python -c "import Cython" > /dev/null 2> /dev/null; then
  cython_version=Cython-0.23.4.tar.gz

  echo "installing cython..."
  cython_source_tmp_dir=$(mktemp -d)
	if test "$arch" = "macosx64"; then
    echo -n "extracting files... " && cython_folder=$(tar xfzv "$cython_tgz_file" -C $cython_source_tmp_dir  2>&1 ) \
        && echo "done" \
        || { echo "Couldn't extract cython files!" && exit 1; }
	else
    echo -n "extracting files... " && cython_folder=$(tar xfzv "$cython_tgz_file" --skip-old-files -C $cython_source_tmp_dir  2> /dev/null) \
        && echo "done" \
        || { echo "Couldn't extract cython files!" && exit 1; }
  fi
	test -z "$cython_folder" && { echo "Couldn't extract cython!" && return 2;}
  if test "$arch" = "macosx64"; then
    cython_folder=$(echo ${cython_folder} | sed "s#x # #" | tr '\n' ' ' | cut -f2 -d ' ')
    cython_folder=$cython_source_tmp_dir/${cython_folder%%\/*};
  else
    cython_folder=$(echo "$cython_folder" | cut -f1 -d ' ' )
    cython_folder="$cython_source_tmp_dir/${cython_folder%%\/*}";
  fi
  if test -e "$cython_install_path"; then
    rm -r "$cython_install_path" \
      || { echo "Couldn't remove old installed cython. Please remove it manually on path \"$cython_install_path\" and try again." && return 1; }
  fi
  mkdir -p "$cython_install_path"
  cd "$cython_folder"; tmp_cython_install_folder="$cython_install_path/lib/$PYTHON_LIB_VERSION/site-packages/"
  mkdir -p "$tmp_cython_install_folder"
  export PYTHONPATH="$tmp_cython_install_folder:$PYTHONPATH"
  echo -n "compiling cython... "
  python setup.py install --prefix "$cython_install_path" > /dev/null 2>/dev/null || { echo "Couldn't install cython." && return 1;}
  echo "done"
  cd - > /dev/null
  mv $(find $cython_install_path -name "site-packages" -type d) "$cython_install_path"
  rm -r $(find $cython_install_path  -maxdepth 1 -mindepth 1 -not -name "site-packages" -a -not -name "bin")
  rm -r $cython_source_tmp_dir
fi

test -d "$cython_install_path"                                  && export cython_install_path_bslash
test -d "$cython_install_path/bin"                              && add_to_env_file    PATH         "$cython_install_path_bslash/bin"
test -d "$cython_install_path/site-packages"                    && add_to_env_file    PYTHONPATH   "$cython_install_path_bslash/site-packages"
#test -d "$cython_install_path/site-packages/cython/core/include" && add_to_env_file CPATH "$cython_install_path_bslash/site-packages/cython/core/include"

source "$NEW_ENV_FILE"
