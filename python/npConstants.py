class npConstants:
  """
  This class is used by dependent packages to armonize numpy flags. Currently
  it can be used obtain armonization in the following information:
    - fortran/c representation;
      o dtype: retrieves floating point string used on numpy
    - dimensions:
      o access: access numpy indexes
      o odim: retrieves the observations axis index
      o pdim: retrieves the patterns axis index
    - floating point data type:
      o dtype: retrieves floating point string used on numpy
  """

  _useFortran = True

  def __init__(self, **kw):
    self.__useFortran = kw.pop( 'useFortran', True )
    self.order     = 'F' if self.__useFortran else 'C'
    self.pdim      = 0 if _useFortran else 1
    self.odim      = 1 if _useFortran else 0
    import numpy as np
    self.fp_dtype  = kw.pop( 'fp_dtype', np.double )
    self.int_dtype = kw.pop( 'int_dtype', np.double )
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
    if set(("pidx","fidx")) <= kw.keys():
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

