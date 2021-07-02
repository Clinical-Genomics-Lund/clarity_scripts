import sys
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString
import pprint

HOSTNAME = 'https://mtapp046.lund.skane.se'
BASE_URI = HOSTNAME + '/api/v2/'
def getSamples(uri) :

    xml = api.GET( uri )
    dom = parseString(xml)
    samples = dom.getElementsByTagName( "sample" )
    for sample in samples:
        sampleList.append(sample.getAttribute("limsid"))

    if dom.getElementsByTagName( "next-page" ):
        getSamples(dom.getElementsByTagName( "next-page" )[0].getAttribute("uri"))
                          
def main():
    global api
    global sampleList
    sampleList= []
    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( "apiuser", "LateDollarsState592")
    
    totalLimsIDs2017 = 0
    totalLimsIDs201709_201712 = 0
    totalNOTSequencedSamples201709_201712 = 0
    uniquePersonalIdentityNumbers = []

    personalIdentityNumber_Seqruns_LimsIDList = {}

    getSamples(HOSTNAME + "/api/v2/samples?udf.Analysis=Clarigo+NIPT+Analys&udf.Classification=Rutinprov&udf.Department=Klinisk+Genetik")
    xml = api.getSamples(sampleList)
    dom = parseString(xml)
    print len(sampleList)

    for sample in dom.getElementsByTagName("smp:sample") :
        if sample.getElementsByTagName("date-received")[0].firstChild.data.split("-")[0] == "2017":
            totalLimsIDs2017 += 1
            month = sample.getElementsByTagName("date-received")[0].firstChild.data.split("-")[1]
            if (month == "09") or (month == "10") or (month == "11") or (month == "12"):
                totalLimsIDs201709_201712 += 1

                SequencingRuns = int(api.getUDF(sample, "Sequencing runs"))
                if SequencingRuns == 0 :
                    totalNOTSequencedSamples201709_201712 += 1
                
                pIDnumber = api.getUDF(sample, "Personal Identity Number")
                if pIDnumber not in uniquePersonalIdentityNumbers :
                    uniquePersonalIdentityNumbers.append(api.getUDF(sample, "Personal Identity Number"))
                    personalIdentityNumber_Seqruns_LimsIDList[pIDnumber] = [SequencingRuns , [sample.getAttribute( "limsid" )] ]
                else:
                    personalIdentityNumber_Seqruns_LimsIDList[pIDnumber][0] += SequencingRuns
                    personalIdentityNumber_Seqruns_LimsIDList[pIDnumber][1].append(sample.getAttribute( "limsid" ))
                
    print "Total LimsIDs in 2017: " , totalLimsIDs2017
    print "Total LimsIDs in 201709-201712: ", totalLimsIDs201709_201712
    print "Total LimsIDs registered but not sequenced in 201709-201712: " , totalNOTSequencedSamples201709_201712
 
    print "Number of unique personal identity numbers registered in 201709-201712:" , len(uniquePersonalIdentityNumbers)

#    for pID in personalIdentityNumber_Seqruns_LimsIDList:
#        print personalIdentityNumber_Seqruns_LimsIDList[pID][0], pID, personalIdentityNumber_Seqruns_LimsIDList[pID][1]
    
    pID_summary = {}
    SeqRunsList = []
    for pIDnumber in personalIdentityNumber_Seqruns_LimsIDList :
        if personalIdentityNumber_Seqruns_LimsIDList[pIDnumber][0] in SeqRunsList :
            pID_summary[personalIdentityNumber_Seqruns_LimsIDList[pIDnumber][0]][0].append(pIDnumber) 
            for limsID in personalIdentityNumber_Seqruns_LimsIDList[pIDnumber][1]:
                pID_summary[personalIdentityNumber_Seqruns_LimsIDList[pIDnumber][0]][1].append(limsID)  
        else:
            SeqRunsList.append(personalIdentityNumber_Seqruns_LimsIDList[pIDnumber][0])
            pID_summary[personalIdentityNumber_Seqruns_LimsIDList[pIDnumber][0]] = [ [], []]
            pID_summary[personalIdentityNumber_Seqruns_LimsIDList[pIDnumber][0]][0].append(pIDnumber)
            for limsID in personalIdentityNumber_Seqruns_LimsIDList[pIDnumber][1]:
                pID_summary[personalIdentityNumber_Seqruns_LimsIDList[pIDnumber][0]][1].append(limsID)

    for number in pID_summary :
        print number, "Personal Identity Numbers: ", len(pID_summary[number][0])

if __name__ == "__main__":
    main()


