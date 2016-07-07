# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os


def getCount(idPath, imageRootPath):
    tempFile = open(idPath, 'r')
    lines = tempFile.readlines()
    tempFile.close()
    for line in lines:
        line = line.split("\t")
        imagePath = imageRootPath + line[1]
        imagePath = imagePath.decode('UTF-8').encode('GBK')
        all_file = os.listdir(imagePath)
        if os.path.exists(imagePath):
            count1 = len(all_file)
        else:
            count1 = 0
        count2 = int(line[2])
        max_count = int(max(all_file).split('.')[0])
        if count1 != count2 or count1 != max_count:
            print line[1] + ": " + str(count1) + ", " + str(count2) + ", " + str(max_count)
    print "check over!"

for save_file in ["ATF", "lunar", "save_1", "save_2", "snh48"]:
    getCount("info\\%s.data" % save_file, "Z:\\G+\\weibo\\%s\\" % save_file)
