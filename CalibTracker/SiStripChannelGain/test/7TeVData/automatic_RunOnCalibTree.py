#!/usr/bin/env python

import os,sys
import getopt
import commands
import time
import ROOT
import urllib
import string
import optparse

def numberOfEvents(file):
	rootfile = ROOT.TFile.Open(file,'read')
	tree = ROOT.TTree()
	rootfile.GetObject("gainCalibrationTree/tree",tree)
        NEntries = tree.GetEntries()
        rootfile.Close()
        print file +' --> '+str(NEntries)
	return NEntries	


PCLDATASET = '/StreamExpress/Run2015D-PromptCalibProdSiStripGains-Express-v3/ALCAPROMPT' #used if usePCL==True
#PCLDATASET = '/StreamExpress/Run2015D-PromptCalibProdSiStripGains-Express-v4/ALCAPROMPT' #used if usePCL==True

#PCLDATASET = '/StreamHIExpress/HIRun2015-PromptCalibProdSiStripGains-Express-v1/ALCAPROMPT' #used if usePCL==True
CALIBTREEPATH = '/store/group/dpg_tracker_strip/comm_tracker/Strip/Calibration/calibrationtree/GR15' #used if usePCL==False
#CALIBTREEPATH = "/castor/cern.ch/user/m/mgalanti/calibrationtree/GR12"
#CALIBTREEPATH = "/castor/cern.ch/user/m/mgalanti/calibrationtree/GR11"

#runsToVeto = [257365,257364,257363,257361,257360,257359,257358,257357,257356,257355,257354,257353,257351,257349,257348,257347,257346,257345,257344,257342,257341,257340,257339,257338,257337,257336,257335,257334,257332,257331,257330,257329,257328,257327,257326,257325,257324,257323,257322,257321,257319,257307,257306,257305,257303,257302,257301,257299,257297,257296,257295,257287,257284,257281,257280,257279,257276,257275,257274,257270,257268,257253,257252,257251,257249,257248,257247,257246,257244,257243,257234,257233,257232,257231,257230,257222,257217,257216,257208,257207,257206,257205,257204,257198,257196,257195,257194,257193,257192,257187,257186,257184,257182,257180,257177,257174,257173,257171,257170,257168,257163,257161,257160,257159,257158,257156,257154,257153,257150,257148,257145,257144,257143,257140,257139,257135,257134,257133,257132,257131,257129,257128,257127,257126,257125,257124,257123,257122,257120,257118,257117,257116,257115,257114,257113,257112,257110,257109,257108,257105,257101,257100,257099,257098,257097,257095,257093,257092,257091,257090,257089,257088,257087,257086,257085,257081,257080,257079,257076,257075,257073,257072,257071,257068,257067,257066,257065,257064,257063,257062,257061,257059,257058,257057,257055,257054,257052,257051,257050,257049,257048,257046,257045,257044,257043,257042,257041,257040,257039,257038,257037,257036,257035,257034,257032,257031,257027,]


runsToVeto = []
#runsToVeto = [247388, 247389, 247395247395, 247397, 247982, 248026, 248031, 248033]


#read arguments to the command line
#configure
usage = 'usage: %prog [options]'
parser = optparse.OptionParser(usage)
parser.add_option('-f', '--firstRun'   ,    dest='firstRun'           , help='first run to process (-1 --> automatic)'  , default='-1')
parser.add_option('-l', '--lastRun'    ,    dest='lastRun'            , help='last run to process (-1 --> automatic)'   , default='-1')
parser.add_option('-P', '--publish'    ,    dest='publish'            , help='publish the results'                      , default='False')
parser.add_option('-p', '--pcl'        ,    dest='usePCL'             , help='use PCL output instead of calibTree'      , default='False')
(opt, args) = parser.parse_args()

