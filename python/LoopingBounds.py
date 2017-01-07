__all__ = ['LoopingBounds', 'MatlabLoopingBounds', 'PythonLoopingBounds',
           'transformToMatlabBounds', 'transformToPythonBounds',
           'transformToSeqBounds', 'LoopingBoundsCollection',
           'MatlabLoopingBoundsCollection', 'PythonLoopingBoundsCollection',
           'SetDepth', 'traverse']

import numpy as np
from RingerCore.Logger import Logger

class SetDepth(Exception):
  def __init__(self, value):
    self.depth = value

def traverse(o, tree_types=(list, tuple),
    max_depth_dist=0, max_depth=np.iinfo(np.uint64).max, 
    level=0, idx=0, parent=None,
    simple_ret=False):
  """
  Loop over each holden element. 
  Can also be used to change the holden values, e.g.:

  a = [[[1,2,3],[2,3],[3,4,5,6]],[[[4,7],[]],[6]],7]
  for obj, idx, parent in traverse(a): parent[idx] = 3
  [[[3, 3, 3], [3, 3], [3, 3, 3, 3]], [[[3, 3], []], [3]], 3]

  Examples printing using max_depth_dist:

  In [0]: for obj in traverse(a,(list, tuple),0,simple_ret=False): print obj
  (1, 0, [1, 2, 3], 0, 3)
  (2, 1, [1, 2, 3], 0, 3)
  (3, 2, [1, 2, 3], 0, 3)
  (2, 0, [2, 3], 0, 3)
  (3, 1, [2, 3], 0, 3)
  (3, 0, [3, 4, 5, 6], 0, 3)
  (4, 1, [3, 4, 5, 6], 0, 3)
  (5, 2, [3, 4, 5, 6], 0, 3)
  (6, 3, [3, 4, 5, 6], 0, 3)
  (4, 0, [4, 7], 0, 4)
  (7, 1, [4, 7], 0, 4)
  (6, 0, [6], 0, 3)
  (7, 2, [[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 0, 1) 

  In [1]: for obj in traverse(a,(list, tuple),1): print obj
  ([1, 2, 3], 0, [[1, 2, 3], [2, 3], [3, 4, 5, 6]], 1, 3)
  ([2, 3], 0, [[1, 2, 3], [2, 3], [3, 4, 5, 6]], 1, 3)
  ([3, 4, 5, 6], 0, [[1, 2, 3], [2, 3], [3, 4, 5, 6]], 1, 3)
  ([4, 7], 0, [[4, 7], []], 1, 4)
  ([6], 0, [[[4, 7], []], [6]], 1, 3)
  ([[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 2, None, 1, 1)

  In [2]: for obj in traverse(a,(list, tuple),2,simple_ret=False): print obj
  ([[1, 2, 3], [2, 3], [3, 4, 5, 6]], 0, [[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 2, 2)
  ([[4, 7], []], 0, [[[4, 7], []], [6]], 2, 3)
  ([[[4, 7], []], [6]], 1, [[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 2, 2)

  In [3]: for obj in traverse(a,(list, tuple),3): print obj
  ([[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 0, None, 3, 1)

  In [4]: for obj in traverse(a,(list, tuple),4): print obj
  ([[[1, 2, 3], [2, 3], [3, 4, 5, 6]], [[[4, 7], []], [6]], 7], 1, None, 4, 1)

  In [5]: for obj in traverse(a,(list, tuple),5): print obj
  <NO OUTPUT>

  """
  if isinstance(o, tree_types):
    level += 1
    # FIXME Still need to test max_depth
    if level > max_depth:
      if simple_ret:
        yield o
      else:
        yield o, idx, parent, 0, level
      return
    skipped = False
    isDict = isinstance(o, dict)
    if isDict:
      loopingObj = o.iteritems()
    else:
      loopingObj = enumerate(o)
    for idx, value in loopingObj:
      try:
        for subvalue, subidx, subparent, subdepth_dist, sublevel in traverse(value, tree_types, max_depth_dist, max_depth, level, idx, o ):
          if subdepth_dist == max_depth_dist:
            if skipped:
              subdepth_dist += 1
              break
            else:
              if simple_ret:
                yield subvalue
              else:
                yield subvalue, subidx, subparent, subdepth_dist, sublevel 
          else:
            subdepth_dist += 1
            break
        else: 
          continue
      except SetDepth, e:
        if simple_ret:
          yield o
        else:
          yield o, idx, parent, e.depth, level
        break
      if subdepth_dist == max_depth_dist:
        if skipped:
          subdepth_dist += 1
          break
        else:
          if simple_ret:
            yield o
          else:
            yield o, idx, parent, subdepth_dist, level
          break
      else:
        if level > (max_depth_dist - subdepth_dist):
          raise SetDepth(subdepth_dist+1)
  else:
    if simple_ret:
      yield o
    else:
      yield o, idx, parent, 0, level

