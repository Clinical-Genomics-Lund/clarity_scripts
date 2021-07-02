import sys
import re
import getopt
import glsapiutil
import datetime
import os
from subprocess import call


now = datetime.datetime.now()
HOSTNAME = 'https://clarity-test.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"

def main():
    filename = '/all/PrintTest.zpl'
    f = open(filename, 'w+')
    
    f.write('^XA\n^BY3.0,1,38\n^FO50,0\n^BQN,2,3\n^FDMM,_' + 'TESTsample1' + '^FS\n^FO125,33^ADN,27,15^FD' + 'TESTsample1' + '^FS\n^FO125,70^ADN,20,10^FD' + 'BarcodeTest' + '^FS\n^FO125,93^ADN,20,10^FD' + '20180216' + '^FS\n^XZ')
    f.close()
    call( ['lp','-d','ZebraLabCMD','-o','raw',filename])
    os.remove(filename)
    
if __name__ == "__main__":
    main()