scriptDir = os.getcwd()
globaltag="75X_dataRun2_Express_v0"
#globaltag="74X_dataRun2_Express_v3"
#globaltag = "75X_dataRun2_v5"#"74X_dataRun2_Express_v2"
firstRun = int(opt.firstRun)
lastRun  = int(opt.lastRun)
MC=""
publish = (opt.publish=='True')
mail = "martin.delcourt@cern.ch"
automatic = True;
usePCL = (opt.usePCL=='True')
maxNEvents = 500000000

if(firstRun!=-1 or lastRun!=-1): automatic = False


print "firstRun = " +str(firstRun)
print "lastRun  = " +str(lastRun)
print "publish  = " +str(publish)
print "usePCL   = " +str(usePCL)



#go to parent directory = test directory
os.chdir("..");

#identify last run of the previous calibration
if(firstRun<=0):
   out = commands.getstatusoutput("ls /afs/cern.ch/cms/tracker/sistrvalidation/WWW/CalibrationValidation/ParticleGain/ | grep Run_ | tail -n 1");
   firstRun = int(out[1].split('_')[3])+1
   print "firstRun = " +str(firstRun)


initEnv='cd ' + os.getcwd() + ';'
initEnv+='source /afs/cern.ch/cms/cmsset_default.sh' + ';'
initEnv+='eval `scramv1 runtime -sh`' + ';'

eosLs = "/afs/cern.ch/project/eos/installation/0.3.84-aquamarine/bin/eos.select ls -lrth "
#Get List of Files to process:
NTotalEvents = 0;
run = 0
FileList = ""

if(usePCL==True):
   print("Get the list of PCL output files from DAS")
   results = commands.getstatusoutput(initEnv+"das_client.py  --limit=9999 --query='run dataset="+PCLDATASET+"'")[1].splitlines()
   results.sort()
   for line in results:
      if(line.startswith('Showing')):continue
      if(len(line)<=0):continue
      linesplit = line.split('   ')
      print linesplit
      run     = int(line.split('   ')[0])      
      if(run<firstRun or run in runsToVeto):continue
      if(lastRun>0 and run>lastRun):continue      
      #check that this run at least contains some events
      print("Checking number of events in run %i" % run)
      NEventsDasOut = commands.getstatusoutput(initEnv+"das_client.py  --limit=9999 --query='summary dataset="+PCLDATASET+" run="+str(run)+" | grep summary.nevents'")[1].splitlines()[-1]
      if(not NEventsDasOut.isdigit() ):
         print ("issue with getting number of events from das, skip this run")
         print NEventsDasOut
         continue
      if(FileList==""):firstRun=run;
      NEvents = int(NEventsDasOut)
      if(NEvents<=3000):continue #only keep runs with at least 3K events
      FileList+="#run=" + str(run) + " -->  NEvents="+str(NEvents/1000).rjust(8)+"K\n"
      resultsFiles = commands.getstatusoutput(initEnv+"das_client.py  --limit=9999 --query='file dataset="+PCLDATASET+" run="+str(run)+"'")
      if(int(resultsFiles[0])!=0 or results[1].find('Error:')>=0):
         print ("issue with getting the list of files from das, skip this run")
         print resultsFiles
         continue
      for f in resultsFiles[1].splitlines():
         if(not f.startswith('/')):continue
         FileList+='calibTreeList.extend(["'+f+'"])\n'
      NTotalEvents += NEvents;
      print("Current number of events to process is " + str(NTotalEvents))
      if(automatic==True and NTotalEvents >= maxNEvents):break;
