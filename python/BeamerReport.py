
__all__ = ['BeamerConfig', 'BeamerTexReport', 'PdfReport']

import textwrap as _textwrap

def formatTex( text ):
  """
  Strip initial and final '\n' if available and dedent text.
  """
  return _textwrap.dedent( text.lstrip('\n').rstrip('\n') )

class TexException(Exception):
  """
    Exception thrown by specific errors during this module execution
  """
  pass

class TexObject( object ):
  """
  TexObject inherited class will convert the object to a string containing the
  tex code by using the skeleton template and its configured attributes.
  """

  def __init__( self ):
    if not 'skeleton' in self.__dict__:
      raise AttributeError('Cannot create a TexObject without skeleton attribute')
    self.skeleton = formatTex( self.skeleton )

  def __str__( self ):
    try:
      return self.skeleton % self.__dict__
    except KeyError, e:
      raise TexException("Couldn't format %s tex code due to: %s." % (self.__class__, e) )

from RingerCore.LimitedTypeList import LimitedTypeList

class TexItemCollection( TexObject ):
  """
  Base class for tex item collections.
  """
  __metaclass__ = LimitedTypeList
  _acceptedTypes = type(None), # This will be filled after TexItemCollection is defined
TexItemCollection._acceptedTypes = basestring, TexItemCollection

class TexEnum( TexItemCollection ):
  """
  Tex enumeration object 
  """

  def __init__( self ):
    self.skeleton = kw.pop( 'skeleton',  )

  def addItem( self, item ):
    self.items.append( item )

class TexPackage( TexObject ):
  """
    Defines a tex package to be included
  """
  __skeleton = formatTex(
r"""
\usepackage%(config)s{%(package)s}
""")

  def config(self):
    # Add '+' only if necessary
    return self.args.join(',') 

class PDFTexLayout( TexPackage ):

  __layout = formatTex(
r"""\pgfpagesuselayout{resize to}[
  physical paper width=8in, physical paper height=6in]
""")

  def __init__( self ):
    self.package = 'pgfpages'

class TexSlide( TexObject ):
  """
  The most basic object to be created by the beamer submodule. slide object
  """

  def __init__( self, text, options ):
    self.title = kw.pop( 'title', '')
    self.body = ''
    self.skeleton = kw.pop( 'skeleton', r'''\begin{frame}{%{title}s}
                                              %{body}s
                                            \end{frame}
                                         '''
                          )

   def addEnum( self, items ):

class SlidesFactory( Logger ):
  """
    Contains several slide templates to be used.
  """

  def __init__( self ):
    pass

  # TODO Add all default slide types

class BeamerConfig( object ):
  """
    Beamer configuration object
  """

  def __init__(self, **kw):
    # Pre-ample configuration
    self.theme = retrieve_kw( kw, 'theme' , 'Madrid'  )
    self.color = retrieve_kw( kw, 'color' , 'default' )
    self.font  = retrieve_kw( kw, 'font'  , 'serif'   )
    # 
    self.title = kw.pop('title', 'Report')
    self.institute = kw.pop('institute', 'COPPE/UFRJ')

    
class BeamerTexReport( Logger ):
  """
  A BeamerTexReport object can be used to generate templated slides 
  containing plots, tables etc.

  It must be used as a context manager, that is:

  with BeamerTexReport( BeamerConfig( theme = 'YourTheme', ...) ) as btr:
    btr.fullFigureSlide( figurePath )
    ...

  Check the available methods dedicated for 
  """
  __metaclass__ = LimitedTypeList
  _acceptedTypes = TexSlide, TexSession

  def __init__(self, fname, beamerConfig, **kw):
    from RingerCore import checkForUnusedVars, GRID_ENV 
    self.name = ensureExtension(fname, '.tex')
    self.ignoreErrors = retrieve_kw( kw, 'ignoreErrors', False if not GRID_ENV else True )
    Logger.__init__(self,kw)
    checkForUnusedVars( kw, self._logger.warning )

    import socket
    self._machine = socket.gethostname()
    import getpass
    self._author = getpass.getuser()

    from time import gmtime, strftime
    self._data = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    from BeamerDefaults import DefaultPreamble
    self.tex_preamble = 

  def _titleSlide( self, bConf ):
    self.factory( 
    pname = self._author + '$@$' + self._machine
    self._pfile.write( (bconst.beginHeader) % \
              (self._title, self._title, pname, self._institute) )

  def __enter__(self):
    # Create output file
    from RingerCore import ensureExtension
    self._logger.verbose("Ope")
    self.
    self._pfile = open( , 'w')

    from BeamerTemplates import BeamerConstants as bconst
    self._pfile.write( bconst.beginDocument )

    self._pfile.write( bconst.beginTitlePage )
    return self

  def __str__( self ):
    self._str = ''
    with TexDocument( self._str ):
      for texObj in self:
        try:
          str_ += str(texObj)
          if str_[-1] =! '\n': str_ += '\n'
        except TexException as e:
          if not self.ignoreErrors:
            raise e
          else
            self._logger.warning('%s', e)

  def __iter__( self ):
    for texObj in self.items:
      yield texObj

  def __exit__(self, exc_type, exc_value, traceback):
    from BeamerTemplates import BeamerConstants as bconst
    self._pfile.write( bconst.endDocument )
    self._pfile.close()


class BeamerPDFReport( Logger ):

  def __init__(self, bTex):
    try:
      bTex.name
    except AttributeError:
      # Assume that it is a file

    if isinstance( bTex, BeamerTexReport ):
    else:

