import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString
import xlsxwriter

HOSTNAME = ""
VERSION = ""
BASE_URI = ""

totVolume = {"NextSeq" : 1300.0 , 
             "MiniSeq" : 500.0, 
             "NovaSeq SP 300" : 100.0,
             "NovaSeq S1 300" : 100.0,
             "NovaSeq S2 300" : 150.0,
             "NovaSeq S4 300" : 310.0}

denConc = {"NextSeq" : 20.0 ,
           "MiniSeq" : 5.0  }

#Convert kit selection to number of available reads
KitToReads = { 'NextSeq mid 300 v2' : 260000000.0,
               'NextSeq high 300 v2' : 800000000.0,
               'MiniSeq mid 300' : 26000000.0, # changed from 19000000.0 20210210
               'MiniSeq high 300' : 50000000.0, 
               'NovaSeq SP 300' : 2000000000.0, #changed from 1600000000 20201012
               'NovaSeq S1 300' : 3500000000.0, # changed from 3200000000.0 20200810 
               'NovaSeq S2 300' : 8200000000.0, 
               'NovaSeq S4 300' : 24000000000.0 } #changed from 20000000000.0 20201116

#ng/ul to nM convertion
nMConversionFactor = { 'SureSelectXTHS' : 3.52,
                       'TruSightMyeloid' : 3.85 , 
                       'NexteraQAML' : 3.85 ,
                       'Microbiology' : 3.37, 
                       'TruSeqStrandedmRNA' : 3.44, 
                       'TWISTMyeloid' : 2.47,
                       'TWISTHereditarySolid' : 2.47, 
                       'TWISTClinicalWES' : 2.47, 
                       'TWISTLymphoma' : 2.47, 
                       'TWISTPanCancer' : 2.47,
                       'TWISTSolidTumor' : 2.47,
                       'SarsNGS' : 3.37
                       }

#TruSightMyeloid: (conc * 1000000) / (649 * 400)
#NexteraQAML: (conc * 1000000) / (649 * 400)
#SureSelectXTHS: (conc * 1000000) / (660 * 430)
#Microbiology: (conc * 1000000) / (660 * 450) 
#Twist: (conc * 1000000) / (660 * 570) 

def setupGlobalsFromURI( uri ):

    global HOSTNAME
    global VERSION
    global BASE_URI
    
    tokens = uri.split( "/" )
    HOSTNAME = "/".join(tokens[0:3])
    VERSION = tokens[4]
    BASE_URI = "/".join(tokens[0:5]) + "/"

def writeToExcel_FinalSequencingPool(poolName_Data, phiXvolume): 
    string = "##### Create final sequencing pool#####" 
    f_outsheet.write(16, 0, string, cell_format_blue)
    string = "PhiX volume (ul)" 
    row = 17
    col = 0
    f_outsheet.write(row, 0, string)
    f_outsheet.write(row, 1, phiXvolume, cell_format_2dec)
    
    for pool in (sorted(poolName_Data)):
        string = pool + " volume (ul):"
        f_outsheet.write(row+2, col, string)
        f_outsheet.write(row+2, col+1, poolName_Data[pool]["volumeToFinalSequencingPool"], cell_format_2dec)
        f_outsheet.conditional_format(row+2, col+1,row+2, col+1,{'type':     'cell',
                                                               'criteria': '<',
                                                               'value':    2,
                                                               'format':   cell_format_red})
        row +=2

