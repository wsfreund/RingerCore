show_help() {
cat << EOF
Usage: ${0##*/} [--headers-only] [--bootstrap-extra-args="BOOTSTRAP_EXTRA_ARGS"] 
                [--b2-extra-args="B2_EXTRA_ARGS"]

Check if boost is available and, if not available, install it to "\$INSTALL_AREA/boost".

    -h             display this help and return
    --check-header
                   The header file to check if boost functionality is available.
    --headers-only
                   Do not compile boost, just add the headers to installation
                   place.  It is useful to reduce compilation time and resource
                   usage when all you use are some boost templates.
    --bootstrap-extra-args        
                   Add extra arguments to booststrap. Useful to request compilation 
                   of some specific libraries.
                   This option is ignored when --header-only is set.
    --b2-extra-args
                   Add extra arguments to b2. Useful to request compilation of
                   some specific libraries.
                   This option is ignored when --header-only is set.
    --disable-recheck
                   If a .gch file is available, do not try to recheck if boost
                   is available, just asume that boost instalation, if needed,
                   was already handled.
EOF
}

# Default values:
DISABLE_RECHECK=0 # Whether to recheck if it is needed to install boost
HEADERS_ONLY=0 # Whether to 
CHECK_HEADER="./boost_test.h"

while :; do
  case $1 in
    -h|-\?|--help)   # Call a "show_help" function to display a synopsis, then exit.
      show_help
      return
      ;;
    --check-header)
      if [ ${2#--} != $2 ]; then
        CHECK_HEADER=1
        echo 'ERROR: "--check-header" requires a non-empty option argument.\n' >&2
      else
        CHECK_HEADER=$2
        shift 2
        continue
      fi
      ;;
    --check-header=?*)
      CHECK_HEADER=${1#*=} # Delete everything up to "=" and assign the remainder.
      ;;
    --check-header=)   # Handle the case of an empty --check-header=
      echo 'ERROR: "--check-header" requires a non-empty option argument.\n' >&2
      return 1
      ;;
    --headers-only)
      if [ ${2#--} != $2 ]; then
        HEADERS_ONLY=1
      else
        HEADERS_ONLY=$2
        shift 2
        continue
      fi
      ;;
    --headers-only=?*)
      HEADERS_ONLY=${1#*=} # Delete everything up to "=" and assign the remainder.
      ;;
    --headers-only=)   # Handle the case of an empty --headers-only=
      echo 'ERROR: "--headers-only" requires a non-empty option argument.\n' >&2
      return 1
      ;;
    --disable-recheck)
      if [ ${2#--} != $2 ]; then
        DISABLE_RECHECK=1
      else
        DISABLE_RECHECK=$2
        shift 2
        continue
      fi
      ;;
    --disable-recheck=?*)
      DISABLE_RECHECK=${1#*=} # Delete everything up to "=" and assign the remainder.
      ;;
    --disable-recheck=)   # Handle the case of an empty --disable-recheck=
      echo 'ERROR: "--disable-recheck" requires a non-empty option argument.\n' >&2
      return 1
      ;;
    --b2-extra-args)
      if [ ${2#--} != $2 ]; then
        echo 'ERROR: "--b2-extra-args" requires a non-empty option argument.\n' >&2
        return 1
      else
        B2_EXTRA_ARGS=$2
        shift 2
        continue
      fi
      ;;
    --b2-extra-args=?*)
      B2_EXTRA_ARGS=${1#*=} # Delete everything up to "=" and assign the remainder.
      ;;
    --b2-extra-args=)   # Handle the case of an empty --disable-recheck=
      echo 'ERROR: "--b2-extra-args" requires a non-empty option argument.\n' >&2
      return 1
      ;;
    --bootstrap-extra-args)
      if [ ${2#--} != $2 ]; then
        echo 'ERROR: "--bootstrap-extra-args" requires a non-empty option argument.\n' >&2
        return 1
      else
        BOOTSTRAP_EXTRA_ARGS=$2
        shift 2
        continue
      fi
      ;;
    --bootstrap-extra-args=?*)
      BOOTSTRAP_EXTRA_ARGS=${1#*=} # Delete everything up to "=" and assign the remainder.
      ;;
    --bootstrap-extra-args=)   # Handle the case of an empty --disable-recheck=
      echo 'ERROR: "--bootstrap-extra-args" requires a non-empty option argument.\n' >&2
      return 1
      ;;
    --extra-test-args)
      if [ ${2#--} != $2 ]; then
        echo 'ERROR: "--extra-test-args" requires a non-empty option argument.\n' >&2
        return 1
      else
        EXTRA_TEST_ARGS=$2
        shift 2
        continue
      fi
      ;;
    --extra-test-args=?*)
      EXTRA_TEST_ARGS=${1#*=} # Delete everything up to "=" and assign the remainder.
      ;;
    --extra-test-args=)       # Handle the case of an empty --disable-recheck=
      echo 'ERROR: "--extra-test-args" requires a non-empty option argument.\n' >&2
      return 1
      ;;
    --)              # End of all options.
      shift
      break
      ;;
    -?*)
      echo 'WARN: Unknown option (ignored): %s\n' "$1" >&2
      ;;
    *)               # Default case: If no more options then break out of the loop.
      break
  esac
  shift
