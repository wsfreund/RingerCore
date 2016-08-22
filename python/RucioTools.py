__all__ = ['RucioTools']

from RingerCore import Logger


class RucioTools( Logger ):

  def __init__(self):
    Logger.__init__(self)

  # Get all files name for the dataset (ds) passed
  def get_list_files( self, ds ):
    import os
    self._logger.info(('Getting list of files in %s')%(ds))
    command = ('rucio list-files %s | cut -f2 -d  "|" >& rucio_list_files.txt') % (ds) 
    os.system(command)
    files = list()
    with open('rucio_list_files.txt') as f:
      lines = f.readlines()
      for line in lines:  
        # remove skip line
        line = line.replace('\n','')
        # remove spaces
        for s in line:  
          if ' ' in line:  line = line.replace(' ','')
        # remove corrupt files
        if line.endswith('.2'):  
          self._logger.warning(('Remove corrupt file: %s')%(line))
          continue
        files.append( line )
      # remove junk lines
      files.pop(0);  files.pop(-1)
      files.pop(0);  files.pop(-1)
      files.pop(0);  files.pop(-1)
      files.sort()

    return files

  # Download file using rucio
  def download( self, f):
    import os
    self._logger.info(('Download file %s')%(f))
    command = ('rucio download %s --no-subdir') % (f) 
    os.system( command )
    self._logger.info('Download completed.')

  # remove "user.youloggin:" from the name
  def noUsername(self, f):
    return f.split(':')[1]


