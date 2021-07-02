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
xrow = 0
xcol = 0

totVolume = {"NextSeq" : 1300.0 , 
             "MiniSeq" : 500.0, 
             "NovaSeq SP 300" : 100.0,
             "NovaSeq S4 300" : 310.0}

denConc = {"NextSeq" : 20.0 ,
           "MiniSeq" : 5.0  }

#Convert kit selection to number of available reads
KitToReads = { 'NextSeq mid 300 v2' : 260000000.0,
               'NextSeq high 300 v2' : 800000000.0,
               'MiniSeq mid 300' : 19000000.0, # changed from 16000000.0 20200701
               'MiniSeq high 300' : 50000000.0, 
               'NovaSeq SP 300' : 2000000000.0, #changed from 1600000000 20201012
               'NovaSeq S4 300' : 24000000000.0 } #changed from 20000000000.0 20201116

#ng/ul to nM convertion
nMConversionFactor = { 'SureSelectXTHS' : 3.52,
                       'TruSightMyeloid' : 3.85 , 
                       'NexteraQAML' : 3.85 ,
                       'Microbiology' : 3.37, 
                       'TruSeqStrandedmRNA' : 3.44, 
                       'TWISTMyeloid' : 2.47,
                       'TWISTHereditarySolid' : 2.47, 
                       'TWISTClinicalWES' : 2.47}

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

def writeDilutionToFile( measuredPoolConc_nM ) : 
    global xrow
    global xcol
    global cell_format_2dec
    global cell_format_grey

    #If concentration more than 10nM --> Dilute to 10 nM first
    if measuredPoolConc_nM > 10 :
        f_outsheet.write_string(xrow, xcol, "Dilution to 10 nM:", cell_format_grey)
        xrow +=1
        f_outsheet.write(xrow, xcol, "Volume pool (ul):")
        f_outsheet.write_number(xrow, xcol+1, 5.00, cell_format_2dec)
        xrow +=1
        f_outsheet.write(xrow, xcol, "Volume EB buffer (ul):")
        volumeRSB = ((measuredPoolConc_nM * 5.0) / 10.0 ) - 5.0
        f_outsheet.write_number(xrow, xcol+1, volumeRSB, cell_format_2dec)
        xrow +=2

        f_outsheet.write_string(xrow, xcol, "Dilution to 1 nM:", cell_format_grey)
        xrow +=1
        f_outsheet.write(xrow, xcol, "Volume pool (ul):")
        f_outsheet.write_number(xrow, xcol+1, 5.00, cell_format_2dec)
        xrow +=1
        f_outsheet.write(xrow, xcol, "Volume EB buffer (ul):")
        volumeRSB = ((10.0 * 5.0) / 1.0 ) - 5.0
        f_outsheet.write_number(xrow, xcol+1, volumeRSB, cell_format_2dec)
        xrow +=2
    else :
        f_outsheet.write_string(xrow, xcol, "Dilution to 1 nM:", cell_format_grey)
        xrow +=1
        f_outsheet.write(xrow, xcol, "Volume pool (ul):")
        f_outsheet.write_number(xrow, xcol+1, 5.00, cell_format_2dec)
        xrow +=1
        f_outsheet.write(xrow, xcol, "Volume EB buffer (ul):")
        volumeRSB = ((measuredPoolConc_nM * 5.0) / 1.0 ) - 5.0
        f_outsheet.write_number(xrow, xcol+1, volumeRSB, cell_format_2dec)
        xrow +=2

