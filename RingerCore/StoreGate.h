
#ifndef ANALYSISTOOLS_SYSTEM_STOREGATE_H
#define ANALYSISTOOLS_SYSTEM_STOREGATE_H

#include "TObject.h"
#include "TFile.h"
#include "TDirectory.h"
#include "TProfile.h"
#include "TH1F.h"
#include "TH2F.h"
#include "TEfficiency.h"
#include "TTree.h"
#include "RingerCore/MsgStream.h"
#include <string>
#include <map>
#include <vector>

namespace SG{
  
  class StoreGate:MsgService{
    
  public:

    StoreGate(std::string fileName, MSG::Level msglevel = MSG::INFO);
    ~StoreGate();
    bool cd();
    bool cd( std::string theDir );
    bool mkdir( std::string theDir );

    bool finalize();

    bool addHistogram( TH1F*        hist );
    bool addHistogram( TH2F*        hist );
    bool addHistogram( TEfficiency* hist );
    bool addHistogram( TProfile*    hist );
    bool addTree( TTree* tree);

    TH1F*         hist1(std::string feature );    
    TProfile*     histP(std::string feature );    
    TEfficiency*  histE(std::string feature );    
    TH2F*         hist2(std::string feature );    
    TTree*        tree( std::string feature );

  private:
    
    bool exist(std::string theDir);
    
    std::string                      m_basePath;
    std::string                      m_currentDir;
    std::string                      m_fileName;
    std::vector<std::string>         m_dirs;
    std::map<std::string, TObject* > m_objs;
    TFile*                           m_file;

  };

}// namespace


#endif
