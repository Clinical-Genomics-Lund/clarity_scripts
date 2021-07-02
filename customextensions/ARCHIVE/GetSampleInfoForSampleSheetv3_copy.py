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
        SampleProj_Description = "," + assay + "_" + name + "_" + pedigree + "_" + familyID + "_" + motherID + "_" + fatherID + "_" + sex + "_" + status + "_" + geneList + urgent


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
        SampleProj_Description = "," + assay + "_" + name + "_" + pedigree + "_" + familyID + "_" + motherID + "_" + fatherID + "_" + sex + "_" + status + "_" + geneList + application + urgent

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
        SampleProj_Description = "," + assay + "_" + name + "_" + analysis + "_" + pairedSample + "_" + groupID + "_" + sampleType + "_" + sex + "_" + geneList + "_" + department + urgent

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description


                            
def getMICROinfo(planID, DOM, Name, Index, sLimsID, sUDFs, instrument, kitVersion):

    SampleID = sLimsID + "_" + planID

    #Index Example: A701-A503 (ATCACGAC-TGTTCTCT)
    I7_ID = Index.split('-')[0]
    I5_ID = re.search(r'\-(.*)\s', Index).group(1)

    I7_Index = re.search(r'\((.*)\-', Index).group(1)
    I5_Index = re.search(r'[A|T|G|C]{8}\-(.*)\)', Index).group(1)

    if "NextSeq" in instrument or "MiniSeq" in instrument or "v1.5" in kitVersion:
        #Get reverse complement of Index 5
        complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
        I5_Index = "".join(complement.get(base, base) for base in reversed(I5_Index))

    #Get Species
    try :
        species = sUDFs["Species"] 
    except:
        print "Reference Genome (species) must be chosen for microbiology samples"
        sys.exit(255)

    #Sample Project and Description Field
    tokens = Name.split("_")    
    SampleProj_Description = ",microbiology_" + tokens[0] + "_" + species

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description




def getRNASEQinfo(planID, DOM, Name, Index, sLimsID, sUDFs, instrument, kitVersion):

    SampleID = sLimsID + "_" + planID

    #Index Example: A03 UD00001 (ATCACGAC-TGTTCTCT)
    I7_ID = Index.split(' ')[1]
    I5_ID = Index.split(' ')[1]
    
    I7_Index = re.search(r'\((.*)\-', Index).group(1)
    I5_Index = re.search(r'[A|T|G|C]{8}\-(.*)\)', Index).group(1)

    if "NextSeq" in instrument or "MiniSeq" in instrument or "v1.5" in kitVersion:
        #Get reverse complement of Index 5
        complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
        I5_Index = "".join(complement.get(base, base) for base in reversed(I5_Index))

    #fusioncatcher
    if "TruSeq Stranded mRNA - Fusion" in sUDFs["Analysis"] :
        Analysis = "rnaseq-fusion"
        
        if "Diagnosis" in sUDFs:
            if sUDFs["Diagnosis"] == "Annat" :
                Diagnosis = "other" 
            elif sUDFs["Diagnosis"] == u"Solid tumör" :
                Diagnosis = "solidtumor"
            else:
                Diagnosis = sUDFs["Diagnosis"]

            SampleProj_Description = ",rnaseq-fusion_" + Name + "_" + Diagnosis
        else:
            print "TruSeq Stranded mRNA - Fusion samples must have a value for Diagnosis"
            sys.exit(255)

    #bladderclassifier
    elif "TruSeq Stranded mRNA - Bladder" in sUDFs["Analysis"] :
        SampleProj_Description = ",rnaseq-bladder_" + Name + "_rnaseq-bladder"

    #alignment and STAR
    else:
        SampleProj_Description = ",rnaseq_" + Name + "_rnaseq"

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description




def getNIPTinfo(planID, DOM, Name, Index, sLimsID, instrument):

    SampleID = sLimsID + "_" + planID

    #Index example: A1 p704-p504 (CACCGGGA-CGATATGA)
    p7p5 = Index.split(' ')[1]
    I7_ID = p7p5[0:2] + "-" + p7p5[2:4]
    I7_ID = p7p5[5:7] + "-" + p7p5[7:9]
    I7_Index = re.search(r'\((.*)\-', Index).group(1)
    I5_Index = re.search(r'[A|T|G|C]{8}\-(.*)\)', Index).group(1)

    if "NextSeq" in instrument or "MiniSeq" in instrument:
        #Get reverse complement of Index 5
        complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
        I5_Index = "".join(complement.get(base, base) for base in reversed(I5_Index))

    #Sample Project and Description Field
    SampleProj_Description = "NIPT,nipt_" + Name

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description