def writeToExcel(instrument, poolName_Data, loadingConc, poolVol_denature, bufferVol_denature) : 
    colors = ['#FFCCE5', '#E5CCFF', '#CCFFFF', '#CCFFE5','#E5FFCC','#FFE5CC', '#FFCCCC', '#E0E0E0', '#FF9999', '#F5F5DC', '#FFCCE5', '#E5CCFF', '#CCFFFF', '#CCFFE5' ]

    row = 0
    col = 0
	
    f_outsheet.write(row+1, col, "Dilution to 10 nM:", cell_format_blue)
    f_outsheet.write(row+2, col, "Volume pool (ul):")
    f_outsheet.write(row+3, col, "Volume EB buffer (ul):")

    if instrument == "NovaSeq" :
        string = "Dilution to " +  str(loadingConc/200) + " (nM) = " + str(loadingConc) + " (pM) final loading conc. " 
    else: 
        f_outsheet.write(9, 0, "Denature and dilute the 1 nM pool according to the protocol.")
        if instrument == "NextSeq" :
            f_outsheet.write(10, 0, "Total volume should be 250 ul at 20 pM.")
        elif instrument == "MiniSeq" :
            f_outsheet.write(10, 0, "Total volume should be 1 ml at 5 pM.") 
        
        string = "FOR ALL POOLS - Dilute to loading concentration: " + str(loadingConc) + " (pM)"
        border = f_outfile.add_format({ 'bg_color': '#D3D1D0'})
        f_outsheet.set_row(11,8, border)
        f_outsheet.write(12, 0, string, cell_format_blue)
        f_outsheet.write(13, col, "Volume pool (ul):")
        f_outsheet.write(14, col, "Volume HT1 (ul):")
        f_outsheet.write(13, col+1, poolVol_denature , cell_format_2dec)
        f_outsheet.write(14, col+1, bufferVol_denature , cell_format_2dec)
        string = "Dilution to 1nM:"

    f_outsheet.write(row+5, col, string, cell_format_blue)
    f_outsheet.write(row+6, col, "Volume pool (ul):")
    f_outsheet.write(row+7, col, "Volume EB buffer (ul):")

    c = 0
    for pool in (sorted(poolName_Data)):
        cell_format_colorChange = f_outfile.add_format({'bg_color':   colors[c],
                                                        'font_color': '#0c0000'})
        f_outsheet.write(0, col+1, pool, cell_format_colorChange)
        f_outsheet.write(2, col+1, poolName_Data[pool]["poolVol_dil"] , cell_format_2dec)
        f_outsheet.write(3, col+1, poolName_Data[pool]["bufferVol_dil"] , cell_format_2dec)
        
        f_outsheet.write(6, col+1, poolName_Data[pool]["poolVol"] , cell_format_2dec)
        f_outsheet.write(7, col+1, poolName_Data[pool]["bufferVol"], cell_format_2dec )
        
        col += 1
        c += 1
	 
