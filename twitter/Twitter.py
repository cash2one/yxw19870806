# -*- coding:UTF-8  -*-
'''
Created on 2014-5-31

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


class Twitter(common.Tool):

    def __init__(self):
        super(Twitter, self).__init__()
        self.print_msg("配置文件读取完成")

    def _trace(self, msg):
        super(Twitter, self).trace(msg, self.isShowError, self.traceLogPath)
    
    def _print_error_msg(self, msg):
        super(Twitter, self).print_error_msg(msg, self.isShowError, self.errorLogPath)
        
    def _print_step_msg(self, msg):
        super(Twitter, self).print_step_msg(msg, self.isShowError, self.stepLogPath)

    def main(self, userIdListFilePath = '', imageDownloadPath = '', imageTempPath = ''):
        if userIdListFilePath != '':
            self.userIdListFilePath = userIdListFilePath
        if imageDownloadPath != '':
            self.imageDownloadPath = imageDownloadPath
        if imageTempPath != '':
            self.imageTempPath = imageTempPath
        startTime = time.time()
        # 判断各种目录是否存在
        # 日志文件保存目录
        if self.isLog == 1:
            step_log_dir = os.path.dirname(self.stepLogPath)
            if not self.make_dir(step_log_dir, 0):
                self._print_error_msg("创建步骤日志目录：" + step_log_dir + " 失败，程序结束！")
                self.process_exit()
            trace_log_dir = os.path.dirname(self.traceLogPath)
            if not self.make_dir(trace_log_dir, 0):
                self._print_error_msg("创建调试日志目录：" + trace_log_dir + " 失败，程序结束！")
                self.process_exit()
        error_log_dir = os.path.dirname(self.errorLogPath)
        if not self.make_dir(error_log_dir, 0):
            self._print_error_msg("创建错误日志目录：" + error_log_dir + " 失败，程序结束！")
            self.process_exit()

        # 图片保存目录
        self._print_step_msg("创建图片根目录：" + self.imageDownloadPath)
        if not self.make_dir(self.imageDownloadPath, 2):
            self._print_error_msg("创建图片根目录：" + self.imageDownloadPath + " 失败，程序结束！")
            self.process_exit()

        # 设置代理
        if self.isProxy == 1 or self.isProxy == 2:
            self.set_proxy(self.proxyIp, self.proxyPort, "https")

        # 寻找idlist，如果没有结束进程
        userIdList = {}
        if os.path.exists(self.userIdListFilePath):
            userListFile = open(self.userIdListFilePath, "r")
            allUserList = userListFile.readlines()
            userListFile.close()
            for userInfo in allUserList:
                if len(userInfo) < 3:
                    continue
                userInfo = userInfo.replace("\xef\xbb\xbf", "")
                userInfo = userInfo.replace(" ", "")
                userInfo = userInfo.replace("\n", "")
                userInfoList = userInfo.split("\t")
                userIdList[userInfoList[0]] = userInfoList
        else:
            self._print_error_msg("用户ID存档文件: " + self.userIdListFilePath + "不存在，程序结束！")
            self.process_exit()
        # 创建临时存档文件
        newUserIdListFilePath = os.getcwd() + "\\info\\" + time.strftime("%Y-%m-%d_%H_%M_%S_", time.localtime(time.time())) + os.path.split(self.userIdListFilePath)[-1]
        newUserIdListFile = open(newUserIdListFilePath, "w")
        newUserIdListFile.close()
        # 复制处理存档文件
        newUserIdList = copy.deepcopy(userIdList)
        for newUserAccount in newUserIdList:
            # 如果没有数量，则为0
            if len(newUserIdList[newUserAccount]) < 2:
                newUserIdList[newUserAccount].append("0")
            if newUserIdList[newUserAccount][1] == '':
                newUserIdList[newUserAccount][1] = 0
            # 处理上一次image URL
            # 需置空存放本次第一张获取的image URL
            if len(newUserIdList[newUserAccount]) < 3:
                newUserIdList[newUserAccount].append("")
            else:
                newUserIdList[newUserAccount][2] = ""
        
        init_max_id = 999999999999999999
        totalImageCount = 0
        # 循环下载每个id
        for userAccount in sorted(userIdList.keys()):
            self._print_step_msg("Account: " + userAccount)
            # 初始化数据
            dataTweetId = init_max_id
            imageCount = 1
            imageUrlList = []
            isPass = False
            isLastPage = False
            # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
            if len(userIdList[userAccount]) > 2 and userIdList[userAccount][1] != '' and int(userIdList[userAccount][1]) != 0:
                isError = True
            else:
                isError = False
            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if self.isSort == 1:
                imagePath = self.imageTempPath
            else:
                imagePath = self.imageDownloadPath + "\\" + userAccount
            if not self.make_dir(imagePath, 1):
                self._print_error_msg("创建图片下载目录： " + imagePath + " 失败，程序结束！")
                self.process_exit()

            # 图片下载
            while not isLastPage:
                if isPass:
                    break
                photoPageUrl = "https://twitter.com/i/profiles/show/%s/media_timeline?include_available_features=1&include_entities=1&max_position=%s" % (userAccount, dataTweetId)
                photoPageData = self.do_get(photoPageUrl)
                if not photoPageData:
                    self._print_error_msg("无法获取相册信息: " + photoPageUrl)
                    break
                try:
                    page = json.read(photoPageData)
                except:
                    self._print_error_msg("返回信息：" + str(photoPageData) + " 不是一个JSON数据, account: " + userAccount)
                    break

                if not isinstance(page, dict):
                    self._print_error_msg("JSON数据：" + str(page) + " 不是一个字典, account: " + userAccount)
                    break
                if not page.has_key("has_more_items"):
                    self._print_error_msg("在JSON数据：" + str(page) + " 中没有找到'has_more_items'字段, account: " + userAccount)
                    break
                if page['has_more_items'] == False :
                    isLastPage = True
                if not page.has_key("items_html"):
                    self._print_error_msg("在JSON数据：" + str(page) + " 中没有找到'items_html'字段, account: " + userAccount)
                    break

                page = page['items_html']

                imageIndex = page.find("data-url")
                while imageIndex != -1:
                    imageStart = page.find("http", imageIndex)
                    imageStop = page.find('"', imageStart)
                    imageUrl = page[imageStart:imageStop].encode("utf-8")
                    if imageUrl.find('&quot') != -1:
                        imageUrl = imageUrl[:imageUrl.find('&quot')]
                    self._trace("image URL:" + imageUrl)
                    # 将第一张image的URL保存到新id list中
                    if newUserIdList[userAccount][2] == "":
                        newUserIdList[userAccount][2] = imageUrl
                    # 检查是否已下载到前一次的图片
                    if len(userIdList[userAccount]) >= 3:
                        if imageUrl == userIdList[userAccount][2]:
                            isPass = True
                            isError = False
                            break
                    if imageUrl in imageUrlList:
                        imageIndex = page.find('data-url', imageIndex + 1)
                        continue
                    imageUrlList.append(imageUrl)
                    self._print_step_msg("开始下载第 " + str(imageCount) + "张图片：" + imageUrl)
                    imgByte = self.do_get(imageUrl)
                    if imgByte:
                        # 文件类型
                        fileType = imageUrl.split(".")[-1].split(':')[0]
                        # 保存图片
                        imageFile = open(imagePath + "\\" + str("%04d" % imageCount) + "." + fileType, "wb")
                        imageFile.write(imgByte)
                        self._print_step_msg("下载成功")
                        imageFile.close()
                        imageCount += 1
                    else:
                        self._print_error_msg("获取第" + str(imageCount) + "张图片信息失败：" + userAccount + "：" + imageUrl)

                    # 达到配置文件中的下载数量，结束
                    if len(userIdList[userAccount]) >= 3 and userIdList[userAccount][2] != '' and self.getImageCount > 0 and imageCount > self.getImageCount:
                        isPass = True
                        break
                    imageIndex = page.find('data-url', imageIndex + 1)

                if not isLastPage:
                    # 设置最后一张的data-tweet-id
                    dataTweetIdIndex = page.find('data-tweet-id="')
                    while dataTweetIdIndex != -1:
                        dataTweetIdStart = page.find('"', dataTweetIdIndex)
                        dataTweetIdStop = page.find('"', dataTweetIdStart + 1)
                        dataTweetId = page[dataTweetIdStart + 1:dataTweetIdStop]
                        dataTweetIdIndex = page.find('data-tweet-id="', dataTweetIdIndex + 1)

            self._print_step_msg(userAccount + "下载完毕，总共获得" + str(imageCount - 1) + "张图片")
            newUserIdList[userAccount][1] = str(int(newUserIdList[userAccount][1]) + imageCount - 1)
            totalImageCount += imageCount - 1
            
            # 排序
            if self.isSort == 1:
                imageList = sorted(os.listdir(imagePath), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(imageList) >= 1:
                    destPath = self.imageDownloadPath + "\\" + userAccount
                    if not self.make_dir(destPath, 1):
                        self._print_error_msg("创建图片子目录： " + destPath + " 失败，程序结束！")
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
                    self._print_step_msg("图片从下载目录移动到保存目录成功")
                # 删除临时文件夹
                shutil.rmtree(imagePath, True)

            if isError:
                self._print_error_msg(userAccount + "图片数量异常，请手动检查")

            # 保存最后的信息
            newUserIdListFile = open(newUserIdListFilePath, "a")
            newUserIdListFile.write("\t".join(newUserIdList[userAccount]) + "\n")
            newUserIdListFile.close()

        stopTime = time.time()
        self._print_step_msg("存档文件中所有用户图片已成功下载，耗时" + str(int(stopTime - startTime)) + "秒，共计图片" + str(totalImageCount) + "张")

if __name__ == "__main__":
    Twitter().main(os.getcwd() + "\\info\\idlist_1.txt", os.getcwd() +  "\\photo\\twitter1", os.getcwd() +  "\\photo\\twitter1\\tempImage")
    Twitter().main(os.getcwd() + "\\info\\idlist_2.txt", os.getcwd() +  "\\photo\\twitter2", os.getcwd() +  "\\photo\\twitter2\\tempImage")
    Twitter().main(os.getcwd() + "\\info\\idlist_3.txt", os.getcwd() +  "\\photo\\twitter3", os.getcwd() +  "\\photo\\twitter3\\tempImage")
