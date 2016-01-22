import numpy as np
import cPickle
import gzip
import tarfile
import os
import StringIO

def save(o, filename, **kw):
  """
    Save an object to disk.
  """
  compress = kw.pop('compress', True)
  protocol = kw.pop('protocol', -1  )
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
    if len(filename) <= 4 or filename[-4:] != '.pic':
      filename += '.pic'
    if compress:
      if len(filename) <= 3 or filename[-3:] != '.gz':
        filename += '.gz'
      f = gzip.GzipFile(filename, 'wb')
    else:
      f = open(filename, 'w')
    cPickle.dump(o, f, protocol)
    f.close()
  return filename

def load(filename, decompress = 'auto'):
  """
    Loads an object from disk
  """
  filename = os.path.expandvars(filename)
  if not os.path.isfile( os.path.expandvars( filename ) ):
    raise ValueError("Cannot reach file %s" % filename )
  if len(filename) > 4 and (filename[-4:] == '.npy' or \
      filename[-4:] == '.npz'):
    return np.load(filename,mmap_mode='r')
  else:
    if decompress == 'auto':
      if ( len(filename) >= 3 and filename[-3:] == '.gz' ) or \
          ( len(filename) >= 5 and filename[-5:] == '.gzip' ):
        decompress = 'gzip'
      elif  ( len(filename) >= 7 and filename[-7:] == '.tar.gz' ) or \
            ( len(filename) >= 4 and filename[-4:] == '.tgz' ):
        decompress = 'tgz'
      else:
        decompress = False
    if decompress == 'gzip':
      f = gzip.GzipFile(filename, 'rb')
    elif decompress == 'tgz':
      f = tarfile.open(filename, 'r:gz')
      o = []
      for entry in f.getmembers():
        fileobj = f.extractfile(entry)
        if  ( len(entry.name) >= 3 and entry.name[-3:] == '.gz' ) or \
            ( len(entry.name) >= 5 and entry.name[-5:] == '.gzip' ):
          fio = StringIO.StringIO(fileobj.read())
          fzip = gzip.GzipFile(fileobj=fio)
          o.append( cPickle.load(fzip) )
        else:
          o.append( cPickle.load(fileobj) )
      f.close()
      if len(o) == 1:
        return o[0]
      else:
        return o
    else:
      f = open(filename,'r')
    o = cPickle.load(f)
    f.close()
    return o


def expandFolders( pathList ):
  """
    Retrieve all files on the folders on pathList
  """
  # FIXME debug this the ensure correctness when using multiplie folders
  if not isinstance( pathList, list ):
    pathList = [pathList]
  retList = []
  
  for path in pathList:
    if not os.path.exists( os.path.expandvars( path ) ):
      raise ValueError("Cannot reach path %s" % path )
    if os.path.isdir(path):
      localList = [ os.path.join(path,f) for f in os.listdir(path) \
        if os.path.isfile(os.path.join(path,f)) ]
      retList.extend( expandFolders( localList ) )
    else:
      retList.append( path )
  return retList

