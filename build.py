# -*- coding: utf-8 -*-
# 在jenkins上使用的打包脚本

import optparse
import os
import sys
# import getpass
# import json
# import time
# import commands
# import re
# import string
# import subprocess
# import codecs
# import shutil

print('执行build.py')
for item in sys.argv:
    print(item)

mainPath = os.path.split(os.path.realpath(__file__))[0]
print(mainPath)

mainPath = os.path.join(mainPath,'package')

cmd="cd %s;xcodebuild archive -workspace %s.xcworkspace -scheme %s -configuration 'Release Adhoc' -archivePath ./build -derivedDataPath ./derivedData"%(mainPath,'package','package')
print(cmd)
# os.system(cmd)

cmd="cd %s;xcodebuild -exportArchive -archivePath ./build.xcarchive -exportPath ./ipa -exportOptionsPlist ./ExportOptions.plist"%(mainPath)
print(cmd)
sys.stdout.flush()
# os.system (cmd)