class LoopingBounds ( Logger ):
  """
    Create looping bounds using Matlab/(unix seq command) format
          firstBound:incr:lastBound
    where:
      - firstBound [default 1 if matlabFlag else 0]: always close bounded
        value where looping will start;
      - incr [default]: the increment to firstBound which will add looping
        instances until lastBound is reached;
      - lastBound: the bound for until when it should increment firstBound.
        If set matlab flag, then it will a closed bound, otherwise opened.
        I.e, if lastBound is 10, when matlab flag is set to false, it will 
        loop on [0,9] or [0,10) otherwise on [1,10] or [1,11).
  """

  _matlabFlag = False
  _vec = []

  def __init__(self, *args, **kw):
    """
      Set values using min:incr:max and matlabFlag as explained in class
      documentation.
    """
    from RingerCore.util import checkForUnusedVars
    Logger.__init__(self, kw)
    self._matlabFlag = kw.pop('matlabFlag', False )
    checkForUnusedVars( kw, self._logger.warning )
    del kw

    if len(args) > 3: 
      raise ValueError("Input more than 3 values, format should be [min=0:[incr=1:]]max")

    if len(args) == 0: 
      raise ValueError("No input. Format should be [min=0,[incr=1,]]max")

    if isinstance(args[0], LoopingBounds ):
      self._vec = args[0]._vec
      oldFlag = self._matlabFlag
      self._matlabFlag = args[0]._matlabFlag
      if oldFlag != self._matlabFlag:
        if self._matlabFlag:
          self.turnMatlabFlagOn()
        else:
          self.turnMatlabFlagOff()
      return
    elif isinstance(args[0], list ):
      self._vec = args[0]
    else:
      self._vec = list(args)

    if len(self._vec) == 1:
      self._vec.append( self._vec[0] + 1 )
      if not self._matlabFlag:
        self._vec[1] -= 1
      self._vec[0] = 1 if self._matlabFlag else 0
    elif len(self._vec) == 2:
      if self._matlabFlag: 
        self._vec[1] += 1
    else:
      tmp = self._vec[1]
      if self._matlabFlag:
        if tmp > 0:
          self._vec[1] = self._vec[2] + 1
        else:
          self._vec[1] = self._vec[2] - 1
      else:
        self._vec[1] = self._vec[2]
      self._vec[2] = tmp

    if len(self._vec) == 3 and self._vec[2] == 0:
      raise ValueError("Attempted to create looping bounds without increment.")

  @property
  def matlabFlag(self):
    return self._matlabFlag

  def range(self):
    """
      Returns range generator
    """
    for x in range(*self._vec):
      yield x

  def window(self, n):
    """
    Returns a divided window (of width n) over data from the sequence
    s -> (s0,s1,...s[n-1]), (s[n],s[n+1],...,s[2n-1]), ...
    """
    l = self.list()
    for i in xrange(0, len(l), n):
      yield l[i:i+n]

  def __call__(self):
    """
      Returns range generator
    """
    return self.range()

  def list(self):
    """
      Returns list with index range
    """
    return range(*self._vec)

  def incr(self):
    """
      Return increment value
    """
    return self._vec[2] if len(self._vec) == 3 else 1

  def lowerBound(self, openBounded = False):
    """
      Returns lower bound. If openBounded flag is set to true, return the open
      bounded limit.
    """
    l = self.list()
    if not l:
      return None
    increment = 0
    if openBounded:
      increment = -1
    if self.incr() > 0:
      tmp = l[0]
    else:
      tmp = l[-1]
    return tmp + increment

  def upperBound(self, openBounded = False):
    """
      Return upper bound. If openBounded flag is set to true, return the open
      bounded limit.
    """
    l = self.list()
    if not l:
      return None
    increment = 0
    if openBounded:
      increment = 1
    if self.incr() > 0:
      tmp = l[-1]
    else:
      tmp = l[0]
    return tmp + increment

  def startBound(self, openBounded = False):
    """
      Return first entered bound. If openBounded flag is set to true, return
      the open bounded limit.
    """
    l = self.list()
    if not l:
      return None
    deslocate = 0
    if openBounded:
      deslocate = -1 if self.incr() > 0 else +1
    return l[0] + deslocate

  def endBound(self, openBounded = False):
    """
      Return last entered bound. If openBounded flag is set to true, return
      the open bounded limit.
    """
    l = self.list()
    if not l:
      return None
    deslocate = 0
    if openBounded:
      deslocate = 1 if self.incr() > 0 else -1
    return l[-1] + deslocate

  def __getitem__(self, k):
    """
      Overload []
    """
    return self._vec[k]

  def getOriginalVec(self):
    """
      Get original _vec used at the ctor
    """
    tmp = self._vec[:] # copy list
    if len(self._vec) == 3:
      if self._matlabFlag:
        if self._vec[2] > 0:
          tmp[2] = self._vec[1] - 1
        else:
          tmp[2] = self._vec[1] + 1
      else:
        tmp[2] = self._vec[1]
      tmp[1] = self._vec[2]
      if tmp[1] == 1:
        tmp.pop(1)
    else:
      if self._matlabFlag:
        tmp[1] -= 1
        if tmp[0] == 1:
          tmp[0] = tmp.pop()
      else:
        if tmp[0] == 0:
          tmp[0] = tmp.pop()
    return tmp

  def turnMatlabFlagOn(self):
    """
      Set object matlab flag to on
    """
    if not self._matlabFlag:
      self._vec = LoopingBounds( self.getOriginalVec(), matlabFlag = True )._vec
      self._matlabFlag = True

  def turnMatlabFlagOff(self):
    """
      Set object matlab flag to off
    """
    if self._matlabFlag:
      self._vec = LoopingBounds( self.getOriginalVec(), matlabFlag = False )._vec
      self._matlabFlag = False

  def __str__(self):
    """
      String representation of the object
    """
    lb = self.lowerBound()
    ub = self.upperBound()
    nfill = self.get_minNFill( ub, 4 )
    if lb != ub:
      return 'l%s.u%s' % ( str(lb).zfill(nfill), str(ub).zfill(nfill) )
    else:
      return 'i%s' % str(lb).zfill(nfill)

  def formattedString(self, s = '', nfill = None):
    """
      String representation of the object
    """
    # TODO Make work with negative index
    lb = self.lowerBound()
    ub = self.upperBound()
    if nfill is None:
      nfill = self.get_minNFill( 4 )
    else:
      nfill = int( nfill )
    if lb != ub:
      return '%sl%s.%su%s' % ( s, str(lb).zfill(nfill), s, str(ub).zfill(nfill)  )
    else:
      return '%s%s' % (s, str(lb).zfill(nfill) )

  def get_minNFill( self, minN = 0 ):
    """
      Return minimum number of filling chars to make sure that all numbers on
      this looping bounds have the number of chars.
    """
    ub = self.upperBound()
    from RingerCore.util import scale10
    nfill = scale10(ub)
    if nfill < minN:
      nfill = minN
    return int(nfill)

  def __len__(self):
    """
      Retrieve total looping range.
    """
    # FIXME This could be improved for performance, if needed
    return len(self.list())


