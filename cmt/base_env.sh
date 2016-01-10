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

DEP_AREA=$ROOTCOREBIN/../Downloads; DEP_AREA_BSLASH=\$ROOTCOREBIN/../Downloads
INSTALL_AREA=$ROOTCOREBIN/../InstallArea; INSTALL_AREA_BSLASH=\$ROOTCOREBIN/../InstallArea

# Make sure the folders exist
test \! -d $DEP_AREA && mkdir -p $DEP_AREA
test \! -d $INSTALL_AREA && mkdir -p $INSTALL_AREA

source $ROOTCOREBIN/../RingerCore/cmt/common_shell_fcns.sh