done

source "$ROOTCOREBIN/../RootCoreMacros/retrieve_python_info.sh" \
	 || { echo "Couldn't load python information." && exit 1;}

# Local boost installation place:
BOOST_LOCAL_PATH_BSLASH="$INSTALL_AREA_BSLASH/boost"
BOOST_LOCAL_PATH=$(eval echo "$BOOST_LOCAL_PATH_BSLASH")

# The downloaded file to use as reference
boost_file="$DEP_AREA/boost.tgz"
# If not downloaded, try to get it from here:
boost_dl_file="/afs/cern.ch/user/w/wsfreund/public/misc/boost.tgz"
# Else, use this link:
boost_dl_site="http://sourceforge.net/projects/boost/files/boost/1.58.0/boost_1_58_0.tar.gz"

# These are the not expanded versions of boost include/library paths:
boost_include_ne="$BOOST_LOCAL_PATH_BSLASH/include"
boost_lib_ne="$BOOST_LOCAL_PATH_BSLASH/lib"
# And the normal versions of the paths
boost_include="$BOOST_LOCAL_PATH/include"
boost_lib="$BOOST_LOCAL_PATH/lib"

# Flags used during the setup-up. Do not change their default values.
DO_NOT_CHECK=0 # Whether to check local installation
LOCAL_BOOST_INSTALLED=0 # Whether boost was locally installed
INSTALL_LOCAL_BOOST=0 # Whether to install boost locally

boost_dir_libpath=$(dirname $(find $(echo -n $LD_LIBRARY_PATH | tr ":" " ") -maxdepth 1 -mindepth 1 -name "libboost*" -print 2> /dev/null| head -n 1))
boost_dir_incpath=$(dirname $(find $(echo -n $PATH | tr ":" " ") -maxdepth 1 -mindepth 1 -type d -name "boost" -print  2> /dev/null | head -n 1))

test ! -f "$CHECK_HEADER" && echo "Header \"$CHECK_HEADER\" for checking boost compilation does not exist." && exit 1;

# Check if we need to install boost locally or add it to environment path:
if test -f "$boost_include/boost/algorithm/string.hpp" \
    -a $HEADERS_ONLY -eq "1" -o -d "$boost_lib"; then
  echo "boost needed files already installed."
  LOCAL_BOOST_INSTALLED=1
  DO_NOT_CHECK=1
