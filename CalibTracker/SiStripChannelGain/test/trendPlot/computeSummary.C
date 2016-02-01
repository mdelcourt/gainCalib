#include "TROOT.h"
#include "TTree.h"
#include "TFile.h"
#include <iostream>



using namespace std;


string saveFile="gainTrend.root";

void computeSummary(string fileName_="",string payloadName_=""){
   if (fileName_==""){cout<<"No file specified."<<endl; return;}
   TFile * f = new TFile(saveFile.c_str(),"UPDATE");
   TTree * t = (TTree*)f->Get("payloadSummary"); 
   if (!t)return;
   float  MPV[5];
   float  Gain[5];
   gROOT->ProcessLine("#include <iostream>");
   string *payloadName = new string;
   payloadName->assign(payloadName_); 
   t->SetBranchAddress("MPV"        ,&MPV[0]           );
   t->SetBranchAddress("Gain"       ,&Gain[0]          );
   t->SetBranchAddress("MPV_TIB"    ,&MPV[1]           );
   t->SetBranchAddress("MPV_TID"    ,&MPV[2]           );
   t->SetBranchAddress("MPV_TOB"    ,&MPV[3]           );
   t->SetBranchAddress("MPV_TEC"    ,&MPV[4]           );
   t->SetBranchAddress("Gain_TIB"   ,&Gain[1]          );
   t->SetBranchAddress("Gain_TID"   ,&Gain[2]          );
   t->SetBranchAddress("Gain_TOB"   ,&Gain[3]          );
   t->SetBranchAddress("Gain_TEC"   ,&Gain[4]          );
   t->SetBranchAddress("PayloadName",&payloadName      );
   
   float NAPV[5];
   for(int i=0; i<5; i++){MPV[i]=0; Gain[i]=0; NAPV[i]=0;}
   
   TFile * f2 = new TFile(fileName_.c_str());
   TTree * t2 = (TTree*) f2->Get("SiStripCalib/APVGain");
   float MPV_origin; double Gain_origin; UChar_t subDet; bool isMasked;
   t2->SetBranchAddress("FitMPV"  ,&MPV_origin );
   t2->SetBranchAddress("Gain"    ,&Gain_origin);
   t2->SetBranchAddress("SubDet"  ,&subDet     );
   t2->SetBranchAddress("isMasked",&isMasked   );

   //Looping over tree...
   printf("Progressing Bar              :0%%       20%%       40%%       60%%       80%%       100%%\n");
   printf("Looping on the Tree          :");
   int TreeStep = t2->GetEntries()/50;if(TreeStep==0)TreeStep=1;
   for (unsigned int ientry = 0; ientry < t2->GetEntries(); ientry++) {
      if(ientry%TreeStep==0){printf(".");fflush(stdout);}
      t2->GetEntry(ientry);

      if(subDet>2 && Gain_origin > 0 && MPV_origin > 0 && ! isMasked){
         NAPV[subDet-2]++;
         NAPV[0]++;
         Gain[0]+=Gain_origin;
         MPV[0]+=MPV_origin;
         Gain[subDet-2]+=Gain_origin;
         MPV [subDet-2]+=MPV_origin;
      }

   }
   cout<<endl;
   f2->Close();
   
   for (int i=0; i<5; i++){MPV[i]/=NAPV[i]; Gain[i]/=NAPV[i];}

   f->cd();
   
   t->Fill();
   t->Write();
   f->Save();
   delete payloadName;
   f->Close();
}