from RingerCore.LimitedTypeList import LimitedTypeList
LoopingBoundsCollection = LimitedTypeList("LoopingBoundsCollection", (), \
    {'_acceptedTypes' : (LoopingBounds,)})

class PythonLoopingBounds (LoopingBounds):
  """
    As LoopingBounds, but sets matlab flag to false
  """
  def __init__(self, *args):
    """
      Set this generator min:incr:max.
    """
    LoopingBounds.__init__(self, *args, matlabFlag = False)
    self.turnMatlabFlagOff()

  def toMatlabLoopingBounds(self):
    """
      Return python loopingBounds as it would be written using Matlab notation
    """
    return MatlabLoopingBounds(self.getOriginalVec())

  def toSeqLoopingBounds(self):
    return SeqLoopingBounds(self.getOriginalVec())

  def turnMatlabFlagOn(self):
    """
      Cannot call turn matlab flags off on PythonLoopingBounds.
    """
    raise RuntimeError("Can only set matlab flag to on for LoopingBounds objects.")

def transformToPythonBounds( bounds ):
  """
   Return an equal representation of the bounds, but as an instance of PythonLoopingBounds
  """
  if isinstance( bounds, PythonLoopingBounds ):
    return bounds
  else:
    originalVec = bounds.getOriginalVec()
    if not bounds.matlabFlag:
      return PythonLoopingBounds( originalVec )
    else:
      if len(originalVec) is 1:
        originalVec=[1, originalVec[0]+1]
      elif len(originalVec) is 3 and originalVec[1] < 0:
        originalVec[-1] -= 1
      else:
        originalVec[-1] += 1
      return PythonLoopingBounds( originalVec )

