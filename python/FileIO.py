__all__ = ['save', 'load', 'expandFolders']

import numpy as np
import cPickle
import gzip
import tarfile
import tempfile
import os
import StringIO

def save(o, filename, **kw):
  """
    Save an object to disk.
  """
  compress = kw.pop( 'compress', True )
  protocol = kw.pop( 'protocol', -1   )
  if not isinstance(filename, str):
    raise("Filename must be a string!")
  filename = os.path.expandvars(filename)
  if type(protocol) is str:
    if protocol == "savez_compressed":
      if type(o) is dict:
        np.savez_compressed(filename, **o)
      else:
        if not isinstance(o, (list,tuple) ):
          o = (o,)
        np.savez_compressed(filename, *o)
    elif protocol == "savez":
      if type(o) is dict:
        np.savez(filename, **o)
      else:
        if not isinstance(o, (list,tuple) ):
          o = (o,)
        np.savez(filename, *o)
    elif protocol == "save":
      np.save(filename, o)
    else:
      raise ValueError("Unknown protocol '%s'" % protocol)
  elif type(protocol) is int:
    if not filename.endswith('.pic'):
      filename += '.pic'
    if compress:
      if not filename.endswith('.gz'):
        filename += '.gz'
      f = gzip.GzipFile(filename, 'wb')
    else:
      f = open(filename, 'w')
    cPickle.dump(o, f, protocol)
    f.close()
  return filename


def load(filename, decompress = 'auto', allowTmpFile = True, useHighLevelObj = False,
         useGenerator = False, tarMember = None):
  """
    Loads an object from disk.

    -> decompress: what protocol should be used to decompress the file.
    -> allowTmpFile: if to allow temporary files to improve loading speed.
    -> useHighLevelObj: automatic convert rawDicts to their python
       representation (not currently supported for numpy files.
    -> useGenerator: This option changes the behavior when loading a tarball
       file with multiple members. Instead returning a collection with all
       contents within the file, it will return a generator allowing each file
       to be read individually, thus reducing the amount of memory used in the
       process.
    -> tarMember: the tarMember in the tarfile to read. When not specified: read
    all.
  """
  filename = os.path.expandvars(filename)
  transformDataRawData = __TransformDataRawData( useHighLevelObj )
  if not os.path.isfile( os.path.expandvars( filename ) ):
    raise ValueError("Cannot reach file %s" % filename )
  if filename.endswith('.npy') or filename.endswith('.npz'):
    if useGenerator:
      return transformDataRawData( np.load(filename,mmap_mode='r') ), None
    else:
      return transformDataRawData( np.load(filename,mmap_mode='r') )
  else:
    if decompress == 'auto':
      if filename.endswith( '.gz' ) or filename.endswith( '.gzip' ):
        decompress = 'gzip'
      elif filename.endswith( '.tar.gz' ) or filename.endswith( '.tgz' ):
        decompress = 'tgz'
      elif filename.endswith( '.gz.tar' ) or filename.endswith( '.tar' ):
        decompress = 'tar'
      else:
        decompress = False
    if decompress == 'gzip':
      f = gzip.GzipFile(filename, 'rb')
    elif decompress in ('tgz','tar'):
      if decompress == 'tar':
        o = __load_tar(filename, 'r:', allowTmpFile, transformDataRawData, tarMember)
      else:
        o = __load_tar(filename, 'r:gz', allowTmpFile, transformDataRawData, tarMember)
      if not useGenerator:
        o = list(map(lambda x: x[0], o))
        if len(o) == 1: o = o[0]
      return o
    else:
      f = open(filename,'r')
    o = cPickle.load(f)
    f.close()
    if useGenerator:
      return transformDataRawData( o ), None
    else:
      return transformDataRawData( o )
# end of (if filename)
# end of (load) 


def __load_tar(filename, mode, allowTmpFile, transformDataRawData, tarMember):
  """
  Internal method for reading tarfiles
  """
  f = tarfile.open(filename, mode, ignore_zeros = True)
  if tarMember is None:
    memberList = f.getmembers()
  elif type(tarMember) is tarfile.TarInfo:
    memberList = [tarMember]
  else:
    raise TypeError("tarMember argument must be TarInfo or None.")
  for entry in memberList:
    if allowTmpFile:
      tmpFolderPath=tempfile.mkdtemp()
      f.extractall(path=tmpFolderPath, members=(entry,))
      with open(os.path.join(tmpFolderPath,entry.name)) as f_member:
        yield transformDataRawData( cPickle.load(f_member) ), entry
      import shutil
      shutil.rmtree(tmpFolderPath)
    else:
      fileobj = f.extractfile(entry)
      if entry.name.endswith( '.gz' ) or entry.name.endswith( '.gzip' ):
        fio = StringIO.StringIO(fileobj.read())
        fzip = gzip.GzipFile(fileobj=fio)
        yield transformDataRawData( cPickle.load(fzip) ), entry
      else:
        yield transformDataRawData( cPickle.load(fileobj) ), entry
  f.close()
# end of (load_tar)

class __TransformDataRawData( object ):
  """
  Transforms raw data if requested to use high level object
  """

  def __init__(self, useHighLevelObj = False):
    self.useHighLevelObj = useHighLevelObj

  def __call__(self, o):
    """
    Run transformation
    """
    if self.useHighLevelObj:
      from RingerCore.RawDictStreamable import retrieveRawDict
      from numpy.lib.npyio import NpzFile
      if type(o) is NpzFile:
        o = dict(o)
      o = retrieveRawDict( o )
    return o
 
def expandFolders( pathList, filters = None, logger = None, level = None):
  """
    Expand all folders to the contained files using the filters on pathList

    Input arguments:

    -> pathList: a list containing paths to files and folders;
    filters;
    -> filters: return a list for each filter with the files contained on the
    list matching the filter glob.
    -> logger: whether to print progress using logger;
    -> level: logging level to print messages with logger;
  """
  if not isinstance( pathList, (list,tuple,) ):
    pathList = [pathList]
  from glob import glob
  if filters is None:
    filters = ['*']
  if not( type( filters ) in (list,tuple,) ):
    filters = [ filters ]
  retList = [[] for idx in range(len(filters))]
  from RingerCore.util import progressbar
  for path in progressbar( pathList, len(pathList), 'Expanding folders: ', 60, 50,
                           True if logger is not None else False, logger = logger,
                           level = level):
    path = os.path.abspath( os.path.expandvars( path ) )
    if not os.path.exists( path ):
      raise ValueError("Cannot reach path '%s'" % path )
    if os.path.isdir(path):
      for idx, filt in enumerate(filters):
        cList = [ f for f in glob( os.path.join(path,filt) ) ]
        if cList: 
          retList[idx].extend(cList)
      folders = [ os.path.join(path,f) for f in os.listdir( path ) if os.path.isdir( os.path.join(path,f) ) ]
      if folders:
        recList = expandFolders( folders, filters )
        if len(filters) is 1:
          recList = [recList]
        for idx, l in enumerate(recList):
          retList[idx].extend(l)
    else:
      for idx, filt in enumerate(filters):
        if path in glob( os.path.join( os.path.dirname( path ) , filt ) ):
          retList[idx].append( path )
  if len(filters) is 1:
    retList = retList[0]
  return retList
