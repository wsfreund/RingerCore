__all__ = ['RucioTools', 'extract_scope']

from RingerCore import Logger

def extract_scope(did):
  """
  Taken from rucio client v1.13.2 itself
  """
  # Try to extract the scope from the DSN
  if did.find(':') > -1:
    if len(did.split(':')) > 2:
      raise RuntimeError('Too many colons. Cannot extract scope and name')
    scope, name = did.split(':')[0], did.split(':')[1]
    if name.endswith('/'):
      name = name[:-1]
    return scope, name
  else:
    scope = did.split('.')[0]
    if did.startswith('user') or did.startswith('group'):
      scope = ".".join(did.split('.')[0:2])
    if did.endswith('/'):
      did = did[:-1]
    return scope, did

#Rucio Class
class RucioTools( Logger ):

  def __init__(self):
    Logger.__init__(self)
    try:# Check if rucio was set
      import os
      os.system('rucio --version')
    except RuntimeError:
      self._fatal('Rucio was not set! please setup this!')
      raise RuntimeError('Rucio command not found!')

  # Get all files name for the dataset (ds) passed
  def get_list_files( self, ds ):
    import os
    self._info(('Getting list of files in %s')%(ds))
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
          self._warning(('Remove corrupt file: %s')%(line))
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
    self._info(('Download file %s')%(f))
    command = ('rucio download %s --no-subdir') % (f) 
    os.system( command )
    self._info('Download completed.')

  # remove "user.youloggin:" from the name
  def noUsername(self, f):
    return f.split(':')[1]