def getMYELOIDinfo(planID, DOM, Name, Index, sLimsID, sUDFs, instrument):

    DiagnosisDict = { "Hematologisk neoplasi" : "AML" ,
                      "KLL" : "KLL",
                      "MPN" : "MPN" , 
                      "Annat" : "Annat", 
                      "Hematologisk neoplasi efter transplantation" : "AlloSCT" }

    #Index Example: A701-A503 (ATCACGAC-TGTTCTCT)
    I7_ID = Index.split('-')[0]
    I5_ID = re.search(r'\-(.*)\s', Index).group(1)

    I7_Index = re.search(r'\((.*)\-', Index).group(1)
    I5_Index = re.search(r'[A|T|G|C]{8}\-(.*)\)', Index).group(1)

    if "NextSeq" in instrument or "MiniSeq" in instrument:
        #Get reverse complement of Index 5
        complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
        I5_Index = "".join(complement.get(base, base) for base in reversed(I5_Index))

    #Get Tumor/Normal
    if "normal" in sUDFs["Sample Type"] :
        SampleType = "N"
    elif "malignitet" in sUDFs["Sample Type"] :
        SampleType = "T"
    else:
        print "The Sample Type field of the Myeloid samples must contain either Vavnadsbiopsi normal or Hematologisk malignitet"
        sys.exit(255)

    #Get Diagnosis
    try:
        Diagnosis = DiagnosisDict[sUDFs["Diagnosis"]]
    except :
        print "Sample Diagnosis must be either Hematologisk neoplasi, KLL, MPN, Annat or Hematologisk neoplasi efter transplantation for the Myeloid samples"
        sys.exit(255)

    #Get paired/unpaired information
    if "Myeloisk Panel - Parad" in sUDFs["Analysis"] :
        Analysis = "paired"
        try :
            PairedSample = sUDFs["Paired Sample Name"]
        except: 
            print "Paired samples must have a value for 'Paired Sample Name'" 
            sys.exit(255)
    elif "Myeloisk Panel - Oparad" in sUDFs["Analysis"] :
        Analysis = "unpaired"
        PairedSample = "X"
    else :
        print "Analysis must be either 'Myeloisk Panel - Parad' or 'Myeloisk Panel - Oparad'"
        sys.exit(255)

    #Get Panel from appended workflow-specific container identifier
    #CAN2 == Nextera, LNP == TruSight Myeloid
    tokens = Name.split("_")
    if tokens[1] == 'CAN2' :
        SampleID = sLimsID + "_N_" + planID
        if PairedSample == "X":
            #Unpaired
            SampleProj_Description = ",myeloid_N" + tokens[0] + "_" + Analysis + "_" + PairedSample + "_" + SampleType + "_" + Diagnosis
        else:
            #Paired
            SampleProj_Description = ",myeloid_N" + tokens[0] + "_" + Analysis + "_N" + PairedSample + "_" + SampleType + "_X"

    elif tokens[1] == 'LNP' :
        SampleID = sLimsID + "_" + planID
        if PairedSample == "X":
            #Unpaired 
            SampleProj_Description = ",myeloid_" + tokens[0] + "_" + Analysis + "_" + PairedSample + "_" + SampleType + "_" + Diagnosis
        else: 
            #Paired
            SampleProj_Description = ",myeloid_" + tokens[0] + "_" + Analysis + "_" + PairedSample + "_" + SampleType + "_X"
    else :
        print "The workflow identifiers 'CAN2' or 'LNP' must be appended to the Library name"
        sys.exit(255)

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description



                
def getEXOMEinfo(planID, DOM, Name, Index, sLimsID, sUDFs, instrument):

    SampleID = sLimsID + "_" + planID

    #Index Example: A01 (GTCTGTCA)
    I7_ID = Index.split(' ')[0]
    I5_ID = "MolBC"
    
    I7_Index = re.search(r'\s\((.*)\)$', Index).group(1)
    I5_Index = "NNNNNNNNNN"
