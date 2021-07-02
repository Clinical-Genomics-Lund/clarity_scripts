from datetime import datetime
myFile = open('/opt/gls/clarity/customextensions/clarityDashboard/append.txt', 'a')
myFile.write('\nAccessed on ' + str(datetime.now()))