def main():
    global api
    api = None    
    api = glsapiutil.glsapiutil2()
    global f_outsheet
    global xrow
    global xcol

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

    #Open output file for writing
    f_outfile = xlsxwriter.Workbook(args[ "outFile" ] + '.xlsx')
    global cell_format_2dec
    cell_format_2dec = f_outfile.add_format()
    cell_format_2dec.set_num_format('0.00')

    global cell_format_yellow
    cell_format_yellow = f_outfile.add_format({'bg_color':   '#FFEB9C',
                                               'font_color': '#0c0000'})

    global cell_format_red
    cell_format_red = f_outfile.add_format({'bg_color':   '#ff4c4c',
                                            'font_color': '#0c0000'})
    global cell_format_blue
    cell_format_blue = f_outfile.add_format({'bg_color':   '#9bdaff',
                                               'font_color': '#0c0000'})

    global cell_format_grey
    cell_format_grey = f_outfile.add_format({'bg_color':   '#d4d5d6',
                                               'font_color': '#0c0000'})
    f_outsheet = f_outfile.add_worksheet()
    columns = (98, 18)

    for i in range(len(columns)):
        f_outsheet.set_column(i, i, columns[i])

    #Go to the pools endpoint and get Pool URIs
    pURI =  args[ "stepURI" ]  + "/pools"
    pURI = pURI.replace("processes", "steps")
    pDOM = parseString(api.GET(pURI))
    pools = pDOM.getElementsByTagName( "pool" )

    #Get instrument from chosen kit
    kit = args[ "kit" ]
    instrument =  args[ "kit" ].split(" ")[0]
    if "NovaSeq" in instrument :
        totVol = float(totVolume[kit])
        
    else: 
        totVol = float(totVolume[instrument])
        denaturedConc = float(denConc[instrument])

    #Get chosen loading concentration
    loadingConc = float( args[ "loadingConc" ] )
    
    poolName_RequiredReads = {}

    #Loop over pools and calculate dilution to 1nM
    requiredReadsAdjForNextera = 0 

    for pool in pools :
        poolURI = pool.getAttribute( "output-uri" )
        poolDOM = parseString(api.GET(poolURI))
        poolName = pool.getAttribute( "name" ).split("_")[0]
        if "TWIST" in poolName: 
            poolName = pool.getAttribute( "name" ).split("_")[0] + "_" + pool.getAttribute( "name" ).split("_")[1]

        #Get UDFs
        readConutPerPool = float( api.getUDF( poolDOM, "Total required read count" ) )
        poolName_RequiredReads[poolName] = readConutPerPool

        if not poolName == "NexteraQAML" :
            requiredReadsAdjForNextera += readConutPerPool

        poolVolume = float( api.getUDF( poolDOM, "Pool volume (ul)" ))
        measuredPoolConc = api.getUDF( poolDOM, "Qubit pool concentration (ng/ul)" )
    
        if measuredPoolConc == "" :
            print "WARNING: Did not find value for Qubit pool concentration (ng/ul)."
            sys.exit(255)
        measuredPoolConc = float(measuredPoolConc)
        #Dilute to 1nM 
        string =  "###### Dilution of " + poolName + "######"
        f_outsheet.write_string(xrow, xcol, string, cell_format_yellow)
        xrow += 2
        
        #Convert from ng/ul to nM
        if "TWIST" in poolName:
            iPoolURI = pool.getElementsByTagName("input")[0].getAttribute( "uri" )
            ipoolDOM = parseString(api.GET(iPoolURI))
            measuredFragmentSize = float( api.getUDF( ipoolDOM, "Region 1 Average Size - bp" ) )
            if measuredFragmentSize == "" :
                measuredPoolConc_nM = float(measuredPoolConc) * nMConversionFactor[poolName.split("_")[0]]
            else :
                measuredPoolConc_nM = float(measuredPoolConc) / (660.0 * measuredFragmentSize) * 1000000
        else: 
             measuredPoolConc_nM = float(measuredPoolConc) * nMConversionFactor[poolName]

        if instrument == "NovaSeq":

            #Dilute pool to correct nM concentration (based on the desired final loading concentration in pM). Table from illumina NovaSeq standard protocol. 
            string = "Dilute pool to correct nM concentration: " +  str(loadingConc/200) + " based on desired final loading concentration " + str(loadingConc) + " (pM)"

            if float(measuredPoolConc_nM) > 80 : 
                dilutedConc =  10.0
                poolVol10 = 2.0
                f_outsheet.write(xrow, xcol, "Dilution to 10 nM")
                xrow += 1
                f_outsheet.write(xrow, xcol, "Volume pool (ul)")
                f_outsheet.write_number(xrow, xcol+1, poolVol10, cell_format_2dec)
                xrow += 1
                f_outsheet.write(xrow, xcol, "Volume Buffer(ul)")
                totVol10 = (poolVol10 * float(measuredPoolConc_nM) ) / dilutedConc 
                bufferVol10 = totVol10 - poolVol10
                f_outsheet.write_number(xrow, xcol+1, bufferVol10, cell_format_2dec)
                xrow += 2

                f_outsheet.write_string(xrow, xcol, string, cell_format_grey)
                xrow += 1

                f_outsheet.write(xrow, xcol, "Volume pool (ul)")
                poolVol = (float(loadingConc/200) * float(totVol)) / dilutedConc
                bufferVol = float(totVol) - poolVol
                if poolVol < 2 :
                    totVolNew = ( dilutedConc * poolVol10 ) / float(loadingConc/200)
                    poolVol = 2.0
                    bufferVol = totVolNew - poolVol
                f_outsheet.write_number(xrow, xcol+1, poolVol, cell_format_2dec)
                xrow += 1
                f_outsheet.write(xrow, xcol, "Volume Buffer(ul)")
                f_outsheet.write_number(xrow, xcol+1, bufferVol, cell_format_2dec)
                xrow += 2
                
            else : 
                f_outsheet.write_string(xrow, xcol, string, cell_format_grey)
                xrow += 1
                f_outsheet.write(xrow, xcol, "Volume pool (ul)")
                poolVol = (float(loadingConc/200) * float(totVol)) / float(measuredPoolConc_nM)
                bufferVol = float(totVol) - poolVol
                if poolVol < 2 : 
                    totVolNew = ( float(measuredPoolConc_nM) * 2.0 ) / float(loadingConc/200)
                    poolVol = 2.0
                    bufferVol = totVolNew - poolVol
                f_outsheet.write_number(xrow, xcol+1, poolVol, cell_format_2dec)
                xrow += 1
                f_outsheet.write(xrow, xcol, "Volume Buffer(ul)")
                f_outsheet.write_number(xrow, xcol+1, bufferVol, cell_format_2dec)
                xrow += 2
                                        
        else: 
            writeDilutionToFile(measuredPoolConc_nM)
        
            #Denature an dilute
            f_outsheet.write(xrow, xcol, "Denature and dilute the 1 nM pool according to the protocol.")
            xrow += 1
            if instrument == "NextSeq" :
                f_outsheet.write(xrow, xcol, "Total volume should be 250 ul at 20 pM.")
            elif instrument == "MiniSeq" :
                f_outsheet.write(xrow, xcol, "Total volume should be 1 ml at 5 pM.")
            xrow += 2

            #Dilute to  loading conc
            string = "Dilute to loading concentration: " + str(loadingConc) + " (pM)"
            f_outsheet.write_string(xrow, xcol, string, cell_format_grey)
            xrow += 1

            f_outsheet.write(xrow, xcol, "Volume pool (ul)")
            poolVol = (float(loadingConc) * float(totVol )) / float(denaturedConc)
            bufferVol = float(totVol) - poolVol
            f_outsheet.write_number(xrow, xcol+1, poolVol, cell_format_2dec)
            xrow += 1
            f_outsheet.write(xrow, xcol, "Volume HT1(ul)") 
            f_outsheet.write_number(xrow, xcol+1, bufferVol, cell_format_2dec)
            xrow += 2

    #Combine pools and PhiX

    #Get PhiX spike-in and adjust available reads
    availableReads = KitToReads[args[ "kit" ]]
    phiX = float(args[ "phiX" ])

    availableReadsAdj = (100.0 - phiX) * 0.01 * availableReads
    phiXreads = availableReads - availableReadsAdj
    phiXvolume = totVol * phiX * 0.01 
    
    f_outsheet.write_string(xrow, xcol, "######Create final sequencing pool######", cell_format_blue)
    xrow +=1
    f_outsheet.write(xrow, xcol, "PhiX volume (ul):")
    f_outsheet.write_number(xrow, xcol+1, phiXvolume, cell_format_2dec)
    xrow +=2
        

    if "NexteraQAML" in poolName_RequiredReads.keys() :
        nexteraQAMLvolume = totVol * (float(poolName_RequiredReads["NexteraQAML"]) /availableReadsAdj)
        f_outsheet.write(xrow, xcol, "NexteraQAML volume (ul):")
        f_outsheet.write_number(xrow, xcol+1, nexteraQAMLvolume, cell_format_2dec)
        xrow +=2
        
        totVolNew = totVol - phiXvolume - nexteraQAMLvolume
        availableReads = (totVolNew / totVol) * availableReads

    else:
        totVolNew = totVol - phiXvolume
        availableReads = (totVolNew / totVol) * availableReads

    #Distribution equal/winner
            
    if args[ "winnerTakesItAll" ] == "Equally distributed" :
        for pool in poolName_RequiredReads.keys() :
            if not pool == "NexteraQAML" :
                volumeToFinalSequencingPool = (float(poolName_RequiredReads[pool]) / float(requiredReadsAdjForNextera) ) * totVolNew
                string = pool + " volume (ul):"
                f_outsheet.write(xrow, xcol, string)
                f_outsheet.write_number(xrow, xcol+1, volumeToFinalSequencingPool, cell_format_2dec)
                f_outsheet.conditional_format(xrow,xcol+1,xrow,xcol+1,{'type':     'cell',
                                                              'criteria': '<',
                                                              'value':    2,
                                                              'format':   cell_format_red})
                xrow +=2

    else :
        splitList =  [i.split('_', 1)[0] for i in poolName_RequiredReads.keys()]
        if args[ "winnerTakesItAll" ] not in splitList :
            print "Can not distribute reads to not existing pool:", args[ "winnerTakesItAll" ] 
            sys.exit(255)
                
        for pool in poolName_RequiredReads.keys() :
            if not pool == "NexteraQAML" :
                    
                if pool.split("_")[0] == args[ "winnerTakesItAll" ] :
                    winnerPoolsCount = splitList.count(args[ "winnerTakesItAll" ])
                    readsToDistribute = (availableReads - requiredReadsAdjForNextera ) / winnerPoolsCount
                    volumeToFinalSequencingPool = ((poolName_RequiredReads[pool] + readsToDistribute) / availableReads ) * totVolNew
                    string = pool + " volume (ul):"
                    f_outsheet.write(xrow, xcol, string)
                    f_outsheet.write_number(xrow, xcol+1, volumeToFinalSequencingPool, cell_format_2dec)
                    f_outsheet.conditional_format(xrow,xcol+1,xrow,xcol+1,{'type':     'cell', 
                                                                       'criteria': '<',
                                                                       'value':    2,
                                                                       'format':   cell_format_red})
                    xrow +=2
                    
                else:
                    volumeToFinalSequencingPool = ( poolName_RequiredReads[pool] / availableReads ) * totVolNew
                    string = pool + " volume (ul):"
                    f_outsheet.write(xrow, xcol, string)
                    f_outsheet.write_number(xrow, xcol+1, volumeToFinalSequencingPool, cell_format_2dec)
                    f_outsheet.conditional_format(xrow,xcol+1,xrow,xcol+1,{'type':     'cell',
                                                                       'criteria': '<',
                                                                       'value':    2,
                                                                       'format':   cell_format_red})
                    xrow +=2

    f_outfile.close()
if __name__ == "__main__":
    main()