PythonLoopingBoundsCollection = LimitedTypeList( \
    "PythonLoopingBoundsCollection", (), \
    {'_acceptedTypes' : (PythonLoopingBounds,)})

class MatlabLoopingBounds (LoopingBounds):
  """
    As LoopingBounds, but sets matlab flag to true
  """
  def __init__(self, *args):
    """
      Set this generator min:incr:max.
    """
    LoopingBounds.__init__(self, *args, matlabFlag = True)

  def toPythonLoopingBounds(self):
    """
      Return python loopingBounds as it would be written using Matlab notation
    """
    return PythonLoopingBounds(self.getOriginalVec())

  def turnMatlabFlagOff(self):
    """
      Cannot call turn matlab flags off on MatlabLoopingBounds.
    """
    raise RuntimeError("Can only set matlab flag to off for LoopingBounds objects.")

def transformToMatlabBounds( bounds ):
  """
  Return an equal representation of the bounds, but as an instance of MatlabLoopingBounds 
  """
  if isinstance( bounds, MatlabLoopingBounds ):
    return bounds
  else:
    originalVec = bounds.getOriginalVec()
    if bounds.matlabFlag:
      return MatlabLoopingBounds( originalVec )
    else:
      if len(originalVec) is 1:
        originalVec=[0, originalVec[0]-1]
      elif len(originalVec) is 3 and originalVec[1] < 0:
        originalVec[-1] += 1
      else:
        originalVec[-1] -= 1
      return MatlabLoopingBounds( originalVec )

MatlabLoopingBoundsCollection = LimitedTypeList( \
    "MatlabLoopingBoundsCollection", (), \
    {'_acceptedTypes' : (PythonLoopingBounds,)})


# Simply redirect SeqLoopingBounds to MatlabLoopingBounds
SeqLoopingBounds = MatlabLoopingBounds
SeqLoopingBoundsCollection = MatlabLoopingBoundsCollection
transformToSeqBounds = transformToMatlabBounds