else:
   print("Get the list of calibTree from castor (eos ls " + CALIBTREEPATH + ")")
   calibTreeInfo = commands.getstatusoutput(eosLs+CALIBTREEPATH)[1].split('\n');
   calibTreeInfo.sort()
   print("Check the number of events available");
   for info in calibTreeInfo:
      if(len(info)<1):continue;
      subParts = info.split();       
      if(not len(subParts)>4 or not subParts[4].isdigit()):
         if len(subParts)>4:
            print subParts[4]
         continue;
      size = int(subParts[4])/1048576;
      if(size < 10): continue	#skip file<10MB
      runS = subParts[8].replace(CALIBTREEPATH+'/',"").replace("calibTree_","").replace(".root","")
      run = int(runS.split('_')[0])
      print "Run : %s"%run
      if(run<firstRun or run in runsToVeto):continue
      if(lastRun>0 and run>lastRun):continue
      print subParts[8]
      NEvents = numberOfEvents("root://eoscms//eos/cms"+CALIBTREEPATH+"/"+subParts[8]);	
      if(NEvents<=3000):continue #only keep runs with at least 3K events
      if(FileList==""):firstRun=run;
      FileList += 'calibTreeList.extend(["root://eoscms//eos/cms'+CALIBTREEPATH+"/"+subParts[8]+'"]) #' + str(size).rjust(6)+'MB  NEvents='+str(NEvents/1000).rjust(8)+'K\n'
      NTotalEvents += NEvents;
      print("Current number of events to process is " + str(NTotalEvents))
      if(automatic==True and NTotalEvents >= maxNEvents):break;


if(lastRun<=0):lastRun = run

print "RunRange=[" + str(firstRun) + "," + str(lastRun) + "] --> NEvents=" + str(NTotalEvents/1000)+"K"
if(automatic==True and NTotalEvents<100):#500000):	#ask at least 500K events to perform the calibration
	print 'Not Enough events to run the calibration'
        os.system('echo "Gain calibration postponed" | mail -s "Gain calibration postponed ('+str(firstRun)+' to '+str(lastRun)+') NEvents=' + str(NTotalEvents/1000)+'K" ' + mail)
	exit(0);

name = "Run_"+str(firstRun)+"_to_"+str(lastRun); 
if(usePCL==True):   name = name+"_PCL"
else:               name = name+"_CalibTree"

oldDirectory = "7TeVData"
newDirectory = "Data_"+name;
os.system("mkdir -p " + newDirectory);
os.system("cp " + oldDirectory + "/* " + newDirectory+"/.");
file = open(newDirectory+"/FileList_cfg.py", "w")
file.write("import FWCore.ParameterSet.Config as cms\n")
file.write("calibTreeList = cms.untracked.vstring()\n")
file.write("#TotalNumberOfEvent considered is %i\n" % NTotalEvents)
file.write(FileList)
file.close()
os.system("cat " + newDirectory + "/FileList_cfg.py")
os.system("sed -i 's|XXX_FIRSTRUN_XXX|"+str(firstRun)+"|g' "+newDirectory+"/*_cfg.py")
os.system("sed -i 's|XXX_LASTRUN_XXX|"+str(lastRun)+"|g' "+newDirectory+"/*_cfg.py")
os.system("sed -i 's|XXX_GT_XXX|"+globaltag+"|g' "+newDirectory+"/*_cfg.py")
os.system("sed -i 's|XXX_PCL_XXX|"+str(usePCL)+"|g' "+newDirectory+"/*_cfg.py")
os.chdir(newDirectory);
if(os.system("sh sequence.sh \"" + name + "\" \"CMS Preliminary  -  Run " + str(firstRun) + " to " + str(lastRun) + "\"")!=0):
	os.system('echo "Gain calibration failed" | mail -s "Gain calibration failed ('+name+')" ' + mail)        
else:
	if(publish==True):os.system("sh sequence.sh " + name);
	os.system('echo "Gain calibration done\nhttps://test-stripcalibvalidation.web.cern.ch/test-stripcalibvalidation/CalibrationValidation/ParticleGain/" | mail -s "Gain calibration done ('+name+')" ' + mail)

if(usePCL==True):
   #Make the same results using the calibTrees for comparisons
   os.chdir(scriptDir); #go back to initial location
   #os.system('python automatic_RunOnCalibTree.py --firstRun ' + str(firstRun) + ' --lastRun ' + str(lastRun) + ' --publish False --pcl False')

if(automatic==True):
   #call the script one more time to make sure that we do not have a new run to process
   os.chdir(scriptDir); #go back to initial location
   os.system('python automatic_RunOnCalibTree.py')

