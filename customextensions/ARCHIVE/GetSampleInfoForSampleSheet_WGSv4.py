#-*- coding: utf-8 -*-
import re
import sys

def getWGSinfo(planID, DOM, Name, Index, sLimsID, sUDFs, instrument, kitVersion):
    Name = Name.replace("_", "-")
    Name = Name.replace(" ", "-")
    Name = Name.replace(".", "-")
    Name = Name.replace("/", "-")

    SampleID = sLimsID + "_" + planID
    
    #Index Example: "D09 UDI0068 (CCTTCACC-GACGCTCC)"
    I7_ID = Index.split(' ')[1]
    I5_ID = Index.split(' ')[1]
    
    I7_Index = re.search(r'\((.*)\-', Index).group(1)
    I5_Index = re.search(r'[A|T|G|C]{8}\-(.*)\)', Index).group(1)
    
    if "NextSeq" in instrument or "MiniSeq" in instrument or "v1.5" in kitVersion:
        #Get reverse complement of Index 5
        complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
        I5_Index = "".join(complement.get(base, base) for base in reversed(I5_Index))

    #Sample Project and Description Field examples
    #Family :wgs-family_4224-12_proband_4224-12_4225-12_4226-12_M_affected_pediatrics 
    #Single : wgs-single_3529-19_proband_3529-19_X_X_M_affected_bla
    #Tumor : wgs-somatic_9091-19_unpaired_X_T_M_other_KliniskGenetik

    changeDict = { "Kvinna" : "F", 
                   "Man" : "M",
                   u"Okänt" : "U" , 
                   "Sjuk" : "affected", 
                   "Frisk" : "unaffected", 
                   "Pediatrik" : "pediatrics" ,
                   "Annat" : "other" ,
                   "aHUS" : "ahus" ,
                   "HAE" : "HAE" , 
                   "complement" : "complement", 
                   "Kanalopati" : "Kanalopati" ,
                   "Komplex kardiologi" : "Komplex-kardiologi" ,
                   "Kardiomyopati" : "Kardiomyopati",
                   "RASopati" : "RASopati" ,
                   "PAH HHT CM-AVM" : "PAH-HHT-CM-AVM" ,
                   "Anpassad" : "Anpassad" ,
                   u"Stroke" : "Stroke" , 
                   "CMT/Neuropati" : "cmt-neuropati",
                   "Ataxi" : "ataxi",
                   "Osteogenesis imperfecta" : "Osteogenesis-imperfecta",
                   u"Bindvävssjukdomar" : "Bindvavssjukdomar",
                   u"Hörselnedsättning" : "Horselnedsattning" ,
                   u"Hereditär Spastisk Parapares" : "hsp", 
                   "Neurodegeneration" : "Neurodegeneration" , 
                   u"Medfött hjärtfel" : "Medfott-hjartfel", 
                   "Hematologisk malignitet" : "hemato", 
                   u"Solid tumör" : "solid", 
                   u"Ofullständig trio" : "Ofullstandig-trio"
                   }
    
    #Set priority
    urgent = ""
    if "Urgent" in sUDFs:
        if sUDFs["Urgent"] == "Ja" : 
            urgent = "_highest"

    #Get somatic or constitutional:
    if "family" in sUDFs["Analysis"]:

        #Get reference genome version (hg19 until ~2020-03)
        referenceGenome = sUDFs["Reference genome"]
        if referenceGenome == "" :
            print "Reference genome must be indicated"
            sys.exit(255)
        else:
            if referenceGenome == "hg19" :
                assay = "wgs"
            if referenceGenome == "hg38" :
                assay = "wgs-hg38"
#        assay = "wgs-family" 

        name = Name

        try: 
            pedigree = sUDFs["Pedigree"]
            familyID = sUDFs["FamilyID"]
            sex = sUDFs["Sex"]
            status = sUDFs["Sample Type"] 
        except : 
            print "Pedigree, FamilyID, Sex and Sample Type must be indicated for WGS family samples" 
            sys.exit(255) 

        if "Proband" in sUDFs["Pedigree"] :
            pedigree = "proband"
        else: 
            pedigree = "relative"

        try:
            motherID = sUDFs["MotherID"]
        except : 
            motherID = "X"

        try: 
            fatherID = sUDFs["FatherID"]
        except:
            fatherID = "X"

        sex = changeDict[ sUDFs["Sex"] ]
        status = changeDict[ sUDFs["Sample Type"] ]
        geneList = "other" #not relevant for family samples

        if "Topup read count" in sUDFs :
            assay = assay + "-topup"
        SampleProj_Description = assay + "_" + name + "_" + pedigree + "_" + familyID + "_" + motherID + "_" + fatherID + "_" + sex + "_" + status + "_" + geneList + urgent


    elif "single" in sUDFs["Analysis"] :
