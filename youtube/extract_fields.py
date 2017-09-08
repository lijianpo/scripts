#encoding=utf-8
import sys
import json
import re
import os

reload(sys)
sys.setdefaultencoding('utf-8')

if len(sys.argv) == 1:
    print "python thisscript.py inputdir outputdir id,duration,tags,title,description,channelid"
    sys.exit(1)

inputdir = sys.argv[1]
outputdir = sys.argv[2]
fields = sys.argv[3]

support_fields = ["duration", "id", "title", "description", "channelid", "tags"]
field_list = fields.split(",")
for field in field_list:
    if field in support_fields:
        continue
    print "Unsupported field: [%s]" % field    
    sys.exit(1)

inputfiles = os.listdir(inputdir)

if not os.path.isdir(outputdir):
    os.makedirs(outputdir)

for infile in inputfiles:
    lastkey = ""
    count = 0
    feature_list = []
    youtubeinfofile = os.path.join(inputdir, infile)
    targetfile = os.path.join(outputdir, infile)
    with open(youtubeinfofile) as f:
        for line in f:
            feature = []
            if len(line) > 1 and line[0] == '#':
                lastkey = line.strip()[1:]
                continue
            count += 1
            jsonstring = json.loads(line.strip())
            items = jsonstring.get("items", [])
            if len(items) == 1:
                for field in field_list:
                    if field == "id":
                        vid = items[0].get("id", {})
                        feature.append(str(vid))
                    elif field == "duration":
                        duration = items[0].get("contentDetails", {}).get("duration", {})
                        duration_str = str(duration)
                        if duration_str.find("PT") != 0:
                            print "duration format error. [%s]" % lastkey
                            duration_str = "-1"
                        duration_str = duration_str.replace("PT", "").replace("H", "*3600+").replace("M", "*60+").replace("S", "*1+") + "0"
                        feature.append(str(eval(duration_str)))
                    elif field == "title":
                        title = items[0].get("snippet", {}).get("title", {})
                        feature.append(str(title))
                    elif field == "description":
                        description = items[0].get("snippet", {}).get("description", {})
                        feature.append(str(description).replace("\n", "").replace("\t", ""))
                    elif field == "channelid":
                        channelid = items[0].get("snippet", {}).get("channelId", {})
                    elif field == "tags":
                        tags = items[0].get("snippet", {}).get("tags", [])
                        taglist = []
                        for tag in tags:
                            taglist.append(str(tag).replace("\n", " ").replace("\r", " "))
                        feature.append(",".join(taglist))
                    else:
                        print "Unsupported field: [%s]\n" % field
            else:
                print "Found no item, the video may be removed. -- [%s]\n" % lastkey
                feature.append(lastkey)
            feature_list.append("\t".join(feature))
        
    with open(targetfile, "w") as f:
        for line in feature_list:
            f.write("%s\n" % line)