def getData(pools, totVol, kit, denaturedConc, phiX, winnerTakesItAll, instrument, loadingConc) : 
    #Loop over pools and calculate dilution to 1nM (not for NovaSeq) 
    requiredReadsAdjForNextera = 0 
    poolName_Data = {}
	
    for pool in pools :
        poolURI = pool.getAttribute( "output-uri" )
        poolDOM = parseString(api.GET(poolURI))
        poolName = pool.getAttribute( "name" ).split("_")[0]

        #Get UDFs
        readConutPerPool = float( api.getUDF( poolDOM, "Total required read count" ) )        
        measuredPoolConc = api.getUDF( poolDOM, "Qubit pool concentration (ng/ul)" )
        if measuredPoolConc == "" :
            print "WARNING: Did not find value for Qubit pool concentration (ng/ul)."
            sys.exit(255)
        measuredPoolConc = float(measuredPoolConc)
		
        #Convert from ng/ul to nM (use real value for  Twist-pools)
        if "TWIST" in poolName: 
            poolName = pool.getAttribute( "name" ).split("_")[0] + "_" + pool.getAttribute( "name" ).split("_")[1]
            iPoolURI = pool.getElementsByTagName("input")[0].getAttribute( "uri" )
            ipoolDOM = parseString(api.GET(iPoolURI))
            measuredFragmentSize = float( api.getUDF( ipoolDOM, "Region 1 Average Size - bp" ) )
			
            if measuredFragmentSize == "" :
                measuredPoolConc_nM = float(measuredPoolConc) * nMConversionFactor[poolName.split("_")[0]]
            else :
                measuredPoolConc_nM = float(measuredPoolConc) / (660.0 * measuredFragmentSize) * 1000000
        else: 
             measuredPoolConc_nM = float(measuredPoolConc) * nMConversionFactor[poolName]

        poolName_Data[poolName] = {}
        poolName_Data[poolName]["readCountPerPool"] = readConutPerPool
        poolName_Data[poolName]["measuredPoolConc_nM"] = measuredPoolConc_nM

        if not poolName == "NexteraQAML" :
            requiredReadsAdjForNextera += readConutPerPool

    #Combine pools and PhiX
    #Get PhiX spike-in and adjust available reads
    availableReads = KitToReads[kit]
    phiX = float(phiX)

    availableReadsAdj = (100.0 - phiX) * 0.01 * availableReads
    phiXvolume = totVol * phiX * 0.01 
    
    if "NexteraQAML" in poolName_Data.keys() :
        nexteraQAMLvolume = totVol * (float(poolName_Data["NexteraQAML"]["readCountPerPool"]) /availableReadsAdj)
        poolName_Data["NexteraQAML"]["volumeToFinalSequencingPool"] = nexteraQAMLvolume
        totVolNew = totVol - phiXvolume - nexteraQAMLvolume

    else:
        totVolNew = totVol - phiXvolume

    availableReads = (totVolNew / totVol) * availableReads

    #Distribution equal/winner    
    if winnerTakesItAll == "Equally distributed" :
        for pool in poolName_Data.keys() :
            if not pool == "NexteraQAML" :
                volumeToFinalSequencingPool = (float(poolName_Data[pool]["readCountPerPool"]) / float(requiredReadsAdjForNextera) ) * totVolNew
                poolName_Data[pool]["volumeToFinalSequencingPool"] = volumeToFinalSequencingPool

    else :
        splitList =  [i.split('_', 1)[0] for i in poolName_Data.keys()]
        if winnerTakesItAll not in splitList :
            print "Can not distribute reads to not existing pool:", winnerTakesItAll 
            sys.exit(255)
                
        for pool in poolName_Data.keys() :
            if not pool == "NexteraQAML" :
                    
                if pool.split("_")[0] == winnerTakesItAll :
                    winnerPoolsCount = splitList.count(winnerTakesItAll)
                    readsToDistribute = (availableReads - requiredReadsAdjForNextera ) / winnerPoolsCount
                    volumeToFinalSequencingPool = ((poolName_Data[pool]["readCountPerPool"] + readsToDistribute) / availableReads ) * totVolNew
                    poolName_Data[pool]["volumeToFinalSequencingPool"] = volumeToFinalSequencingPool
                    
                else:
                    volumeToFinalSequencingPool = ( poolName_Data[pool]["readCountPerPool"] / availableReads ) * totVolNew
                    poolName_Data[pool]["volumeToFinalSequencingPool"] = volumeToFinalSequencingPool
		 
    for pool in poolName_Data.keys() :
        if instrument == "NovaSeq":
            #Dilute directly to loading concentration (no denature)
			
            if float(poolName_Data[pool]["measuredPoolConc_nM"]) > 80 : 
                #First, dilute to 10 nM
                dilutedConc =  10.0
                poolVol_dil = 2.0
            
                totVol_dil = (poolVol_dil * float(poolName_Data[pool]["measuredPoolConc_nM"]) ) / dilutedConc 
                bufferVol_dil = totVol_dil - poolVol_dil

                #Then, dilute to loading concentration
                poolVol = (float(loadingConc/200) * float(totVol)) / dilutedConc
                bufferVol = float(totVol) - poolVol
				
                if poolVol < 2 :
                    totVol_2 = ( dilutedConc * poolVol_dil ) / float(loadingConc/200)
                    poolVol = 2.0
                    bufferVol = totVol_2 - poolVol
                
            else : 
                poolVol_dil = 0.0
                bufferVol_dil = 0.0
                requiredPoolVolume_5margin = poolName_Data[pool]["volumeToFinalSequencingPool"] + 5.0
                
                poolVol = (float(loadingConc/200) * float(requiredPoolVolume_5margin)) / float(poolName_Data[pool]["measuredPoolConc_nM"])
                bufferVol = float(requiredPoolVolume_5margin) - poolVol
                
                if poolVol < 2 : 
                    totVol_2 = ( float(poolName_Data[pool]["measuredPoolConc_nM"]) * 2.0 ) / float(loadingConc/200)
                    poolVol = 2.0
                    bufferVol = totVol_2 - poolVol

            poolVol_denature = 0
            bufferVol_denature = 0 
	
        else: 		
            #Not MiniSeq, MiSeq, NextSeq
            if float(poolName_Data[pool]["measuredPoolConc_nM"]) > 20 :
                poolVol_dil = 5.0
                bufferVol_dil = (( float(poolName_Data[pool]["measuredPoolConc_nM"]) * poolVol_dil) / 10.0 ) - poolVol_dil
                
                poolVol = 5.0
                bufferVol = ((10.0 * poolVol) / 1.0 ) - poolVol
                
            else :
                poolVol_dil = 0.0
                bufferVol_dil = 0.0
                poolVol = 5.0
                bufferVol = ((float(poolName_Data[pool]["measuredPoolConc_nM"]) * poolVol) / 1.0 ) - poolVol
                            
            #Denature 
            poolVol_denature = (float(loadingConc) * float(totVol )) / float(denaturedConc)
            bufferVol_denature = float(totVol) - poolVol_denature

			
        poolName_Data[pool]["poolVol_dil"] = poolVol_dil
        poolName_Data[pool]["bufferVol_dil"] = bufferVol_dil
        poolName_Data[pool]["poolVol"] = poolVol
        poolName_Data[pool]["bufferVol"] = bufferVol

    return poolName_Data, phiXvolume, poolVol_denature, bufferVol_denature