#    if "NextSeq" in instrument or "MiniSeq" in instrument:
#        #Get reverse complement of Index 5
#        complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
#        I5_Index = "".join(complement.get(base, base) for base in reversed(I5_Index))

    #Sample Project and Description Field examples
    #Trio : exome_3901-15_3901-15_proband_M_affected_pediatrics
    #Single : exome_3213-16_X_X_M_affected_ahus
    #Tumor : exome-tumor_8776-17_paired_8775-17_T_F_neuroblastom
    #BRCA unpaired:
    #BRCA paired:
    
    DiagnosisDict = { "Pediatrik" : "pediatrics" ,
                      "Annat" : "other" , 
                      "aHUS" : "ahus" , 
                      "complement" : "complement" , 
                      "HAE" : "HAE"}

    if "Diagnosis" in sUDFs:
        try : 
            Application = DiagnosisDict[sUDFs["Diagnosis"]] 
        except: 
            print "The diagnosis field must contain either aHUS, complement, Annat or Pediatrik"
            sys.exit(255)

    else:
        if "Tumor" in sUDFs["Analysis"]:
            Application = "other"
        elif "BRCA" in sUDFs["Analysis"] :
            Application = "BRCA"
        elif "CTG" in sUDFs["Analysis"] :
            Application = ""

        elif "Gene list" in sUDFs :

            geneLists = { "Kanalopati" : "Kanalopati" ,
                          "Komplex kardiologi" : "Komplex-kardiologi" ,
                          "Kardiomyopati" : "Kardiomyopati", 
                          "RASopati" : "RASopati" ,
                          "PAH HHT CM-AVM" : "PAH-HHT-CM-AVM" ,
                          "Anpassad" : "Anpassad" , 
                          "Stroke" : "Stroke" , # by Viktor
                          "CMT/Neuropati" : "cmt-neuropati", 
                          "Ataxi" : "ataxi", 
                          "Osteogenesis imperfecta" : "Osteogenesis-imperfecta",
                          u"Bindvävssjukdomar" : "Bindvavssjukdomar",
                          u"Hörselnedsättning" : "Horselnedsattning" ,
                          u"Hereditär Spastisk Parapares" : "hsp" 
                          }

            #More than one gene list
            if "," in sUDFs["Gene list"] :
                tmp = []
                Genelist = sUDFs["Gene list"].split(", ")
                for Glist in Genelist :
                    try : 
                        tmp.append( geneLists[ Glist ] )
                    except:
                        print "The gene list field must contain one of the following option: Kanalopati,Bindv:avssjukdomar,Komplex kardiologi,Kardiomyopati,RASopati, H:orselneds:attning, Anpassad, PAH HHT CM-AVM, CMT/Neuropati, Stroke, Hereditar Spastisk Parapares or Ataxi. If more than one gene lists are used, please use ',' as seperator."
                        sys.exit(255)

                tmp = ("+").join(tmp)
                Application =  tmp

            #Only one gene list
            else :
                try:
                    Application = geneLists[ sUDFs["Gene list"] ]
                except:
                    print "The gene list field must contain one of the following option: Kanalopati,Bindv:avssjukdomar,Komplex kardiologi,Kardiomyopati,RASopati, H:orselneds:attning, Anpassad, PAH HHT CM-AVM, CMT/Neuropati, Stroke, Hereditar Spastisk Parapares or Ataxi."
                    sys.exit(255)


    if ( (sUDFs["Analysis"] == "SureSelectXTHS - Trio Exome") or (sUDFs["Analysis"] == "SureSelectXTHS - Single Exome") or (sUDFs["Analysis"] == "SureSelectXTHS - Paired Tumor Exome")or (sUDFs["Analysis"] == "SureSelectXTHS - Unpaired Tumor Exome") ):

        #For these samples, gender must be indicated
        if "Sex" in sUDFs:
            if sUDFs["Sex"] == "Man":
                sex = "M"
            elif sUDFs["Sex"] == "Kvinna":
                sex = "F"
            elif sUDFs["Sex"] == u"Okänt" :
                sex = "U"
            else :
                print "Man, Kvinna or Okant must be indicated for the SureSelect XTHS samples"
                sys.exit(255)
        else :
            print "Man, Kvinna or Okant must be indicated for the SureSelect XTHS samples"
            sys.exit(255)


        #Check the Trio samples
        if sUDFs["Analysis"] == "SureSelectXTHS - Trio Exome" :
        
            if "Sample Type" in sUDFs:
                if sUDFs["Sample Type"] == "Frisk":
                    Type = "unaffected"
                elif sUDFs["Sample Type"] == "Sjuk" :
                    Type = "affected"
                else:
                    print "The Sample Type field must contain either Sjuk or Frisk"
                    sys.exit(255)
            else :
                print "The Sample Type field must contain either Sjuk or Frisk for trio samples"
                sys.exit(255)


            if "Pedigree" in sUDFs:
                pedigree = sUDFs["Pedigree"]
                if pedigree == "Mamma":
                    pedigree = "mother"
                elif pedigree == "Pappa":
                    pedigree = "father"
                elif pedigree == "Proband" :
                    pedigree = "proband"
                elif pedigree == "Annat":
                    pedigree = "other"
                else :
                    print "The pedigree must be either Mamma, Pappa, Proband or Annat for the SureSelect XTHS samples"
                    sys.exit(255)
            else :
                print "The pedigree must be either Mamma, Pappa, Proband or Annat for the SureSelect XTHS samples"
                sys.exit(255)
        
            SampleProj_Description = ",exome_" + Name + "_" + sUDFs["FamilyID"] + "_" + pedigree + "_" + sex + "_" + Type + "_" + Application

        #Single samples
        elif sUDFs["Analysis"] == "SureSelectXTHS - Single Exome" :
            SampleProj_Description = ",exome_" + Name + "_" + "X" + "_" + "X" + "_" + sex + "_affected_" + Application

        #Tumor Samples
        elif "Tumor" in sUDFs["Analysis"]:
            #Get paired/unpaired information
            if "Paired Tumor Exome" in sUDFs["Analysis"] :
                Analysis = "paired"
                try: 
                    PairedSample = sUDFs["Paired Sample Name"]
                except:
                    print "Paired Sample Name must be indicated for paired tumor samples" 
                    sys.exit(255)
            else :
                Analysis = "unpaired"
                PairedSample = "X"

            #Get Tumor/Normal
            try : 
                SampleType = sUDFs["Sample Type"][:1]
            except:
                print "The Sample Type field of the SureSelect Tumor samples must contain either 'Normalprov' or 'Tumorprov'"
                sys.exit(255)

            #Get department for Coyote
            department = sUDFs["Department"].replace(" ", "") 

            SampleProj_Description = ",exome-tumor_" + Name + "_" + Analysis + "_" + PairedSample + "_" + SampleType + "_" + sex + "_" + Application + "_" + department

    elif ("BRCA" in sUDFs["Analysis"] ) :
        #BRCA samples

        #Get Tumor/Normal
        try :
            SampleType = sUDFs["Sample Type"][:1]
        except:
            print "The Sample Type field of the BRCA samples must contain either 'Normalprov' or 'Tumorprov'"
            sys.exit(255)

        #Get paired/unpaired information
        if "Paired BRCA" in sUDFs["Analysis"] :
            Analysis = "paired"
            try:
                PairedSample = sUDFs["Paired Sample Name"]
            except:
                print "Paired Sample Name must be indicated for paired BRCA samples"
                sys.exit(255)

        else :
            Analysis = "unpaired"
            PairedSample = "X"


        #Get tissue
        Tissue = "X"
        if "Tissue" in sUDFs.keys():
            if sUDFs["Tissue"] == "FFPE":
                Tissue = "FFPE"

        SampleProj_Description = ",brca_" + Name + "_" + Analysis + "_" + PairedSample + "_" + SampleType + "_" + Application + "_" + Tissue

    elif ("CTG" in sUDFs["Analysis"] ) :
        #CTG exome samples
        SampleProj_Description = ",exome-ctg_" + Name #+ "_" + Application

    else:
        print "Trio, Single, Tumor, CTG or BRCA must be indicated in the analysis field for the SureSelect XTHS samples"
        sys.exit(255)

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description
