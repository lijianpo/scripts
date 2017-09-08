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
    print "python thisscript.py youtube_id_path.txt apikey_path.txt target_dir"
    sys.exit(1)

youtube_id_path = sys.argv[1]
apikey_path = sys.argv[2]
target_dir = sys.argv[3]

def get_workfile(rootpath, order):
    s = "%06d" % order
    current_file = os.path.join(rootpath, s + ".txt")
    return current_file

apikey_list = []
apikey_dict = {}
idx = 0

def get_apikey():
    global idx
    while idx < len(apikey_list):
        if apikey_dict[apikey_list[idx]] < (1000000 - 20000):
            apikey_dict[apikey_list[idx]] += 7
            return (True, apikey_list[idx])
        else:
            idx += 1
    return (False, "NULL")
    
def dump_apikey():
    with open(apikey_path, "w") as f:
        for i in xrange(0, len(apikey_list)):
            vkey = apikey_list[i]
            vquota = apikey_dict[vkey]
            if i == idx:
                vquota += 700
            f.write("%s\t%d\n" % (vkey, vquota))
        
ids = []
with open(youtube_id_path, "r") as f:
    for line in f:
        ids.append(line.strip())
        
total = len(ids)
print "Total: %d ids.\n" % total

# Load key file
with open(apikey_path, "r") as f:
    for line in f:
        keys = line.strip().split('\t')
        if len(keys) != 2: continue
        apikey, quato_ = keys[0], keys[1]
        apikey_list.append(apikey)
        apikey_dict[apikey] = int(quato_)

# Load processed keys, ignore them
processed_ids = {}
max_file_order = 0
if os.path.isdir(target_dir):
    filelist = os.listdir(target_dir)
    for f in filelist:
        abspath = os.path.join(target_dir, f)
        with open(abspath, "r") as fd:
            for line in fd:
                if len(line) >= 9 and len(line) < 15 and line[0] == '#':
                    vid = line.strip()[1:]
                    processed_ids[vid] = 1
    filenumlist = [int(f[:-4]) for f in filelist]
    max_file_order = max(filenumlist)
else:
    os.makedirs(target_dir, 0755)
        
count = 0
keyused = 0
processed_list = []
max_file_order += 1
for vid in ids:
    if processed_ids.has_key(vid):
        count += 1
        print "Processing %d/%d, dumplited id: [%s]\n" % (count, total, vid)
        continue
    keyvalied, quatokey = get_apikey()
    if not keyvalied:
        print "Don't have any valied keys."
        break
    response = urllib.urlopen("https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id=%s&key=%s" % (vid, quatokey))
    httpcode = response.getcode()
    jsonstr = "NULL"
    if httpcode != 200:
        print "Bad http code: %d, [%s]\n" % (httpcode, vid)
    else:
        jsonstr = response.read().replace("\n", "")
    processed_list.append("#%s\n%s" % (vid, jsonstr))
    processed_ids[vid] = 1

    count += 1
    keyused += 1
    
    print "Processed %d/%d ids.\n" % (count, total)
    if keyused % 100 == 0:
        current_file = get_workfile(target_dir, max_file_order)
        with open(current_file, "a") as f:
            for line in processed_list:
                f.write("%s\n" % line)
        processed_list = []
        print "=================="
        for apikey in apikey_list:
            print "%s\tused %d quotas" % (apikey, apikey_dict[apikey])
        print "==================\n"
        dump_apikey()
    if keyused % 50000 == 0:
        max_file_order += 1

if processed_list:
    current_file = get_workfile(target_dir, max_file_order)
    with open(current_file, "a") as f:
        for line in processed_list:
            f.write("%s\n" % line)
    processed_list = []