else
  if test "$DISABLE_RECHECK" -eq "0" -o \! -f "$CHECK_HEADER.o"
  then
    echo "checking boost instalation (this may take a while)..."
    # Check if --with-libraries= in --bootstrap-extra-args
    if test "${BOOTSTRAP_EXTRA_ARGS#*--with-libraries=*}" != "${BOOTSTRAP_EXTRA_ARGS}"
    then
      extra_args_libs="${BOOTSTRAP_EXTRA_ARGS#*--with-libraries=}"
      extra_args_libs="${extra_args_libs%--*},"
      OLD_IFS=$IFS; IFS=',';
      for lib in $extra_args_libs; do
        boost_needed_libs="$boost_needed_libs -lboost_$lib"
      done
      IFS=$OLD_IFS
      boost_needed_libs=$(echo $boost_needed_libs | sed -e 's/^[ \t]*//')
      echo "requested to check the following libraries: $boost_needed_libs"
    fi 

    test -n "$boost_dir_libpath" && extra_libpath=-L$boost_dir_libpath
    test -n "$boost_dir_incpath" && extra_incpath=-I$boost_dir_incpath

    if ! $CXX $CHECK_HEADER $extra_incpath $extra_libpath $boost_needed_libs $EXTRA_TEST_ARGS -o $CHECK_HEADER.o > /dev/null 2> /dev/null
    then
      INSTALL_LOCAL_BOOST=1
    else
      if test -n "$extra_libpath"; then
        old_field=$($ROOTCOREDIR/scripts/get_field.sh $MAKEFILE PACKAGE_LDFLAGS)
        if test "${old_field#*$extra_libpath}" = "$old_field"
        then
          $ROOTCOREDIR/scripts/set_field.sh $MAKEFILE PACKAGE_LDFLAGS "$old_field $extra_libpath"
        fi
      fi
      if test -n "$extra_incpath"; then
        old_field=$($ROOTCOREDIR/scripts/get_field.sh $MAKEFILE PACKAGE_CXXFLAGS)
        if test "${old_field#*$extra_incpath}" = "$old_field"
        then
          $ROOTCOREDIR/scripts/set_field.sh $MAKEFILE PACKAGE_CXXFLAGS "$old_field $extra_incpath"
        fi
        old_field=$($ROOTCOREDIR/scripts/get_field.sh $MAKEFILE PACKAGE_OBJFLAGS)
        if test "${old_field#*$extra_incpath}" = "$old_field"
        then
          $ROOTCOREDIR/scripts/set_field.sh $MAKEFILE PACKAGE_OBJFLAGS "$old_field $extra_incpath"
        fi
      fi
      echo "boost installed at file system" && return 0;
    fi
  else
    echo "skipping boost recheck."
  fi
fi

