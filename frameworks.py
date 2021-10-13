# -*- coding: utf-8 -*-
# 在jenkins上使用的打包脚本

import os
import sys
import json
import commands
import re
import shutil


reload(sys)
sys.setdefaultencoding("utf-8")


if len(sys.argv)<4:
    print('python build.py branch uploadfolder build_id')
    sys.stdout.flush()
    sys.exit(1)

mainPath = os.path.split(os.path.realpath(__file__))[0]
currentBranch = '%s'%(sys.argv[1])    #will be updated
uploadFolder = '%s'%(sys.argv[2])
leading_4_spaces = re.compile('^    ')




rely_modules = {
    'third':[],
    'user':['third'],
    'network':['user','third'],
    'basic' :  ['network','user','third'],
    'optional':['basic','network','user','third'],
    'models':  ['basic','network','user','third'],
    'chatbase':['models','basic','network','user','third'],
    'chat':    ['chatbase','models','basic','network','user','third'],

    'company':  ['chatbase','basic','models','network','user','third'],
    'homepage': ['chatbase','basic','models','network','user','third'],
    'login':    ['basic','models','network','user','third'],
    'support':  ['basic','models','network','user','third'],
    'setting':  ['basic','models','network','user','third'],
    'boss':     ['chatbase','basic','models','network','user','third'],
    'geek':     ['chatbase','basic','models','network','user','third']
}

def createFlag(content):
    flagPath = os.path.join(mainPath,'frameworks/building')
    folder = os.path.join(mainPath,'frameworks')
    if not os.path.exists(folder):
        os.makedirs(folder)
    f = open(flagPath,'w')
    f.write(content)
    f.close()
    return

def removeFlag():
    flagPath = os.path.join(mainPath,'frameworks/building')
    if os.path.exists(flagPath):
        os.remove(flagPath)
    return

def sysexit(errorCode,name):
    createFlag('Failed to build framework %s!'%(moduleMap[name][0]))
    sys.exit(errorCode)
    return

def getCurrentBranch():
    cmd = 'git rev-parse --abbrev-ref HEAD'
    status, output = commands.getstatusoutput(cmd)
    return output

def get_commits(folder):
    cmd = 'cd "%s"; git log'%(folder)
    status, output = commands.getstatusoutput(cmd)
    lines = output.split('\n')
    commits = []
    current_commit = {}

    def save_current_commit():
        title = current_commit['message'][0]
        message = current_commit['message'][1:]
        if message and message[0] == '':
            del message[0]
        current_commit['title'] = title
        current_commit['message'] = '\n'.join(message)
        commits.append(current_commit)

    for line in lines:
        if not line.startswith(' '):
            if line.startswith('commit '):
                if current_commit:
                    save_current_commit()
                    current_commit = {}
                current_commit['hash'] = line.split('commit ')[1]
            else:
                try:
                    key, value = line.split(':', 1)
                    current_commit[key.lower()] = value.strip()
                except ValueError:
                    pass
        else:
            current_commit.setdefault(
                'message', []
            ).append(leading_4_spaces.sub('', line))
    if current_commit:
        save_current_commit()
    return commits

def getLastCommitHash(name):
    path = os.path.join(mainPath,'../%s'%(moduleMap[name][1]))
    return get_commits(path)[0]['hash']

# 查找目录下的lib***.a文件，返回文件名
def findFileWithExtension(folder,extension):
    for filename in os.listdir(folder):
        pathname = os.path.join(folder,filename)
        if filename.endswith(extension) and os.path.isfile(pathname):
            return pathname
    return ''

def checkoutModule(gitName,defaultBranch):
    branch = defaultBranch
    
    print('-------- %s 切换分支到:%s -----------'%(gitName,branch))
    sys.stdout.flush()
    path = os.path.join(mainPath,'../%s'%(gitName))
    if os.path.exists(path):
        print(gitName+': ')
        sys.stdout.flush()
        cmd = 'cd "%s"; git reset --hard HEAD;git pull'%(path)
        print(cmd)
        sys.stdout.flush()
        os.system(cmd)
        cmd = 'cd "%s";git branch --set-upstream-to=origin/%s %s; git checkout %s 2>/dev/null || git checkout -b %s; git pull'%(path,branch,branch,branch,branch)
        print(cmd)
        sys.stdout.flush()
        os.system(cmd)
        return
    
    repo = 'bosszhipinspec'
    cmd = 'cd "%s/.."; git clone "git@git.kanzhun-inc.com:%s/%s.git"; cd "%s";git branch --set-upstream-to=origin/%s %s; git checkout %s 2>/dev/null || git checkout -b %s; git pull'%(mainPath,repo,gitName,path,branch,branch,branch,branch)
    print(cmd)
    sys.stdout.flush()
    os.system(cmd)
    return

