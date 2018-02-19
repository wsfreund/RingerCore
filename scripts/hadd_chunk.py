#!/usr/bin/env python

from RingerCore import ( ArgumentParser, BooleanStr, OMP_NUM_THREADS
                       , grouper, Logger, LoggingLevel )
from itertools import repeat
import sys, os, tempfile
from shutil import rmtree
from subprocess import call, PIPE

hadd_chunk = ArgumentParser( add_help = False
                           , description = '')
hadd_chunk.add_argument('target', action='store', help = "Target file")
hadd_chunk.add_argument('files', action='store', nargs='+', help = "Input files")
hadd_chunk.add_argument('--chunk-size', action='store', type=int, default=50,
            help = "Chunk size of the hadd jobs")
hadd_chunk.add_argument('--divide-by-run', action='store_true', 
                        help = """Try to divide using run counts equally.""")
args, argv = hadd_chunk.parse_known_args()
argv=list(argv)

mainLogger = Logger.getModuleLogger( __name__, LoggingLevel.INFO )

def lcall(inputs):
  target = inputs[0]
  files = list(filter(lambda x: x is not None,inputs[1]))
  with open(os.devnull, "w") as w:
    if not call(['hadd'] + argv + [target] + files, stdout=w):
      mainLogger.info('target %s successfully created', target)
    else:
      mainLogger.error('target %s failed', target)
  return target

if os.path.exists(args.target) and not '-f' in argv:
  mainLogger.fatal("target file already exists")

if args.divide_by_run:
  from TuningTools import GridJobFilter
  from RingerCore import select, straverse, apply_sort, NotSet
  from collections import Counter
  from operator import itemgetter
  from itertools import count
  import ROOT
  def getNEvents(path):
    try:
      f = ROOT.TFile(path)
      h = f.Get('h_Cutflow')
      ret = h[51]
      f.Close()
      return ret
    except IndexError: return 0
  #from ElectronIDDevelopment.histAndPDFComparisonHelpers import getRunNumber
  ffilter = GridJobFilter()
  jobFilters = ffilter( args.files )
  jobFileCollection = select( args.files, jobFilters, popListInCaseOneItem=False )
  #jobNFilesCollection = map(len, jobFileCollection)
  # get run numbers:
  #runNumbers = [ getRunNumber(jobFiles[0]) for jobFiles in jobFileCollection ]
  events = [ map(getNEvents,pathList) for pathList in jobFileCollection ]
  jobFileCollection1 = []
  jobFileCollection2 = []
  nevents1 = 0
  nevents2 = 0
  for jobFileList, eventList in reversed(zip(jobFileCollection, events)):
    jobFileList1 = []
    jobFileList2 = []
    for fname, fnevents in zip(jobFileList, eventList):
      if not fnevents: continue
      if nevents2 > nevents1:
        jobFileList1.append(fname); nevents1 += fnevents
      else:
        jobFileList2.append(fname); nevents2 += fnevents
    jobFileCollection1.append(jobFileList1)
    jobFileCollection2.append(jobFileList2)
  mainLogger.info("Final number of events distribution: (group1:%d,group2:%d)", nevents1, nevents2)
  mainLogger.info("Number of files per run: %r", zip(map(len, jobFileCollection1), map(len, jobFileCollection2)))
  args.files=list(straverse(jobFileCollection2))

if OMP_NUM_THREADS>1:
  from multiprocessing import Pool
  p = Pool(OMP_NUM_THREADS)
else:
  class P: pass
  p = P()
  p.map = map
files = args.files
oldTemp = None

while len(files) > 1:
  taskFiles = list(grouper( files, args.chunk_size ))
  tmpFile = tempfile.mkdtemp()
  if len(taskFiles) > 1:
    targets = [os.path.join(tmpFile,'tmp_%d.root' % i) for i in range(len(taskFiles))]
  else:
    targets = [args.target]
  files = p.map(lcall, zip(targets, taskFiles) )
  if oldTemp is not None:
    if oldTemp.startswith( tempfile.tempdir ): rmtree( oldTemp )
  oldTemp = tmpFile
if oldTemp is not None:
  if oldTemp.startswith( tempfile.tempdir ): rmtree( oldTemp )

