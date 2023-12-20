import json
import requests
import sqlite3

NVD_URL_BASE = "https://services.nvd.nist.gov/rest/json/cve/1.0/"
SRTOOL_DB = "/temp/" # ask estape if sqlite file is needed

def nvd(cve_number):
    print('retreiving CVE data from NVD: '+cve_number)
    return

    ''' extract from nvd resources'''
    # As-is, needs to be refactored
    temp = ()
    outfile = 'tmp/' + cve_number + '.json'
    url = NVD_URL_BASE + cve_number
    print(f'Fetching {url}')
    try:
        # Request
        r = requests.get(url=url)

        if r.status_code == 200:
            # Extracting data in json format
            data = r.json()
            f = open(outfile, "w")
            f.write(json.dumps(data, indent=4, sort_keys=True))
            f.close()
            print('file saved: ' + outfile)
            desc = data["result"]["CVE_Items"][0]["cve"]["description"]["description_data"][0]["value"]
            if "baseMetricV2" in data["result"]["CVE_Items"][0]["impact"]:
                impact_v2 = data["result"]["CVE_Items"][0]["impact"]["baseMetricV2"]["cvssV2"]["baseScore"]
            else:
                impact_v2 = 0

            if "baseMetricV3" in data["result"]["CVE_Items"][0]["impact"]:
                impact_v3 = data["result"]["CVE_Items"][0]["impact"]["baseMetricV3"]["cvssV3"]["baseScore"]
            else:
                impact_v3 = 0

            #print(f'> {cve_number}\nDescription:\t{desc}\nImpact V2:\t{impact_v2}\nImpact V3:\t{impact_v3}')
            print(f'> {cve_number};{desc};{impact_v2};{impact_v3}')

            refs=data["result"]["CVE_Items"][0]["cve"]["references"]["reference_data"]
            extra_desc = ""
            counter = 0
            for ref in refs:
                counter += 1
                extra_desc += "\nURL:["+str(counter)+"]" + ref["url"]

            if impact_v3:
                temp = (desc+extra_desc, impact_v3)
                #return desc+extra_desc, impact_v3

            else:
                temp = (desc+extra_desc, impact_v3)
                #return desc+extra_desc, impact_v2`

    except Exception as ex:
        print(f'ERROR:\t{ex}')

    if len(temp) == 0:
        print(f'Alert:\t{cve_number} not found')
        
    return temp

def srtool(cve_number):
    temp = ()
    
    try:
        conn = sqlite3.connect(SRTOOL_DB)
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM orm_cve WHERE orm_cve.name=\'{cve_number}\'')
        rows = cur.fetchall()
        if len(rows) > 0:
            cve_temp = rows[0]
            print(f'> {cve_number}\nDescription:\t{cve_temp[12]}\nImpact V2:\t{cve_temp[19]}\nImpact V3:\t{cve_temp[17]}')
            score = cve_temp[19]
            if score == '':
                score = cve_temp[17]

            temp = (cve_temp[12], score)

    except Exception as ex:
        print(f'ERROR:\t{ex}')

    if len(temp) == 0:
        print(f'Alert:\t{cve_number} not found')

    return temp