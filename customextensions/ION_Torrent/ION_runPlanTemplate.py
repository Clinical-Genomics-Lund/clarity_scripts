import re
import sys
import httplib2
import json

def updateTorrentRunPlanLiqBi( shortID, tubeLabel, torrentServer, sampleData, workflow_LiqBi, project ):
    #Set host server
    if torrentServer == "S5Prime" :
        torrent_host = 'http://10.0.224.67/'
        bed = "/results/uploads/BED/19/hg19/unmerged/detail/Oncomine_Lung_cfDNA.07112017.Designed.bed"
        hotspot = "/results/uploads/BED/20/hg19/unmerged/detail/Oncomine_Lung_cfDNA.07112017.Hotspots.bed"

    elif torrentServer == "S5" :
        torrent_host = 'http://10.0.224.62/'
        bed = "/results/uploads/BED/29/hg19/unmerged/detail/Oncomine_Lung_cfDNA.07112017.Designed.bed"
        hotspot = "/results/uploads/BED/28/hg19/unmerged/detail/Oncomine_Lung_cfDNA.07112017.Hotspots.bed"

    else :
        print "Torrent Server must be S5Prime or S5"
        sys.exit(255)
        
    h = httplib2.Http()
    h.add_credentials('ionadmin', 'ionadmin')
    headers = {"Content-type": "application/json","Accept": "application/json"}
    
    # Get all planned experiments
    resp, content = h.request(torrent_host + '/rundb/api/v1/plannedexperiment/', "GET" )
    cont = json.loads( content )

    # Find the URI for the one with the specified planShortID
    plan_uri = "NOT_SET"
    for plan in cont["objects"]:
        if plan["planShortID"] == shortID:
            plan_uri = plan["resource_uri"]
            break

    # Get the data for that plan
    resp, content = h.request( torrent_host + plan_uri, "GET" )
    plan_dict = json.loads( content )

    # Change values
    plan_dict["bedfile"] = bed
    plan_dict["sampleTubeLabel"] = tubeLabel
    plan_dict["planStatus"] = "pending"

    #Update the content in "barcodedSamples"
    for sample in plan_dict["barcodedSamples"].keys():
        
        for bc in  plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"].keys():

            sampleName = sampleData[bc][3] + '_' + sampleData[bc][0] + '_' + sampleData[bc][4]
            sampleName = sampleName.decode('unicode-escape')
            
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["reference"] = "hg19"
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["targetRegionBedFile"] = bed
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["nucleotideType"] = "DNA"
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["hotSpotRegionBedFile"] = hotspot
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["externalId"] = sampleName
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["endBarcode"] = u''
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["controlType"] = u''
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["sseBedFile"] = u''

            plan_dict["barcodedSamples"][sampleName] = plan_dict["barcodedSamples"][sample].copy()
            del plan_dict["barcodedSamples"][sample]

    del plan_dict["selectedPlugins"]["IonReporterUploader"]["userInput"]["userInputInfo"]
    plan_dict["selectedPlugins"]["IonReporterUploader"]["userInput"]["userInputInfo"] = []

    for bc in sampleData.keys() :
        sampleName = sampleData[bc][3] + '_' + sampleData[bc][0] + '_' + sampleData[bc][4]
        sampleName = sampleName.decode('unicode-escape')
        default_dict = { u'setid': str(sampleData[bc][6]).decode('unicode-escape'),
                         u'tag_isFactoryProvidedWorkflow' : u'true',
                         u'Workflow': u'Oncomine Lung Liquid Biopsy - w1.3 - DNA - Single Sample',
                         
                         }
                        
        plan_dict["selectedPlugins"]["IonReporterUploader"]["userInput"]["userInputInfo"].append(default_dict)

    #Update the plan with the new data
    resp, content = h.request( torrent_host + plan_uri + "?format=json", "PUT", json.dumps( plan_dict ) )