#        wgs-single_3529-19_proband_3529-19_X_X_M_affected_bla
        #Get reference genome version (hg19 until ~2020-03)
        referenceGenome = sUDFs["Reference genome"]
        if referenceGenome == "" :
            print "Reference genome must be indicated"
            sys.exit(255)
        else:
            if referenceGenome == "hg19" :
                assay = "wgs"
            if referenceGenome == "hg38" :
                assay = "wgs-hg38"
#        assay = "wgs-single" 

        name = Name
        pedigree = "proband" 
        familyID = Name
        motherID = "X"
        fatherID = "X"
        
        try : 
            sex = changeDict[ sUDFs["Sex"] ]
        except: 
            print "Sex must be indicated for WGS single samples" 
            sys.exit(255)
        
        status = "affected" 

        if "Gene list" in sUDFs.keys() : 
            try: 
                geneList = changeDict[sUDFs["Gene list"] ]

            except: 
                if "," in sUDFs["Gene list"] :
                    tmp = []
                    Genelist = sUDFs["Gene list"].split(", ")
                    
                    for Glist in Genelist :
                        try :
                            tmp.append( changeDict[ Glist ] )
                        except:
                            print "The gene list field is not recognized"
                            sys.exit(255)

                    tmp = ("+").join(tmp)
                    geneList =  tmp
            application = ""

        elif sUDFs["Diagnosis"] :
            geneList = "other" 
            try: 
                application = changeDict[sUDFs["Diagnosis"] ]
                application = "_" + application
            except: 
                print "The diagnosis field is not recognized"
                sys.exit(255)
        else: 
            application = "_other" 
        
        if "Topup read count" in sUDFs :
            assay = assay + "-topup"
        SampleProj_Description = assay + "_" + name + "_" + pedigree + "_" + familyID + "_" + motherID + "_" + fatherID + "_" + sex + "_" + status + "_" + geneList + application + urgent

    elif "somatic" in sUDFs["Analysis"]:
        #exome-tumor_9091-19_unpaired_X_T_M_other_KliniskGenetik
        assay = "wgs-somatic"
        name = Name

        #Get paired/unpaired information
        if "paired" in sUDFs["Analysis"] and "unpaired" not in sUDFs["Analysis"]:
            analysis = "paired"
            try:
                pairedSample = sUDFs["Paired Sample Name"]
                pairedSample = pairedSample.replace("_", "-")
                pairedSample = pairedSample.replace(" ", "-")
                pairedSample = pairedSample.replace(".", "-")
                pairedSample = pairedSample.replace("/", "-")
            except:
                print "Paired Sample Name must be indicated for paired tumor samples"
                sys.exit(255)
        else :
            analysis = "unpaired"
            pairedSample = "X"
                    
        #Get Tumor/Normal
        try :
            sampleType = sUDFs["Sample Type"][:1]
        except:
            print "The Sample Type field of the Tumor samples must contain either 'Normalprov' or 'Tumorprov'"
            sys.exit(255)

        #Get groupID 
        if sampleType == "T" :
            groupID = Name 
        elif sampleType == "N" :
            groupID = pairedSample

        try :
            sex = changeDict[ sUDFs["Sex"] ]
        except:
            print "Sex must be indicated for WGS single samples"
            sys.exit(255)
                        
        #Set genelist field
        geneList = "other"

        #Get department for Coyote
        department = sUDFs["Department"].replace(" ", "")
        
        if "Topup read count" in sUDFs :
            assay = assay + "-topup"
        SampleProj_Description = assay + "_" + name + "_" + analysis + "_" + pairedSample + "_" + groupID + "_" + sampleType + "_" + sex + "_" + geneList + "_" + department + urgent

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description
