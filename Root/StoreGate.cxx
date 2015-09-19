#include <string>
#include <iostream>
#include <algorithm> 

// root include(s)
#include "TObject.h"
#include "TFile.h"
#include "TH1F.h"
#include "TH1F.h"
#include "TProfile.h"
#include "TEfficiency.h"
#include "TDirectory.h"
#include "TTree.h"

#include "RingerCore/MsgStream.h"
#include "RingerCore/StoreGate.h"


using namespace SG;
using namespace std;

StoreGate::StoreGate(std::string fileName, MSG::Level msglevel):
  IMsgService("StoreGate"),
  MsgService(msglevel)
{
  
  m_basePath   = "file";
  m_fileName   = fileName;
  m_file       = new TFile(m_fileName.c_str(),"recreate");
  m_currentDir = m_basePath;
  
  m_file->mkdir(m_currentDir.c_str());
  m_file->cd(m_currentDir.c_str());
  m_dirs.clear();
  m_dirs.push_back(m_currentDir);
  MSG_INFO("storegate was created, file name is: " << m_fileName);
}

StoreGate::~StoreGate(){
  delete m_file;

  //for(auto dir : m_dirs){
   // if(m_objs[dir]) delete m_objs[dir];
  //}
}

bool StoreGate::finalize(){
  m_file->Write();
  m_file->Close();
  return true;
}


bool StoreGate::mkdir(std::string theDir){
 
  if(theDir == "")  return true; 
  cd();
  if(theDir[0] == '/')  theDir.erase(0,1);
  if(theDir[theDir.size()-1] == '/') theDir.erase(theDir.size()-1);
  std::string fullpath = m_currentDir + "/" + theDir;

  if (exist(fullpath)){
    MSG_ERROR(BOLDRED << "action mkdir can not create < " << fullpath << " > , this dir checkDirectory into storegate." << NORMAL);
    return false;
  }

  m_dirs.push_back(fullpath);  
  m_file->mkdir(fullpath.c_str());
  cd(theDir);
  return true;
}

bool StoreGate::cd(std::string theDir){
  cd();
  std::string fullpath = m_currentDir+"/"+theDir;
  if (!exist(fullpath)){
    MSG_ERROR(BOLDRED <<  "cd():  < " << fullpath << " > don't checkDirectory into storegate." << NORMAL);
    return false;
  }
  m_currentDir = fullpath;
  m_file->cd(fullpath.c_str());
  return true;
}

bool StoreGate::cd(){
  m_currentDir=m_basePath;
  m_file->cd();
  return true;
}

bool StoreGate::exist(std::string theDir){
  std::vector<std::string>::iterator it;
  it = std::find (m_dirs.begin(), m_dirs.end(), theDir);
  if (it == m_dirs.end())  return false;
  return true;
}


bool StoreGate::addHistogram( TH1F* hist){  
  std::string feature(hist->GetName());
  std::string fullpath = m_currentDir + "/" + feature;
  if(exist(fullpath)){
    MSG_WARNING(BOLDYELLOW << "This feature  "<< feature << " exist  into this path: " << m_currentDir
        << ". Storegate don't attach!" << NORMAL);
    return false;
  }
  m_dirs.push_back(fullpath); 
  m_objs[fullpath] = (TObject *)hist;
  return true;
}


bool StoreGate::addHistogram( TH2F* hist){  
  std::string feature(hist->GetName());
  std::string fullpath = m_currentDir + "/" + feature;
  if(exist(fullpath)){
    MSG_WARNING(BOLDYELLOW << "This feature "<< feature << " exist  into this path: " << m_currentDir 
        << ". Storegate don't attach!" << NORMAL);
    return false;
  }
  m_dirs.push_back(fullpath);  
  m_objs[fullpath] = (TObject *)hist;
  return true;
}


bool StoreGate::addHistogram( TEfficiency* hist){  
  std::string feature(hist->GetName());
  std::string fullpath = m_currentDir + "/" + feature;
  if(exist(fullpath)){
    MSG_WARNING(BOLDYELLOW << "This feature "<< feature << " exist  into this path: " << m_currentDir 
        << ". Storegate don't attach!" << NORMAL);
    return false;
  }
  m_dirs.push_back(fullpath);  
  m_objs[fullpath] = (TObject *)hist;
  return true;
}


bool StoreGate::addHistogram( TProfile* hist){  
  std::string feature(hist->GetName());
  std::string fullpath = m_currentDir + "/" + feature;
  if(exist(fullpath)){
    MSG_WARNING(BOLDYELLOW << "This feature  "<< feature << " exist  into this path: " << m_currentDir 
        << ". Storegate don't attach!" << NORMAL);
    return false;
  }
  m_dirs.push_back(fullpath);  
  m_objs[fullpath] = (TObject *)hist;
  return true;
}


TH1F* StoreGate::hist1(std::string feature){
  std::string fullpath = m_currentDir + "/" + feature;
  if(!exist(fullpath)){
    MSG_WARNING(BOLDYELLOW << "This feature "<< feature << " doesn't exist into this path: " << m_currentDir << "." << NORMAL);
    return 0;
  }
  MSG_DEBUG("get histogram with path: " << fullpath << " into the storegate." );
  return ((TH1F*)m_objs[fullpath]);
}


TEfficiency* StoreGate::histE(std::string feature){
  std::string fullpath = m_currentDir + "/" + feature;
  if(!exist(fullpath)){
    MSG_WARNING(BOLDYELLOW << "This feature "<< feature << " doesn't exist into this path: " << m_currentDir << "." << NORMAL);
    return 0;
  }
  MSG_DEBUG("get histogram with path: " << fullpath << " into the storegate."); 
  return ((TEfficiency*)m_objs[fullpath]);
}

TProfile* StoreGate::histP(std::string feature){
  std::string fullpath = m_currentDir + "/" + feature;
  if(!exist(fullpath)){
    MSG_WARNING(BOLDYELLOW << "This feature "<< feature << " doesn't exist into this path: " << m_currentDir << "." << NORMAL);
    return 0;
  }
  MSG_DEBUG("get histogram with path: " << fullpath << " into the storegate."); 
  return ((TProfile*)m_objs[fullpath]);
}


TH2F* StoreGate::hist2(std::string feature){
  std::string fullpath = m_currentDir + "/" + feature;
  if(!exist(fullpath)){
    MSG_WARNING(BOLDYELLOW << "This feature "<< feature << " doesn't exist into this path: " << m_currentDir << "." << NORMAL);
    return 0;
  }
  MSG_DEBUG("get histogram with path: " << fullpath << " into the storegate."); 
  return ((TH2F*)m_objs[fullpath]);
}


bool StoreGate::addTree(TTree *tree){

  std::string feature(tree->GetName());
  std::string fullpath = m_currentDir + "/" + feature;
  if(exist(fullpath)){
    MSG_WARNING(BOLDYELLOW << "This feature "<< feature << " doesn't exist into this path: " << m_currentDir 
        << ". Storegate don't attach!"<< NORMAL);
    return false;
  }
  m_dirs.push_back(fullpath);
  m_objs[feature] = (TObject*)tree;
  return true;
}


TTree* StoreGate::tree(std::string feature){
  std::string fullpath = m_currentDir + "/" + feature;
  if(!exist(fullpath)){
     MSG_WARNING(BOLDYELLOW << "this feature "<< feature << " doesn't exist into this path: " << m_currentDir << "." << NORMAL);
    return 0;
  }
  return ((TTree*)m_objs[fullpath]);
}




