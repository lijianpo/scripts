#encoding=utf-8
import sys
import json
import re
import os

reload(sys)
sys.setdefaultencoding('utf-8')

if len(sys.argv) == 1:
    print "python thisscript.py inputdir outputdir id,duration,tags,title,description,channelid,viewCount,likeCount,dislikeCount [wanted_id]"
    sys.exit(1)

wanted_id_dict = {}
if len(sys.argv) == 5:
    with open(sys.argv[4]) as f:
        for line in f:
            line = line.strip()
            if not wanted_id_dict.has_key(line):
                wanted_id_dict[line] = 1
    
inputdir = sys.argv[1]
outputdir = sys.argv[2]
fields = sys.argv[3]

support_fields = ["duration", "id", "title", "description", "channelid", "tags", "viewCount", "likeCount", "dislikeCount"]
field_list = fields.split(",")
for field in field_list:
    if field in support_fields:
        continue
    print "Unsupported field: [%s]" % field    
    sys.exit(1)

inputfiles = os.listdir(inputdir)

if not os.path.isdir(outputdir):
    os.makedirs(outputdir)

count = 0
reason_dict = {}
for infile in inputfiles:
    lastkey = ""
    feature_list = []
    youtubeinfofile = os.path.join(inputdir, infile)
    targetfile = os.path.join(outputdir, infile)
    with open(youtubeinfofile) as f:
        for line in f:
            feature = []
            if len(line) > 1 and line[0] == '#':
                lastkey = line.strip()[1:]
                if len(lastkey) != 11:
                    reason_dict[lastkey] = "ID_LEN_NOT_EQUALTO_11"
                continue
            count += 1
            if count % 1000 == 0:
                print "INFO: Processed %d lines.." % count
            jsonstring = ""
            try:
                jsonstring = json.loads(line.strip())
            except:
                print "ERROR: NO_JSON_FOUND [%s] " % lastkey
                continue
            items = jsonstring.get("items", [])
            if len(items) == 1:
                failed = False
                for field in field_list:
                    if field == "id":
                        vid = items[0].get("id", {})
                        if not vid:
                            reason_dict[lastkey] = "ID_NOT_FOUND"
                            failed = True
                            break
                        if wanted_id_dict and not wanted_id_dict.has_key(lastkey):
                            failed = True
                            break
                        feature.append(str(vid))
                    elif field == "duration":
                        duration = items[0].get("contentDetails", {}).get("duration", {})
                        if not duration:
                            reason_dict[lastkey] = "DURATION_NOT_FOUND"
                            duration = "PT0"
                        duration_str = str(duration)
                        if duration_str.find("PT") != 0:
                            reason_dict[lastkey] = "DURATION_BAD_FORMAT"
                            failed = True
                            break
                        duration_str = duration_str.replace("PT", "").replace("H", "*3600+").replace("M", "*60+").replace("S", "*1+") + "0"
                        feature.append(str(eval(duration_str)))
                    elif field == "title":
                        title = items[0].get("snippet", {}).get("title", {})
                        if not title:
                            reason_dict[lastkey] = "TITLE_NOT_FOUND"
                            title = ""
                        feature.append(str(title).replace("\n", "").replace("\t", ""))
                    elif field == "description":
                        description = items[0].get("snippet", {}).get("description", {})
                        if not description:
                            reason_dict[lastkey] = "DESCRIPTION_NOT_FOUND"
                            description = ""
                        feature.append(str(description).replace("\n", "").replace("\t", ""))
                    elif field == "channelid":
                        channelid = items[0].get("snippet", {}).get("channelId", {})
                        if not channelid:
                            reason_dict[lastkey] = "CHANNELID_NOT_FOUND"
                            channelid = ""
                        feature.append(str(channelid))
                    elif field == "tags":
                        tags = items[0].get("snippet", {}).get("tags", [])
                        if not tags:
                            reason_dict[lastkey] = "TAG_NOT_FOUND"
                            tags = ""
                        taglist = []
                        for tag in tags:
                            taglist.append(str(tag).replace("\n", " ").replace("\r", " "))
                        feature.append(",".join(taglist))
                    elif field == "viewCount":
                        viewCount = items[0].get("statistics", {}).get("viewCount", {})
                        if not viewCount:
                            reason_dict[lastkey] = "VIEWCOUNT_NOT_FOUND"
                            viewCount = 0
                        feature.append(str(viewCount))
                    elif field == "likeCount":
                        likeCount = items[0].get("statistics", {}).get("likeCount", {})
                        if not likeCount:
                            reason_dict[lastkey] = "LIKECOUNT_NOT_FOUND"
                            likeCount = 0
                        feature.append(str(likeCount))
                    elif field == "dislikeCount":
                        dislikeCount = items[0].get("statistics", {}).get("dislikeCount", {})
                        if not dislikeCount:
                            reason_dict[lastkey] = "DISLIKECOUNT_NOT_FOUND"
                            dislikeCount = 0
                        feature.append(str(dislikeCount))
                    else:
                        print "INFO: Unsupported field: [%s]\n" % field
            else:
                reason_dict[lastkey] = "ITEM_NOT_FOUND"
                failed = True
                break
            if not failed:
                feature_list.append("\t".join(feature))
    if feature_list:
        with open(targetfile, "w") as f:
            for line in feature_list:
                f.write("%s\n" % line)

removed_id_file = os.path.join(outputdir, "reason.txt")
with open(removed_id_file, "w") as f:
    for vkey in reason_dict:
        f.write("%s\t%s\n" % (vkey, reason_dict[vkey]))
