#/usr/bin/python
#coding=utf-8

import json
import sys
import os
import urllib
import pdb
import time

reload(sys)
sys.setdefaultencoding("utf-8")

if len(sys.argv) == 1:
    print "python this.py idfile.txt relatedidfile.txt apikeyfile.txt"
    sys.exit(1)

idfile_path = sys.argv[1]
relatedidfile_path = sys.argv[2]
apikeyfile_path = sys.argv[3]

apikey_list = []
apikey_dict = {}
apikey_idx = 0
def get_apikey():
    global apikey_idx
    while apikey_idx < len(apikey_list):
        if apikey_dict[apikey_list[apikey_idx]] < (1000000 - 20000):
            apikey_dict[apikey_list[apikey_idx]] += 102
            return (True, apikey_list[apikey_idx])
        else:
            apikey_idx += 1
    return (False, "NULL")
    
def dump_apikey():
    with open(apikeyfile_path, "w") as f:
        for i in xrange(0, len(apikey_list)):
            apikey = apikey_list[i]
            quotas = apikey_dict[apikey]
            if i == apikey_idx:
                quotas += (102 * 50)
            f.write("%s\t%d\n" % (apikey, quotas))

ids = []
with open(idfile_path, "r") as f:
    for line in f:
        ids.append(line.strip())
        
total = len(ids)
print "Total: %d ids.\n" % total

with open(apikeyfile_path, "r") as f:
    for line in f:
        keys = line.strip().split('\t')
        if len(keys) != 2: continue
        apikey, quotas = keys[0], keys[1]
        apikey_list.append(apikey)
        apikey_dict[apikey] = int(quotas)

processed_ids = {}
if os.path.exists(relatedidfile_path):
    with open(relatedidfile_path, "r") as f:
        for line in f:
            tokens = line.strip().split('\t')
            if len(tokens) != 2: continue
            vid, relatedvids = tokens[0], tokens[1]
            if not processed_ids.has_key(vid):
                processed_ids[vid] = len(relatedvids.split(','))
        
count = 0
keyused = 0
with open(relatedidfile_path, "a") as f:
    for vid in ids:
        #if processed_ids.has_key(vid) and processed_ids[vid] > 20:
        if processed_ids.has_key(vid):
            count += 1
            print "Processing %d/%d, dumplited id: [%s]\n" % (count, total, vid)
            continue
        keyvalied, quatokey = get_apikey()
        if not keyvalied:
            print "Don't have any valied keys."
            break
        response = urllib.urlopen("https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=25&relatedToVideoId=%s&type=video&key=%s" % (vid, quatokey))
        resinjson = json.loads(response.read())
        relatedids = []
        for search_result in resinjson.get("items", []):
            if search_result["id"]["kind"] == "youtube#video":
                relatedids.append(search_result["id"]["videoId"])
        if len(relatedids) == 0:
            relatedids.append("NULL")
            print "Empty related id: %s\n" % vid

        f.write("%s\t%s\n" % (vid, ",".join(relatedids)))
        processed_ids[vid] = len(relatedids)

        count += 1
        keyused += 1
        print "Processed %d/%d ids.\n" % (count, total)
        if keyused % 50 == 0:
            print "=================="
            for apikey in apikey_list:
                print "%s\tused %d quotas" % (apikey, apikey_dict[apikey])
            print "==================\n"
            dump_apikey()
