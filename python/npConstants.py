from RingerCore.util   import checkForUnusedVars, setDefaultKey
import numpy as np

class npConstants(object):
  """
  This class is used by dependent packages to armonize numpy flags. Currently
  it can be used obtain armonization in the following information:
    - fortran/c representation;
      o dtype: retrieves floating point string used on numpy
    - dimensions:
      o access: access numpy indexes
      o shape: return shape using npat and nobs
      o odim: retrieves the observations axis index
      o pdim: retrieves the patterns axis index
    - floating point data type:
      o fp_dtype: retrieves floating point dtype used on numpy
    - integer data types:
      o int_dtype: common integer dtype
      o scounter_dtype: short integer dtype to use as counter
      o flag_dtype: the integer to use on flags (usually only -1,0,1 are
      flagged)
  """

  def __init__(self, **kw):
    self.__useFortran = kw.pop( 'useFortran', True )
    self.order          = 'F' if self.__useFortran else 'C'
    self.pdim           = 0   if self.__useFortran else 1
    self.odim           = 1   if self.__useFortran else 0
    self.fp_dtype       = np.dtype( kw.pop( 'fp_dtype',       np.double ) )
    self.int_dtype      = np.dtype( kw.pop( 'int_dtype',      np.int64  ) )
    self.scounter_dtype = np.dtype( kw.pop( 'scounter_dtype', np.uint8  ) )
    self.flag_dtype     = np.dtype( kw.pop( 'flag_dtype',     np.int8   ) )
    checkForUnusedVars(kw)
  # __init__

  @property
  def dtype(self):
    "Redirect dtype to floating point type."
    return self.fp_type

  @property
  def fdim(self):
    "Redirect feature dimension to pattern."
    return self.pdim

  @property
  def isfortran(self):
    "Return if indexes are order in fortran representation."
    return self.__useFortran

  def access(self, **kw):
    """
    Access numpy indexes informing pattern and observation index through keywords dict:
      - pidx|fidx;
      - oidx;
    respectively. 

    You can use the char ':' to expand the full dimension. This is the same as
    using slice(None).
    """
    if set(("pidx","fidx")) <= set(kw.keys()):
      raise KeyError('Cannot use both pidx and fidx keywords')
    pidx = kw.pop('pidx', slice(None))
    if pidx is None: pidx = kw.pop('fidx', None)
    oidx = kw.pop('oidx', slice(None))
    if pidx == ':': pidx = slice(None)
    if oidx == ':': oidx = slice(None)
    if type(pidx) == tuple:
      pidx = slice(*pidx)
    if type(oidx) == tuple:
      oidx = slice(*oidx)
    if self.__useFortran:
      return pidx, oidx
    else:
      return oidx, pidx
  # access

  def shape(self, **kw):
    """
    Return shape using total number of observations and patterns.
    Retuned shape will always be a matrix.
    """
    if set(("npat","nfeat")) <= set(kw.keys()):
      raise KeyError('Cannot use both pidx and fidx keywords')
    npat = kw.pop('npat', None)
    if npat is None: npat = kw.pop('nfeat', None)
    nobs = kw.pop('nobs', None)
    if npat is None:
      npat = 1
    if nobs is None:
      nobs = 1
    if self.__useFortran:
      return (npat, nobs)
    else:
      return (nobs, npat)
  # shape

  def array(self, obj, **kw):
    """
    Shortcut for this default floating point array, but type can be changed.
    """
    setDefaultKey( kw, 'dtype', self.fp_dtype )
    setDefaultKey( kw, 'order', self.order )
    return np.array( obj, **kw )

  def fp_array(self, obj, **kw):
    """
    Shortcut for default numpy array method using this numpy floating point dtype and order
    """
    kw['dtype'] = self.fp_dtype
    setDefaultKey( kw, 'order', self.order )
    return np.array( obj, **kw )

  def int_array(self, obj, **kw):
    """
    Shortcut for default numpy array method using this numpy integer dtype and order
    """
    kw['dtype'] = self.int_dtype
    setDefaultKey( kw, 'order', self.order )
    return np.array( obj, **kw )

  def scounter_array(self, obj, **kw):
    """
    Shortcut for default numpy array method using this numpy short counter dtype and order
    """
    kw['dtype'] = self.scounter_dtype
    setDefaultKey( kw, 'order', self.order )
    return np.array( obj, **kw )

  def flag_array(self, obj, **kw):
    """
    Shortcut for default numpy array method using this numpy flag dtype and order
    """
    kw['dtype'] = self.flag_dtype
    setDefaultKey( kw, 'order', self.order )
    return np.array( obj, **kw )

  def zeros(self, shape, **kw):
    """
    Shortcut for default numpy zeros method using this numpy floating point dtype and order.
    dtype can be changed.
    """
    setDefaultKey( kw, 'dtype', self.fp_dtype )
    setDefaultKey( kw, 'order', self.order )
    return np.zeros( obj, **kw )

  def fp_zeros(self, shape, **kw):
    """
    Shortcut for default numpy zeros method using this numpy floating point and dtype and order
    """
    kw['dtype'] = self.fp_dtype
    setDefaultKey( kw, 'order', self.order )
    return np.zeros( obj, **kw )

  def int_zeros(self, shape, **kw):
    """
    Shortcut for default numpy zeros method using this numpy integer dtype and order
    """
    kw['dtype'] = self.int_dtype
    setDefaultKey( kw, 'order', self.order )
    return np.zeros( obj, **kw )

  def scounter_zeros(self, shape, **kw):
    """
    Shortcut for default numpy zeros method using this numpy short counter dtype and order
    """
    kw['dtype'] = self.scounter_dtype
    setDefaultKey( kw, 'order', self.order )
    return np.zeros( obj, **kw )

  def flag_zeros(self, shape, **kw):
    """
    Shortcut for default numpy zeros method using this numpy flag dtype and order
    """
    kw['dtype'] = self.flag_dtype
    setDefaultKey( kw, 'order', self.order )
    return np.zeros( obj, **kw )

  def ones(self, shape, **kw):
    """
    Shortcut for default numpy ones method using this numpy floating point dtype and order.
    dtype can be changed.
    """
    setDefaultKey( kw, 'dtype', self.fp_dtype )
    setDefaultKey( kw, 'order', self.order )
    return np.ones( obj, **kw )

  def fp_ones(self, shape, **kw):
    """
    Shortcut for default numpy ones method using this numpy floating point and dtype and order
    """
    kw['dtype'] = self.fp_dtype
    setDefaultKey( kw, 'order', self.order )
    return np.ones( obj, **kw )

  def int_ones(self, shape, **kw):
    """
    Shortcut for default numpy ones method using this numpy integer dtype and order
    """
    kw['dtype'] = self.int_dtype
    setDefaultKey( kw, 'order', self.order )
    return np.ones( obj, **kw )

  def scounter_ones(self, shape, **kw):
    """
    Shortcut for default numpy ones method using this numpy short counter dtype and order
    """
    kw['dtype'] = self.scounter_dtype
    setDefaultKey( kw, 'order', self.order )
    return np.ones( obj, **kw )

  def flag_ones(self, shape, **kw):
    """
    Shortcut for default numpy ones method using this numpy flag dtype and order
    """
    kw['dtype'] = self.flag_dtype
    setDefaultKey( kw, 'order', self.order )
    return np.ones( obj, **kw )

  def __repr__(self):
    return 'npConstants(fp_dtype=%r,int_dtype=%r,scounter_dtype=%r,flag_dtype=%r,order=%s)' % \
      (self.fp_dtype, self.int_dtype, self.scounter_dtype, self.flag_dtype, self.order)
