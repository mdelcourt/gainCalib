from ROOT import *
import os


def execute(script,args):
   argstr=""
   for a in args:
      argstr+="%s,"%a
   argstr=argstr[:-1]
   cmd="echo 'gROOT->LoadMacro(\"%s_C.so\"); %s(%s); gSystem->Exit(0);' | root -b -l"%(script,script,argstr)
   os.system(cmd)


payloadFolder = ".."
collector="computeSummary"


#Get files to process
f=TFile("gainTrend.root")
t=f.Get("payloadSummary")
processedRuns = [ payload.PayloadName for payload in t ]
print "Payloads %s found in data file."%processedRuns


for x in t : print x.PayloadName
toProcess = [ payload if "Data_Run" in payload and not payload in processedRuns else '' for payload in os.listdir(payloadFolder)]
while '' in toProcess:toProcess.remove('')
print "Left to process : %s"%toProcess


#Process files
#Compile
os.system("root -b -l -q %s.C+"%collector)

#Running...
for payload in toProcess:
   fullPath='\"'+payloadFolder+"/"+payload+"/Gains.root\""
   arg=[fullPath,'\"'+payload+'\"']
   execute(collector,arg)

#Plotter :





