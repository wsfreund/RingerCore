if test "$(python -c "from distutils import sysconfig; print sysconfig.get_config_var('CC').split(' ')[0].startswith('/afs/cern.ch/sw/lcg/contrib/gcc/')")" \
        = "True"; then
  gccBinPath=$(readlink -f $(dirname $(python -c "from distutils import sysconfig; print sysconfig.get_config_var('CC').split(' ')[0]")))
  gccLibPath=$(readlink -f "$gccBinPath/../lib/")
  gccLib64Path=$(readlink -f "$gccBinPath/../lib64/")
  add_to_env LD_LIBRARY_PATH "$gccLibPath"
  add_to_env LD_LIBRARY_PATH "$gccLib64Path"
fi

