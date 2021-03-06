import sys
import re
import os
import getopt
from genologics.lims import *
from genologics.entities import *
import datetime
from subprocess import call

now = datetime.datetime.now()
api = None

def printLabel(Input):

    #Get the date
    Date = now.strftime("%Y-%m-%d")
    
    for k in sorted(Input):
        filename = '/all/' + Input[k]["sampleLimsID"] + '.zpl'
        f = open(filename, 'w+')
        #print '^XA\n^CFA,25\n^FO25,20^FD' + Input[k]["scanBID"] + ' LYSATE^FS\n^CFA,20\n^FO25,45^FD' + k + '^FS\n^FO25,65^FD' + Date + '^FS\n^XZ'
        #sys.exit(255)

        f.write('^XA\n^CFA,25\n^FO25,20^FD' + k + ' LYS^FS\n^CFA,20\n^FO25,45^FD' + Input[k]["scanBID"] + '^FS\n^FO25,65^FD' + Date + '^FS\n^XZ')
        f.close()
        call( ['lp','-d','ZebraPat','-o','raw',filename])
        os.remove(filename)

def getInputSamples(process):
    InputSamples = {}
    for input in process.all_inputs(unique=True) : 
        sampleName = input.samples[0].name
        sampleLimsID = input.samples[0].id
        scanBID = input.samples[0].udf["SCAN-B ID"]
        InputSamples[sampleName] = {"scanBID" : scanBID, 
                                    "sampleLimsID" : sampleLimsID }
    
    return InputSamples

def main():

    global args
    args = {}
    opts, extraparams = getopt.getopt(sys.argv[1:], "b:u:p:s:")

    for o,p in opts:
        if o == '-b':
            args[ "BASEURI" ] = p
        elif o == '-u':
            args[ "USERNAME" ] = p
        elif o == '-p':
            args[ "PASSWORD" ] = p
        elif o == '-s':
            args[ "stepID" ] = p

    BASEURI = args["BASEURI"].split('api')[0]
    lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"])
    lims.check_version()
    process = Process(lims,id= args[ "stepID" ])

    InputSamples = getInputSamples(process)

    printLabel(InputSamples)

if __name__ == "__main__":
    main()
