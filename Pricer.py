import requests
import json
import time
import sys

# Vendor list harvested from the javascript on the GSA EIS WebPage.  These codes enable us to decode responses
Vendors = ["v5_att", "v6_verizon", "v8_level3", "v12_centurylink", "v23_harris", "v53_btfederal", "v71_mettel",
           "v72_granite", "v73_coretech", "v76_microtech"]


# functions for retrieving data from file
def getCsvValues(csvRow):
    """Split the row from the CSV file and return it as a list of values"""
    x = csvRow.split(",")
    return ([x[0].split("\n")[0], x[1].split("\n")[0]])


def readPricingInput(fileName):
    """Read pricing combinations from a file. This should be a CSV file. The return will be list of CLIN/NSC pairs"""
    dataValues = []
    pricingDataFile = open(fileName, "r")
    contents = pricingDataFile.readlines()
    pricingDataFile.close()
    for row in contents[1:]:
        dataValues.append(getCsvValues(row))
    return dataValues


# functions for working with GSA web site

# retrieve base page to establish session key
def getBaseWebPage():
    return requests.get("https://eis-public-pricer.nhc.noblis.org/unit-pricer/")


# verify the CLIN is good
def VerifyCLINData(clinCode):
    queryStr = "?service_id=all&q=" + clinCode + "&page=1&sort=name"
    r = requests.put("https://eis-public-pricer.nhc.noblis.org/ajax.php/clin-search/search" + queryStr)
    j = json.loads(r.text)
    # print (r.text)
    return str(j["rows"][0]["sets"][0]["btable_id"])


# verify NSC is good
def VerifyNSCData(nscCode):
    queryStr = "?type=80&q=" + nscCode
    r = requests.put("https://eis-public-pricer.nhc.noblis.org/ajax.php/unit-pricer/get_locs" + queryStr)
    # print (r.text)
    j = json.loads(r.text)
    return j["rows"][0]["id"]


# get the price info to a particular CLIN/NSC combo (currently only domestic)
def GetPriceData(clinCode, nscCode):
    queryStr = "?service_id=" + clinCode[
                                :2] + "&clin=" + clinCode + "&btable_id=2911&loc_orig=" + nscCode + "&dates=month"
    # print("https://eis-public-pricer.nhc.noblis.org/ajax.php/unit-pricer/price"+queryStr)
    r = requests.put("https://eis-public-pricer.nhc.noblis.org/ajax.php/unit-pricer/price" + queryStr)
    return r.text


# Main Program...
if len(sys.argv) < 3:
    print "Missing parameters"
    print "Usage:python Pricer.py <fully qualified input file name> <fully qualified output file name>"
    exit(-1)

print("StartTime:" + time.asctime(time.localtime(time.time())))

pricingFile = sys.argv[1]
resultsFile = sys.argv[2]
Data = readPricingInput(pricingFile)

r = getBaseWebPage()

outputFile = open(resultsFile, "w")
outputFile.write(
    "\"CLIN\",\"Origin\",\"Start Date\",\"Stop Date\",\"AT&T\",\"Verizon Federal\",\"Level 3\",\"CenturyLink\",\"Harris\",\"BT Federal\",\"MetTel\",\"Granite\",\"Core Technologies\",\"MicroTech\"\n")

for item in Data[:3]:
    print("CLIN: " + item[0] + " NSC:" + item[1])
    try:
        # VerifyCLINData(item[0])
        # VerifyNSCData(item[1])
        result = GetPriceData(item[0], item[1])
        js = json.loads(result)
        csvRow = "\"" + item[0] + "\",\"" + item[1] + "\","
        csvRow += "\"" + js["rows"][0]["date_start"] + "\","
        csvRow += "\"" + js["rows"][0]["date_stop"] + "\","
        for vendor in Vendors:
            try:
                csvRow += str(js["rows"][0]["prices"][vendor]["prices"][0])
            except:
                csvRow += "\"n/a\""
            csvRow += ","
        outputFile.write(csvRow[:-1] + "\n")
    except:
        print ("WARNING! Unable to process :" + item[0] + "," + item[1])

outputFile.close()

print("StopTime:" + time.asctime(time.localtime(time.time())))
