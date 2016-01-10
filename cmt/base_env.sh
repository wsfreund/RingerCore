MAKEFILE=$PWD/Makefile.RootCore

NEW_ENV_FILE=$PWD/new_env_file.sh

echo -n > $NEW_ENV_FILE
chmod +x $NEW_ENV_FILE

arch=`root-config --arch`
if test "$arch" = "macosx64"
then
  include_marker="-I"
  include_system_marker="-isystem"
else
  include_marker="-I"
  include_system_marker="-isystem"
fi

source $ROOTCOREBIN/../RingerCore/cmt/common_shell_fcns.sh