def getOutputDir(targetName):
    return os.path.join(mainPath,'frameworks/%s/Products'%(targetName))

def buildPodfileContent(name,targetName):
    result = ''
    depends = rely_modules[name]
    if name=='basic' or 'basic' in depends:
        result = result + "pod 'BZHeaders',:path => '../../bz_models/Headers', :inhibit_warnings => false\n"
    result = result + ("pod '%s',:path => '..', :inhibit_warnings => false\n"%(targetName))
    for d in depends:
        podname = moduleMap[d][0]
        result = result + ("pod '%s', :path=>'Pods/%s'\n"%(podname,podname))
    return result

def preparePodfile(name):
    projName = moduleMap[name][0]
    frameworkDir = moduleMap[name][1]

    frameworkDir = os.path.join(mainPath,'../%s'%(frameworkDir))
    podspecPath = findFileWithExtension(frameworkDir,'podspec')
    filename = os.path.basename(podspecPath)
    (targetName,extension) = os.path.splitext(filename)
    targetDir = os.path.join(frameworkDir,targetName)
    podfilePath = os.path.join(targetDir,'Podfile')

    podfileContent = open(podfilePath,'r').readlines()
    firstPodIndex = -1
    index=0
    while index<len(podfileContent):
        line = podfileContent[index]
        if line.startswith('pod'):
            if firstPodIndex<0:
                firstPodIndex= index
            podfileContent.pop(index)
        else:
            index=index+1
    if firstPodIndex<0:
        firstPodIndex = len(podfileContent)
    podfileContent.insert(firstPodIndex,buildPodfileContent(name,targetName))
    content = ''.join(podfileContent)
    f = open(podfilePath,'w')
    f.write(content)
    f.close()
    return

def copyDepends(name):
    destFolder = os.path.join(mainPath,'../%s/%s/Pods'%(moduleMap[name][1],moduleMap[name][0]))
    srcFrom = os.path.join(mainPath,'frameworks')
    depends = rely_modules[name]
    for d in depends:
        f = os.path.join(srcFrom,moduleMap[d][0])
        t = os.path.join(destFolder,moduleMap[d][0])
        if os.path.exists(t):
            shutil.rmtree(t)
        shutil.copytree(f,t)
    return

def resetRepo(name):
    repoFolder = os.path.join(mainPath,'../%s'%(moduleMap[name][1]))
    cmd = "cd '%s'; rm -rf Products; git reset --hard HEAD"%(repoFolder)
    print(cmd)
    sys.stdout.flush()
    os.system(cmd)
    return

#更新上传信息
def updateUploadInfo(name):
    configPath = os.path.join(uploadFolder,'%s/versions.ini'%(currentBranch))
    txt = '{}'
    if os.path.exists(configPath):
        txt = open(configPath,'r').read()
    config = json.loads(txt)
    config[moduleMap[name][0]] = getLastCommitHash(name)
    f = open(configPath,'w')
    f.write(json.dumps(config))
    f.close()
    return

#获取上传的包的提交hash
def getUploadedCommitHash(name):
    configPath = os.path.join(uploadFolder,'%s/versions.ini'%(currentBranch))
    txt = '{}'
    if os.path.exists(configPath):
        txt = open(configPath,'r').read()
    config = json.loads(txt)
    m = moduleMap[name][0]
    if config.has_key(m):
        return config[m]
    return ''

def uploadSourceCode(name):
    sourceFolder = os.path.join(mainPath,'../%s'%(moduleMap[name][1]))
    sourceName = 'Source'
    if name=='third' or name=='optional':
        sourceFolder = os.path.join(mainPath,'../%s/%s'%(moduleMap[name][1],moduleMap[name][0]))
        sourceName = 'Pods'
    to = os.path.join(uploadFolder,"%s/%s_src.zip"%(currentBranch,moduleMap[name][0]))
    if os.path.exists(to):
        os.remove(to)
    cmd = 'cd "%s";zip -q -r "%s" %s'%(sourceFolder,to,sourceName)
    print(cmd)
    sys.stdout.flush()
    os.system(cmd)
    return

#上传打包好的framework
def uploadFramework(name):
    folder = os.path.join(uploadFolder,currentBranch)
    if not os.path.exists(folder):
        os.makedirs(folder)
    source = os.path.join(mainPath,'frameworks')
    to = os.path.join(uploadFolder,"%s/%s.zip"%(currentBranch,moduleMap[name][0]))
    if os.path.exists(to):
        os.remove(to)
    cmd = 'cd "%s";zip -q -r "%s" %s'%(source,to,moduleMap[name][0])
    print(cmd)
    sys.stdout.flush()
    os.system(cmd)
    if not os.path.exists(to):
        print('Failed to upload framework %s'%(name))
        sys.stdout.flush()
        sysexit(1,name)
    return

