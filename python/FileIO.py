import numpy as np
import cPickle
import gzip
import tarfile
import os

def save(o, filename, **kw):
  """
    Save an object to disk.
  """
  compress = kw.pop('compress', True)
  protocol = kw.pop('protocol', -1  )
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
      if len(filename) <= 5 or filename[-5:] != '.gzip':
        filename += '.gzip'
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
  if len(filename) > 4 and (filename[-4:] == '.npy' or \
      filename[-4:] == '.npz'):
    return np.load(filename)
  else:
    if decompress == 'auto':
      if ( len(filename) >= 4 and filename[-4:] == '.gzip' ):
        decompress = 'gzip'
      elif  ( len(filename) >= 6 and filename[-6:] == '.tar.gz' ) or \
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

