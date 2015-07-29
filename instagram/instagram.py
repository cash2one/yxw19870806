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
    
    def print_error_msg(self, msg):
        super(Instagram, self).print_error_msg(msg, self.isShowError, self.errorLogPath)
        
    def print_step_msg(self, msg):
        super(Instagram, self).print_step_msg(msg, self.isShowError, self.stepLogPath)
         
    def __init__(self):
        config = self.analyze_config( os.getcwd() + "\\..\\common\\config.ini")
        # 程序配置
        self.isLog = self.get_config(config, "IS_LOG", 1, 2)
        self.isShowError = self.get_config(config, "IS_SHOW_ERROR", 1, 2)
        self.isDebug = self.get_config(config, "IS_DEBUG", 1, 2)
        self.isShowStep = self.get_config(config, "IS_SHOW_STEP", 1, 2)
        self.isSort = self.get_config(config, "IS_SORT", 1, 2)
        self.getImageCount = self.get_config(config, "GET_IMAGE_COUNT", 0, 2)
        # 代理
        self.isProxy = self.get_config(config, "IS_PROXY", 2, 2)
        self.proxyIp = self.get_config(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxyPort = self.get_config(config, "PROXY_PORT", "8087", 0)
        # 文件路径
        self.errorLogPath = self.get_config(config, "ERROR_LOG_FILE_NAME", "\\log\\errorLog.txt", 3)
        if self.isLog == 0:
            self.traceLogPath = ""
            self.stepLogPath = ""
        else:
            self.traceLogPath = self.get_config(config, "TRACE_LOG_FILE_NAME", "\\log\\traceLog.txt", 3)
            self.stepLogPath = self.get_config(config, "STEP_LOG_FILE_NAME", "\\log\\stepLog.txt", 3)
        self.imageDownloadPath = self.get_config(config, "IMAGE_DOWNLOAD_DIR_NAME", "\\photo", 3)
        self.imageTempPath = self.get_config(config, "IMAGE_TEMP_DIR_NAME", "\\tempImage", 3)
        self.userIdListFilePath = self.get_config(config, "USER_ID_LIST_FILE_NAME", "\\info\\idlist.txt", 3)
        self.print_msg("配置文件读取完成")

    def main(self):
        startTime = time.time()
        # 判断各种目录是否存在
        # 日志文件保存目录
        if self.isLog == 1:
            stepLogDir = os.path.dirname(self.stepLogPath)
            if not self.make_dir(stepLogDir, 0):
                self.print_error_msg("创建步骤日志目录：" + stepLogDir + " 失败，程序结束！")
                self.process_exit()
            traceLogDir = os.path.dirname(self.traceLogPath)
            if not self.make_dir(traceLogDir, 0):
                self.print_error_msg("创建调试日志目录：" + traceLogDir + " 失败，程序结束！")
                self.process_exit()
        errorLogDir = os.path.dirname(self.errorLogPath)
        if not self.make_dir(errorLogDir, 0):
            self.print_error_msg("创建错误日志目录：" + errorLogDir + " 失败，程序结束！")
            self.process_exit()

         # 图片保存目录
        self.print_step_msg("创建图片根目录：" + self.imageDownloadPath)
        if not self.make_dir(self.imageDownloadPath, 2):
            self.print_error_msg("创建图片根目录：" + self.imageDownloadPath + " 失败，程序结束！")
            self.process_exit()

        # 设置代理
        if self.isProxy == 1 or self.isProxy == 2:
            self.set_proxy(self.proxyIp, self.proxyPort, "http")

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
            self.print_error_msg("用户ID存档文件: " + self.userIdListFilePath + "不存在，程序结束！")
            self.process_exit()
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
            if newUserIdList[newUserAccount][1] == '':
                newUserIdList[newUserAccount][1] = 0
            # 处理上一次image id
            # 需置空存放本次第一张获取的image URL
            if len(newUserIdList[newUserAccount]) < 3:
                newUserIdList[newUserAccount].append("")
            else:
                newUserIdList[newUserAccount][2] = ""

        allImageCount = 0
        # 循环下载每个id
        for userAccount in sorted(userIdList.keys()):
            self.print_step_msg("Account: " + userAccount)
            # 初始化数据
            imageId = ""
            imageCount = 1
            isPass = False
            # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
            if len(userIdList[userAccount]) > 2 and userIdList[userAccount][1] != '' and int(userIdList[userAccount][1]) != 0 and userIdList[userAccount][2] != "":
                isError = True
            else:
                isError = False
            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if self.isSort == 1:
                imagePath = self.imageTempPath
            else:
                imagePath = self.imageDownloadPath + "\\" + userAccount
            if not self.make_dir(imagePath, 1):
                self.print_error_msg("创建图片下载目录： " + imagePath + " 失败，程序结束！")
                self.process_exit()

            # 图片下载
            while 1:
                if isPass:
                    break
                if imageId == "":
                    photoAlbumUrl = "http://instagram.com/%s/media" % userAccount
                else:
                    photoAlbumUrl = "http://instagram.com/%s/media?max_id=%s" % (userAccount, imageId)
                photoAlbumPage = self.do_get(photoAlbumUrl)
                if not photoAlbumPage:
                    self.print_error_msg("无法获取相册信息: " + photoAlbumUrl)
                    break
                photoAlbumData = self.do_get(photoAlbumUrl)
                try:
                    photoAlbumPage = json.read(photoAlbumData)
                except:
                    self.print_error_msg("返回信息：" + str(photoAlbumData) + " 不是一个JSON数据, user id: " + str(userAccount))
                    break
                if not isinstance(photoAlbumPage, dict):
                    self.print_error_msg("JSON数据：" + str(photoAlbumPage) + " 不是一个字典, user id: " + str(userAccount))
                    break
                if not photoAlbumPage.has_key("items"):
                    self.print_error_msg("在JSON数据：" + str(photoAlbumPage) + " 中没有找到'items'字段, user id: " + str(userAccount))
                    break
                # 下载到了最后一张图了
                if photoAlbumPage["items"] == []:
                    break
                for photoInfo in photoAlbumPage["items"]:
                    if not photoInfo.has_key("images"):
                        self.print_error_msg("在JSON数据：" + str(photoInfo) + " 中没有找到'images'字段, user id: " + str(userAccount))
                        break
                    if not photoInfo.has_key("id"):
                        self.print_error_msg("在JSON数据：" + str(photoInfo) + " 中没有找到'id'字段, user id: " + str(userAccount))
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
                        self.print_error_msg("在JSON数据：" + str(photoInfo["images"]) + " 中没有找到'standard_resolution'字段, user id: " + str(userAccount) + ", image id: " + imageId)
                        break
                    if not photoInfo["images"]["standard_resolution"].has_key("url"):
                        self.print_error_msg("在JSON数据：" + str(photoInfo["images"]["standard_resolution"]) + " 中没有找到'url'字段, user id: " + str(userAccount) + ", image id: " + imageId)
                        break
                    imageUrl = photoInfo["images"]["standard_resolution"]["url"]
                    self.print_step_msg("开始下载第 " + str(imageCount) + "张图片：" + imageUrl)
                    imgByte = self.do_get(imageUrl)
                    if imgByte:
                        # 文件类型
                        fileType = imageUrl.split(".")[-1]
                        # 保存图片
                        imageFile = open(imagePath + "\\" + str("%04d" % imageCount) + "." + fileType, "wb")
                        imageFile.write(imgByte)
                        self.print_step_msg("下载成功")
                        imageFile.close()
                        imageCount += 1
                    else:
                        self.print_error_msg("获取第" + str(imageCount) + "张图片信息失败：" + str(userAccount) + "，" + imageUrl)

                    # 达到配置文件中的下载数量，结束
                    if len(userIdList[userAccount]) >= 3 and userIdList[userAccount][2] != '' and self.getImageCount > 0 and imageCount > self.getImageCount:
                        isPass = True
                        break
            self.print_step_msg(userAccount + "下载完毕，总共获得" + str(imageCount - 1) + "张图片")
            newUserIdList[userAccount][1] = str(int(newUserIdList[userAccount][1]) + imageCount - 1)
            allImageCount += imageCount - 1
            
            # 排序
            if self.isSort == 1:
                imageList = sorted(os.listdir(imagePath), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(imageList) >= 1:
                    destPath = self.imageDownloadPath + "\\" + userAccount
                    if not self.make_dir(destPath, 1):
                        self.print_error_msg("创建图片子目录： " + destPath + " 失败，程序结束！")
                        self.process_exit()

                    # 倒叙排列
                    if len(userIdList[userAccount]) >= 2 and userIdList[userAccount][1] != '':
                        count = int(userIdList[userAccount][1]) + 1
                    else:
                        count = 1
                    for fileName in imageList:
                        fileType = fileName.split(".")[1]
                        self.copy_files(imagePath + "\\" + fileName, destPath + "\\" + str("%04d" % count) + "." + fileType)
                        count += 1
                    self.print_step_msg("图片从下载目录移动到保存目录成功")
                # 删除临时文件夹
                shutil.rmtree(imagePath, True)

            if isError:
                self.print_error_msg(userAccount + "图片数量异常，请手动检查")

            # 保存最后的信息
            newUserIdListFile = open(newUserIdListFilePath, "a")
            newUserIdListFile.write("\t".join(newUserIdList[userAccount]) + "\n")
            newUserIdListFile.close()

        stopTime = time.time()
        self.print_step_msg("存档文件中所有用户图片已成功下载，耗时" + str(int(stopTime - startTime)) + "秒，共计图片" + str(allImageCount) + "张")

if __name__ == "__main__":
    Instagram().main()
