
from RingerCore import StoreGate
from ROOT import TH1F, TGraph
import numpy as np

SG = StoreGate( 'monitoring.root' )
SG.mkdir( 'dir1/dir2' )
SG.mkdir( 'dir3' )



SG.cd('dir1/dir2')

h1 = TH1F('h1','',100,0,1)
g1 = TGraph(3, np.array([0,1,2]), np.array([0,2,3]) )
g1.SetName('g1')

SG.attach(h1)
SG.cd('dir3')
SG.attach(g1)

del SG