#判断组件是否有更新
def repoHasChanged(name):
    lastBuildCommit = getUploadedCommitHash(name)
    thisCommit = getLastCommitHash(name)
    return thisCommit!=lastBuildCommit

#从上传文件夹中恢复framework到bossproject/frameworks文件夹
def restoreFramework(name):
    if getUploadedCommitHash(name)!=getLastCommitHash(name):
        return False
    source = os.path.join(uploadFolder,"%s/%s.zip"%(currentBranch,moduleMap[name][0]))
    to = os.path.join(mainPath,'frameworks/%s'%(moduleMap[name][0]))
    if os.path.exists(to):
        shutil.rmtree(to)
    if not os.path.exists(source):
        return False
    cmd = 'unzip -qq -o "%s" -d "%s"'%(source,os.path.join(mainPath,'frameworks'))
    print(cmd)
    sys.stdout.flush()
    os.system(cmd)
    return True

def checkoutModule(gitName,defaultBranch):
    branch = defaultBranch
    
    print('-------- %s 切换分支到:%s -----------'%(gitName,branch))
    sys.stdout.flush()
    path = os.path.join(mainPath,'../%s'%(gitName))
    if os.path.exists(path):
        print(gitName+': ')
        sys.stdout.flush()
        cmd = 'cd "%s"; git reset --hard HEAD;git pull'%(path)
        print(cmd)
        sys.stdout.flush()
        os.system(cmd)
        cmd = 'cd "%s";git branch --set-upstream-to=origin/%s %s; git checkout %s 2>/dev/null || git checkout -b %s; git pull'%(path,branch,branch,branch,branch)
        print(cmd)
        sys.stdout.flush()
        os.system(cmd)
        return
    
    repo = 'lijingxiu'
    cmd = 'cd "%s/.."; git clone "git@github.com:%s/%s.git"; cd "%s";git branch --set-upstream-to=origin/%s %s; git checkout %s 2>/dev/null || git checkout -b %s; git pull'%(mainPath,repo,gitName,path,branch,branch,branch,branch)
    print(cmd)
    sys.stdout.flush()
    os.system(cmd)
    return

def buildFramework(name):
 
    #准备最新代码
    checkoutModule(name,currentBranch)

    # if not repoHasChanged(name):
    #     print('repo %s not changed since last build framework, will restore from upload folder'%(name))
    #     sys.stdout.flush()
    #     if restoreFramework(name):
    #         print('restored %s from upload folder'%(name))
    #         sys.stdout.flush()
    #         return
    #     else:
    #         print('restore failed, will building %s framework from source code'%(name))
    #         sys.stdout.flush()

    # #准备podfile文件
    # preparePodfile(name)

    # #复制依赖的framework
    # copyDepends(name)

    # frameworkDir = os.path.join(mainPath,'../%s'%(frameworkDir))
    # podspecPath = findFileWithExtension(frameworkDir,'podspec')
    # filename = os.path.basename(podspecPath)
    # (targetName,extension) = os.path.splitext(filename)
    # targetDir = os.path.join(frameworkDir,targetName)
    # productPath = "%s/Products/%s.framework"%(frameworkDir,targetName)

    # #remove old
    # cmd = 'rm -rf "%s"'%(productPath)
    # os.system(cmd)

    # #build
    # os.system('cd %s; python process.py'%(targetDir))

    # #check
    # if not os.path.exists(productPath):
    #     print('Failed to build framework %s'%(name))
    #     sys.stdout.flush()
    #     sysexit(1,name)
    # productPath = "%s/Products"%(frameworkDir)
    # if os.path.exists(getOutputDir(targetName)):
    #     shutil.rmtree(getOutputDir(targetName))
    # shutil.copytree(productPath,getOutputDir(targetName))
    # podspecFrom = os.path.join(mainPath,'frameworks/%s/Products/%s.podspec'%(targetName,targetName))
    # podspecTo = os.path.join(mainPath,'frameworks/%s/%s.podspec'%(targetName,targetName))
    # shutil.move(podspecFrom,podspecTo)
    
    # #恢复仓库
    # uploadFramework(name)
    # updateUploadInfo(name)
    # uploadSourceCode(name)
    # resetRepo(name)
    return

def buildAll():
    #清空目录
    cmd = "rm -rf frameworks"
    print(cmd)
    sys.stdout.flush()
    os.system(cmd)
    #创建编译中文件
    createFlag('')
    #拉取models代码
    buildFramework('TestPodCC')
    removeFlag()
    return

buildAll()

