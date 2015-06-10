# -*- coding:utf-8  -*-
'''
Created on 2013-4-8

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import common, json
import copy
import os
import shutil
import time

class Instagram(common.Tool):
    
    def trace(self, msg):
        super(Instagram, self).trace(msg, self.isShowError, self.traceLogPath)
    
    def printErrorMsg(self, msg):
        super(Instagram, self).printErrorMsg(msg, self.isShowError, self.errorLogPath)
        
    def printStepMsg(self, msg):
        super(Instagram, self).printStepMsg(msg, self.isShowError, self.stepLogPath)
         
    def __init__(self):
        config = self.analyzeConfig( os.getcwd() + "\\..\\common\\config.ini")
        # 程序配置
        self.isLog = self.getConfig(config, "IS_LOG", 1, 2)
        self.isShowError = self.getConfig(config, "IS_SHOW_ERROR", 1, 2)
        self.isDebug = self.getConfig(config, "IS_DEBUG", 1, 2)
        self.isShowStep = self.getConfig(config, "IS_SHOW_STEP", 1, 2)
        self.isSort = self.getConfig(config, "IS_SORT", 1, 2)
        self.getImageCount = self.getConfig(config, "GET_IMAGE_COUNT", 0, 2)
        # 代理
        self.isProxy = self.getConfig(config, "IS_PROXY", 2, 2)
        self.proxyIp = self.getConfig(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxyPort = self.getConfig(config, "PROXY_PORT", "8087", 0)
        # 文件路径
        self.errorLogPath = self.getConfig(config, "ERROR_LOG_FILE_NAME", "\\log\\errorLog.txt", 3)
        if self.isLog == 0:
            self.traceLogPath = ""
            self.stepLogPath = ""
        else:
            self.traceLogPath = self.getConfig(config, "TRACE_LOG_FILE_NAME", "\\log\\traceLog.txt", 3)
            self.stepLogPath = self.getConfig(config, "STEP_LOG_FILE_NAME", "\\log\\stepLog.txt", 3)
        self.imageDownloadPath = self.getConfig(config, "IMAGE_DOWNLOAD_DIR_NAME", "\\photo", 3)
        self.imageTempPath = self.getConfig(config, "IMAGE_TEMP_DIR_NAME", "\\tempImage", 3)
        self.userIdListFilePath = self.getConfig(config, "USER_ID_LIST_FILE_NAME", "\\info\\idlist.txt", 3)
        self.printMsg("配置文件读取完成")

    def main(self):
        startTime = time.time()
        # 判断各种目录是否存在
        # 日志文件保存目录
        if self.isLog == 1:
            stepLogDir = os.path.dirname(self.stepLogPath)
            if not self.makeDir(stepLogDir, 0):
                self.printErrorMsg("创建步骤日志目录：" + stepLogDir + " 失败，程序结束！")
                self.processExit()
            traceLogDir = os.path.dirname(self.traceLogPath)
            if not self.makeDir(traceLogDir, 0):
                self.printErrorMsg("创建调试日志目录：" + traceLogDir + " 失败，程序结束！")
                self.processExit()
        errorLogDir = os.path.dirname(self.errorLogPath)
        if not self.makeDir(errorLogDir, 0):
            self.printErrorMsg("创建错误日志目录：" + errorLogDir + " 失败，程序结束！")
            self.processExit()

         # 图片保存目录
        self.printStepMsg("创建图片根目录：" + self.imageDownloadPath)
        if not self.makeDir(self.imageDownloadPath, 2):
            self.printErrorMsg("创建图片根目录：" + self.imageDownloadPath + " 失败，程序结束！")
            self.processExit()

        # 设置代理
        if self.isProxy == 1 or self.isProxy == 2:
            self.proxy(self.proxyIp, self.proxyPort, "http")

        # 寻找idlist，如果没有结束进程
        userIdList = {}
        if os.path.exists(self.userIdListFilePath):
            userListFile = open(self.userIdListFilePath, "r")
            allUserList = userListFile.readlines()
            userListFile.close()
            for userInfo in allUserList:
                if len(userInfo) < 2:
                    continue
                userInfo = userInfo.replace("\xef\xbb\xbf", "")
                userInfo = userInfo.replace(" ", "")
                userInfo = userInfo.replace("\n", "")
                userInfoList = userInfo.split("\t")
                userIdList[userInfoList[0]] = userInfoList
        else:
            self.printErrorMsg("用户ID存档文件: " + self.userIdListFilePath + "不存在，程序结束！")
            self.processExit()
        # 创建临时存档文件
        newUserIdListFilePath = os.getcwd() + "\\info\\" + time.strftime("%Y-%m-%d_%H_%M_%S_", time.localtime(time.time())) + os.path.split(self.userIdListFilePath)[-1]
        newUserIdListFile = open(newUserIdListFilePath, "w")
        newUserIdListFile.close()
        # 复制处理存档文件
        newUserIdList = copy.deepcopy(userIdList)
        for newUserAccount in newUserIdList:
            # 如果没有初始image count，则为0
            if len(newUserIdList[newUserAccount]) < 2:
                newUserIdList[newUserAccount].append("0")
            # 处理上一次image id
            # 需置空存放本次第一张获取的image URL
            if len(newUserIdList[newUserAccount]) < 3:
                newUserIdList[newUserAccount].append("")
            else:
                newUserIdList[newUserAccount][2] = ""

        allImageCount = 0
        # 循环下载每个id
        for userAccount in sorted(userIdList.keys()):
            self.printStepMsg("Account: " + userAccount)
            # 初始化数据
            imageId = ""
            imageCount = 1
            isPass = False
            # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
            if len(userIdList[userAccount]) > 2 and int(userIdList[userAccount][1]) != 0 and userIdList[userAccount][2] != "":
                isError = True
            else:
                isError = False
            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if self.isSort == 1:
                imagePath = self.imageTempPath
            else:
                imagePath = self.imageDownloadPath + "\\" + userAccount
            if not self.makeDir(imagePath, 1):
                self.printErrorMsg("创建图片下载目录： " + imagePath + " 失败，程序结束！")
                self.processExit()

            # 图片下载
            while 1:
                if isPass:
                    break
                if imageId == "":
                    photoAlbumUrl = "http://instagram.com/%s/media" % userAccount
                else:
                    photoAlbumUrl = "http://instagram.com/%s/media?max_id=%s" % (userAccount, imageId)
                photoAlbumPage = self.doGet(photoAlbumUrl)
                if not photoAlbumPage:
                    self.printErrorMsg("无法获取相册信息: " + photoAlbumUrl)
                    break
                photoAlbumData = self.doGet(photoAlbumUrl)
                try:
                    photoAlbumPage = json.read(photoAlbumData)
                except:
                    self.printErrorMsg("返回信息：" + str(photoAlbumData) + " 不是一个JSON数据, user id: " + str(userAccount))
                    break
                if not isinstance(photoAlbumPage, dict):
                    self.printErrorMsg("JSON数据：" + str(photoAlbumPage) + " 不是一个字典, user id: " + str(userAccount))
                    break
                if not photoAlbumPage.has_key("items"):
                    self.printErrorMsg("在JSON数据：" + str(photoAlbumPage) + " 中没有找到'items'字段, user id: " + str(userAccount))
                    break
                # 下载到了最后一张图了
                if photoAlbumPage["items"] == []:
                    break
                for photoInfo in photoAlbumPage["items"]:
                    if not photoInfo.has_key("images"):
                        self.printErrorMsg("在JSON数据：" + str(photoInfo) + " 中没有找到'images'字段, user id: " + str(userAccount))
                        break
                    if not photoInfo.has_key("id"):
                        self.printErrorMsg("在JSON数据：" + str(photoInfo) + " 中没有找到'id'字段, user id: " + str(userAccount))
                        break
                    else:
                        imageId = photoInfo["id"]
                    # 将第一张image的id保存到新id list中
                    if newUserIdList[userAccount][2] == "":
                        newUserIdList[userAccount][2] = imageId
                    # 检查是否已下载到前一次的图片
                    if len(userIdList[userAccount]) >= 3 and userIdList[userAccount][2].find("_") != -1:
                        if imageId == userIdList[userAccount][2]:
                            isPass = True
                            isError = False
                            break
                    if not photoInfo["images"].has_key("standard_resolution"):
                        self.printErrorMsg("在JSON数据：" + str(photoInfo["images"]) + " 中没有找到'standard_resolution'字段, user id: " + str(userAccount) + ", image id: " + imageId)
                        break
                    if not photoInfo["images"]["standard_resolution"].has_key("url"):
                        self.printErrorMsg("在JSON数据：" + str(photoInfo["images"]["standard_resolution"]) + " 中没有找到'url'字段, user id: " + str(userAccount) + ", image id: " + imageId)
                        break
                    imageUrl = photoInfo["images"]["standard_resolution"]["url"]
                    self.trace("image URL:" + imageUrl)
                    imgByte = self.doGet(imageUrl)
                    # 文件类型
                    fileType = imageUrl.split(".")[-1]
                    # 保存图片
                    filename = str("%04d" % imageCount)
                    imageFile = open(imagePath + "\\" + str(filename) + "." + fileType, "wb")
                    if imgByte:
                        self.printStepMsg("开始下载第" + str(imageCount) + "张图片：" + imageUrl)
                        imageFile.write(imgByte)
                        self.printStepMsg("下载成功")
                    else:
                        self.printErrorMsg("获取图片" + str(imageCount) + "信息失败：" + str(userAccount) + "，" + imageUrl)
                    imageFile.close()
                    imageCount += 1
                    # 达到配置文件中的下载数量，结束
                    if len(userIdList[userAccount]) >= 3 and userIdList[userAccount][2] != '' and self.getImageCount > 0 and imageCount > self.getImageCount:
                        isPass = True
                        break
            self.printStepMsg(userAccount + "下载完毕，总共获得" + str(imageCount - 1) + "张图片")
            newUserIdList[userAccount][1] = str(int(newUserIdList[userAccount][1]) + imageCount - 1)
            allImageCount += imageCount - 1
            
            # 排序
            if self.isSort == 1:
                imageList = sorted(os.listdir(imagePath), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(imageList) >= 1:
                    destPath = self.imageDownloadPath + "\\" + userAccount
                    if not self.makeDir(destPath, 1):
                        self.printErrorMsg("创建图片子目录： " + destPath + " 失败，程序结束！")
                        self.processExit()

                    # 倒叙排列
                    if len(userIdList[userAccount]) >= 3:
                        count = int(userIdList[userAccount][1]) + 1
                    else:
                        count = 1
                    for fileName in imageList:
                        fileType = fileName.split(".")[1]
                        shutil.copyfile(imagePath + "\\" + fileName, destPath + "\\" + str("%04d" % count) + "." + fileType)
                        count += 1
                    self.printStepMsg("图片从下载目录移动到保存目录成功")
                # 删除临时文件夹
                shutil.rmtree(imagePath, True)

            if isError:
                self.printErrorMsg(userAccount + "图片数量异常，请手动检查")

            # 保存最后的信息
            newUserIdListFile = open(newUserIdListFilePath, "a")
            newUserIdListFile.write("\t".join(newUserIdList[userAccount]) + "\n")
            newUserIdListFile.close()

        stopTime = time.time()
        self.printStepMsg("存档文件中所有用户图片已成功下载，耗时" + str(int(stopTime - startTime)) + "秒，共计图片" + str(allImageCount) + "张")

if __name__ == "__main__":
    Instagram().main()