def updateTorrentRunPlanCL( shortID, tubeLabel, torrentServer, sampleData, workflow_CL, project ):
    #Set host server
    if torrentServer == "S5Prime" :
        torrent_host = 'http://10.0.224.67/'
        bed = "/results/uploads/BED/22/hg19/unmerged/detail/ColonLungV2.20140523.designed.bed"

    elif torrentServer == "S5" :
        torrent_host = 'http://10.0.224.62/'
        bed = "/results/uploads/BED/29/hg19/unmerged/detail/Oncomine_Lung_cfDNA.07112017.Designed.bed"

    else :
        print "Torrent Server must be S5Prime or S5"
        sys.exit(255)
        
    h = httplib2.Http()
    h.add_credentials('ionadmin', 'ionadmin')
    headers = {"Content-type": "application/json","Accept": "application/json"}
    
    # Get all planned experiments
    resp, content = h.request(torrent_host + '/rundb/api/v1/plannedexperiment/', "GET" )
    cont = json.loads( content )
        
    # Find the URI for the one with the specified planShortID
    plan_uri = "NOT_SET"
    for plan in cont["objects"]:
        if plan["planShortID"] == shortID:
            plan_uri = plan["resource_uri"]
            break

    # Get the data for that plan
    resp, content = h.request( torrent_host + plan_uri, "GET" )
    plan_dict = json.loads( content )
        
    # Change values
    plan_dict["bedfile"] = bed
    plan_dict["sampleTubeLabel"] = tubeLabel
    plan_dict["planStatus"] = "pending"

    #Update the content in "barcodedSamples"
    for sample in plan_dict["barcodedSamples"].keys():

        for bc in  plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"].keys():
                
                sampleName = sampleData[bc][3] + '_' + sampleData[bc][0] + '_' + sampleData[bc][4]
                sampleName = sampleName.decode('unicode-escape')
                
                plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["reference"] = "hg19"
                plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["targetRegionBedFile"] = bed
#                plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["hotSpotRegionBedFile"] = hotspot
                
                plan_dict["barcodedSamples"][sampleName] = plan_dict["barcodedSamples"][sample].copy()
                del plan_dict["barcodedSamples"][sample]
                    
    #Update the plan with the new data
    resp, content = h.request( torrent_host + plan_uri + "?format=json", "PUT", json.dumps( plan_dict ) )
    