def getPoolsDOM(stepURI):
    pURI =  stepURI  + "/pools"
    pURI = pURI.replace("processes", "steps")
    pDOM = parseString(api.GET(pURI))
    pools = pDOM.getElementsByTagName( "pool" )
    return pools
	
def setUpExcel(outFile) :
    global f_outsheet
    global f_outfile
    global cell_format_2dec
    global cell_format_blue
    global cell_format_red
	
    #Open output file for writing
    f_outfile = xlsxwriter.Workbook( outFile + '.xlsx')
   
    cell_format_2dec = f_outfile.add_format()
    cell_format_2dec.set_num_format('0.00')
    
    cell_format_blue = f_outfile.add_format({'bg_color':   '#99ccff',
                                               'font_color': '#0c0000'})

    cell_format_red = f_outfile.add_format({'bg_color':   '#ff4c4c',
                                             'font_color': '#0c0000'})


    f_outsheet = f_outfile.add_worksheet()
    columns = (50, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29)

    for i in range(len(columns)):
        f_outsheet.set_column(i, i, columns[i])

def main():
    global api
    global f_outsheet
    global f_outfile
    global cell_format_2dec
    global cell_format_blue

    api = None    
    api = glsapiutil.glsapiutil2()

    args = {}
    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:k:x:c:l:r:")
    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-k':
            args[ "kit" ] = p
        elif o == '-x':
            args[ "phiX" ] = p
        elif o == '-c':
            args[ "loadingConc" ] = p  
        elif o == '-l':
            args[ "outFile" ] = p
        elif o == '-r':
            args[ "winnerTakesItAll" ] = p

    #Set up globals
    setupGlobalsFromURI( args[ "stepURI" ] )
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )

    #Set up Excelfile, sheet and formats 
    setUpExcel(args[ "outFile" ]) 

    #Go to the pools endpoint and get Pool URIs
    pools = getPoolsDOM(args[ "stepURI" ])

    #Get instrument from chosen kit
    kit = args[ "kit" ]
    instrument =  args[ "kit" ].split(" ")[0]
    
    #Get chosen loading concentration
    loadingConc = float( args[ "loadingConc" ] )
	
    if "NovaSeq" in instrument :
        totVol = float(totVolume[kit])        
        denaturedConc = 0
    else: 
        totVol = float(totVolume[instrument])
        denaturedConc = float(denConc[instrument])

    poolName_Data, phiXvolume, poolVol_denature, bufferVol_denature = getData(pools, totVol, kit, denaturedConc, args[ "phiX" ] , args[ "winnerTakesItAll" ] , instrument, loadingConc ) 
    
    writeToExcel(instrument, poolName_Data, loadingConc, poolVol_denature, bufferVol_denature)
		
    writeToExcel_FinalSequencingPool(poolName_Data, phiXvolume)
	

    f_outfile.close()
	
if __name__ == "__main__":
    main()