# Run boost installation
if test "$INSTALL_LOCAL_BOOST" -eq "1"; then
  if test \( \! -f "$boost_file" \) -o \( "$(md5sum -b $boost_file 2> /dev/null | cut -f1 -d ' ')" != "5a5d5614d9a07672e1ab2a250b5defc5" \) ; then
    if test "$RCM_GRID_ENV" -eq "1"; then
      echo "Boost sources are unavailable, cannot download it from grid." && exit 1;
    fi
    if test -f $boost_dl_file
    then
      if ! rsync -qrvhzPL -e "ssh -o StrictHostKeyChecking=no
                                  -o UserKnownHostsFile=/dev/null
                                  -o LogLevel=quiet" "$boost_dl_file" "$boost_file"
      then
        cp "$boost_dl_file" "$boost_file" \
          || { echo "Couldn't download boost from afs!" && exit 1; }
      fi
    else
      echo -n "downloading boost... "
      if ! wget -q -O "$boost_file" "$boost_dl_site"
      then
        echo "Couldn't download boost and there is no afs access to download it." && exit 1 
      fi
      echo "done!"
    fi
  fi
  boost_source_tmp_dir=$(mktemp -d)
	if test "$arch" = "macosx64"; then
		echo -n "extracting files..." && boost_folder=$(tar xfvz "$boost_file" -C $boost_source_tmp_dir 2>&1 ) \
																	&& echo " done!" \
				|| { echo "Couldn't extract files!" && exit 1; }
	else
		echo -n "extracting files..." && boost_folder=$(tar xfvz "$boost_file" --skip-old-files -C $boost_source_tmp_dir 2> /dev/null) \
																	&& echo " done!" \
				|| { echo "Couldn't extract files!" && exit 1; }
	fi
	test -z "$boost_folder" && { echo "Couldn't extract boost!" && return 2;}
  if test "$arch" = "macosx64"; then
    # FIXME Should use root-config to set toolset for every compilation?
    BOOTSTRAP_DARWIN_ARGS="--with-toolset=clang"
    B2_DARWIN_ARGS="toolset=clang"
    boost_folder=$(echo ${boost_folder} | sed "s#x # #" | tr '\n' ' ' | cut -f2 -d ' ')
    boost_folder=$boost_source_tmp_dir/${boost_folder%%\/*};
  else
    boost_folder=$(echo $boost_folder | cut -f1 -d ' ' )
    boost_folder=$boost_source_tmp_dir/${boost_folder%%\/*};
  fi
  if test $HEADERS_ONLY -eq "0"; then
		echo "installing boost..."
		echo "running boostrap..."
    cd $boost_folder
    if ./bootstrap.sh --prefix="$BOOST_LOCAL_PATH" $BOOTSTRAP_EXTRA_ARGS $BOOTSTRAP_DARWIN_ARGS > /dev/null
    then
      echo "finished setting bootstrap successfully."
    else
      echo "couldn't execute bootstrap.sh." && exit 1
    fi
		echo "compiling boost..."
		test -d $boost_include && b2_command="stage" || b2_command="install"
    if ./b2 $b2_command link=shared \
        --stagedir="$BOOST_LOCAL_PATH" --prefix="$BOOST_LOCAL_PATH" \
        $B2_EXTRA_ARGS $B2_DARWIN_ARGS -j$ROOTCORE_NCPUS \
        > /dev/null
    then
      echo "sucessfully compiled boost."
    else
      echo "couldn't compile boost." && exit 1
    fi
    cd - > /dev/null
  else
    test -d "$boost_include" || mkdir -p "$boost_include"
		echo -n "copying headers... " && cp -r "$boost_folder/boost" "$boost_include" && echo "done!"
  fi
  LOCAL_BOOST_INSTALLED=1
  rm -rf $boost_source_tmp_dir
fi

# Add local boost installation to environment file (if needed)
if test "$LOCAL_BOOST_INSTALLED" -eq "1"; then

  # Add boost libraries to path, when compiled:
  if test $HEADERS_ONLY -eq "0"; then
    old_field=$($ROOTCOREDIR/scripts/get_field.sh $MAKEFILE PACKAGE_LDFLAGS)
    if test "${old_field#*-L$boost_lib}" = "$old_field"
    then
      $ROOTCOREDIR/scripts/set_field.sh $MAKEFILE PACKAGE_LDFLAGS "$old_field -L$boost_lib" # -Wl,-rpath,otherpath
    else
      echo "no need to add boost_lib."
    fi
    add_to_env_file LD_LIBRARY_PATH $boost_lib_ne
    if test "$arch" = "macosx64"
    then
      echo "changing boost library install_names to absolute path:"
      for libfile in $(find $boost_lib  -maxdepth 1 -mindepth 1); do
        echo "  setting '$(basename $libfile)' install_name to: $libfile"
        install_name_tool $libfile -id $libfile
      done
      add_to_env_file DYLD_LIBRARY_PATH $boost_lib_ne
    fi
  fi

  old_field=$("$ROOTCOREDIR/scripts/get_field.sh" "$MAKEFILE" PACKAGE_OBJFLAGS)
  if test "${old_field#*$include_system_marker$boost_include_ne}" = "${old_field}"
  then
    if test $HEADERS_ONLY -eq "0"; then
      "$ROOTCOREDIR/scripts/set_field.sh" "$MAKEFILE" PACKAGE_OBJFLAGS "$old_field -L$boost_lib_ne $include_system_marker$boost_include_ne"  
		else
			"$ROOTCOREDIR/scripts/set_field.sh" "$MAKEFILE" PACKAGE_OBJFLAGS "$old_field $include_system_marker$boost_include_ne"
    fi
  fi

  add_to_env_file CPATH "$boost_include_ne"

  source "$NEW_ENV_FILE" || { echo "couldn't set environment" && exit 1; }

  # Final test:
  if test "$DO_NOT_CHECK" -ne 1; then
    echo -n "checking boost installation..." \
      && { $CXX $CHECK_HEADER -o $CHECK_HEADER.o -L$boost_lib $boost_needed_libs $EXTRA_TEST_ARGS \
         || { echo "\nboost couldn't be found!" && exit 1; } \
         && echo " sucessfully installed!"; }
  fi
fi