def updateTorrentRunPlan( shortID, tubeLabel, torrentServer, sampleData, workflow_DR, workflow_D, workflow_R, project ):
    #Set host server
    if torrentServer == "pgm2" :
        torrent_host = 'http://10.0.224.53/'
        bed = {
            'DNA':  '/results/uploads/BED/37/hg19/unmerged/detail/Oncomine_Focus.20160219.designed.bed',
            'RNA': '/results/uploads/BED/37/hg19/unmerged/detail/Oncomine_Focus.20160219.designed.bed',
            'CF': '/results/uploads/BED/12/hg19/unmerged/detail/CFTRexon.20131001.designed.bed'}
        
        hotspot = {
            'DNA' : '/results/uploads/BED/41/hg19/unmerged/detail/Oncomine_Focus.20160219.hotspots.bed' }
        
    elif torrentServer == "S5" :
        torrent_host = 'http://10.0.224.62/'
        bed = {
            'DNA':  '/results/uploads/BED/12/hg19/unmerged/detail/Oncomine_Focus.20160219.designed.bed',
            'RNA': '/results/uploads/BED/12/hg19/unmerged/detail/Oncomine_Focus.20160219.designed.bed',
            'CF': '/results/uploads/BED/9/hg19/unmerged/detail/CFTRexon.20131001.designed.bed'}

        hotspot = {
            'DNA' : '/results/uploads/BED/16/hg19/unmerged/detail/Oncomine_Focus.20160219.hotspots.bed' }

    elif torrentServer == "S5Prime" :
        torrent_host = 'http://10.0.224.67/'
        bed = {
            'DNA':  '/results/uploads/BED/2/hg19/unmerged/detail/Oncomine_Focus.20160219.designed.bed',
            'RNA': '/results/uploads/BED/2/hg19/unmerged/detail/Oncomine_Focus.20160219.designed.bed',
            'CF': '/results/uploads/BED/3/hg19/unmerged/detail/CFTRexon.20131001.designed.bed'}
        
        hotspot = {
            'DNA' : '/results/uploads/BED/1/hg19/unmerged/detail/Oncomine_Focus.20160219.hotspots.bed' }

    else :
        print "Torrent Server must be either pgm2 , S5 or S5Prime"
        sys.exit(255)
        
    h = httplib2.Http()
    h.add_credentials('ionadmin', 'ionadmin')
    headers = {"Content-type": "application/json","Accept": "application/json"}

    # Get all planned experiments
    resp, content = h.request(torrent_host + '/rundb/api/v1/plannedexperiment/', "GET" )
    cont = json.loads( content )

    # Find the URI for the one with the specified planShortID
    plan_uri = "NOT_SET"
    for plan in cont["objects"]:
        if plan["planShortID"] == shortID:
            plan_uri = plan["resource_uri"]
            break

    # Get the data for that plan
    resp, content = h.request( torrent_host + plan_uri, "GET" )
    plan_dict = json.loads( content )

    # Change values
    plan_dict["bedfile"] = bed["DNA"]
    plan_dict["sampleTubeLabel"] = tubeLabel
    plan_dict["planStatus"] = "pending" 

    #Update the content in "barcodedSamples"
    for sample in plan_dict["barcodedSamples"].keys():

        for bc in  plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"].keys():
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["reference"] = "hg19"
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["targetRegionBedFile"] = bed[ sampleData[bc][2] ]
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["controlType"] = ""
            plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["sseBedFile"] = ""
            
            if (sampleData[bc][2] == "DNA" ) or (sampleData[bc][2] == "CF") :
                plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["nucleotideType"] = "DNA"
                if (sampleData[bc][2] == "DNA" ) :
                    plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["hotSpotRegionBedFile"] = hotspot[ sampleData[bc][2] ]
            else:
                if (sampleData[bc][2] == "RNA" ) :
                    plan_dict["barcodedSamples"][sample]["barcodeSampleInfo"][bc]["nucleotideType"] = "RNA"
                else:
                    print "The suffix after the sample name must be either DNA, RNA or CF"
                    sys.exit(255)
            if sampleData[bc][4] == "CF" :
                sampleName = sampleData[bc][3] + '_' + sampleData[bc][0]
            else:
                sampleName = sampleData[bc][3] + '_' + sampleData[bc][0] + '_' + sampleData[bc][4]

            sampleName = sampleName.decode('unicode-escape')
            plan_dict["barcodedSamples"][sampleName] = plan_dict["barcodedSamples"][sample].copy()
            del plan_dict["barcodedSamples"][sample]

    del plan_dict["selectedPlugins"]["IonReporterUploader"]["userInput"]["userInputInfo"]
    plan_dict["selectedPlugins"]["IonReporterUploader"]["userInput"]["userInputInfo"] = []

    for bc in sampleData.keys() :
        sampleName = sampleData[bc][3] + '_' + sampleData[bc][0] + '_' + sampleData[bc][4]
        sampleName = sampleName.decode('unicode-escape')
        default_dict = { u'Gender': u'',
                         u'NucleotideType': sampleData[bc][2].decode('unicode-escape'),
                         u'Relation': u'Self',
                         u'RelationRole': u'Self',
                         u'barcodeId': bc.decode('unicode-escape'),
                         u'biopsyDays': u'',
                         u'cancerType': u'',
                         u'cellularityPct': str(sampleData[bc][5]).decode('unicode-escape'),
                         u'cellNum': u'',
                         u'coupleID': u'',
                         u'embryoID': u'',
                         u'sample': sampleName,
                         u'sampleDescription': u'',
                         u'sampleExternalId': u'',
                         u'sampleName': sampleName,
                         u'setid': str(sampleData[bc][6]).decode('unicode-escape'),
                         }

        if sampleData[bc][2] == "CF" :
            default_dict[u'ApplicationType'] = u'UploadOnly'
            default_dict[u'NucleotideType'] = u'DNA'
            default_dict[u'tag_isFactoryProvidedWorkflow'] = None
            default_dict[u'Workflow'] = u''

        else :
            if sampleData[bc][7] == "Paired" :
                default_dict[u'ApplicationType'] = u'Oncomine_DNA_RNA_Fusion'
                default_dict[u'Relation'] = u'DNA_RNA'
                default_dict[u'tag_isFactoryProvidedWorkflow'] = u'true'
                default_dict[u'Workflow'] = workflow_DR.decode('unicode-escape')

            else:
                if sampleData[bc][2] == "DNA" :
                    default_dict[u'ApplicationType'] = u'Amplicon Low Frequency Sequencing'
                    default_dict[u'tag_isFactoryProvidedWorkflow'] = u'true'
                    default_dict[u'Workflow'] = workflow_D.decode('unicode-escape')
                if sampleData[bc][2] == "RNA" :
                    default_dict[u'ApplicationType'] = u'Oncomine_RNA_Fusion'
                    default_dict[u'Relation'] = u'SINGLE_RNA_FUSION'
                    default_dict[u'cellularityPct'] = str(sampleData[bc][5]).decode('unicode-escape')
                    default_dict[u'tag_isFactoryProvidedWorkflow'] = u'true'
                    default_dict[u'Workflow'] = workflow_R.decode('unicode-escape')

        plan_dict["selectedPlugins"]["IonReporterUploader"]["userInput"]["userInputInfo"].append(default_dict)

    #Update the plan with the new data
    resp, content = h.request( torrent_host + plan_uri + "?format=json", "PUT", json.dumps( plan_dict ) )
    
