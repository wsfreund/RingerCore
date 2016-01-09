find_lib()
{
  array=$(echo $LD_LIBRARY_PATH | tr ':' ' ' )                        
  OLD_IFS=$IFS; export IFS=' ';
  for place in $array; do
    if test -n "$(find $p -mindepth 1 -maxdepth 1 -name "$1*")"; then
      export IFS=$OLD_IFS
      echo "${place}"
      return 0;
    fi
  done
  export IFS=$OLD_IFS
  return 1;
}

add_to_env_file()
{
  var=$1
  add_path=$2
  echo "test \$(echo \":\$$var:\" | grep -q \":$add_path:\"; echo \$?) -ne 0 && export $var=$add_path:\$$var || true" >> $NEW_ENV_FILE
}
