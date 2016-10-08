# -*- coding:UTF-8  -*-
"""
欅坂46公式Blog图片爬虫
http://www.keyakizaka46.com/mob/news/diarShw.php?cd=member
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
IMAGE_COUNT_PER_PAGE = 20
TOTAL_IMAGE_COUNT = 0
GET_IMAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True
IS_DOWNLOAD_IMAGE = True
IS_DOWNLOAD_VIDEO = True

threadLock = threading.Lock()


def print_error_msg(msg):
    threadLock.acquire()
    log.error(msg)
    threadLock.release()


def print_step_msg(msg):
    threadLock.acquire()
    log.step(msg)
    threadLock.release()


def trace(msg):
    threadLock.acquire()
    log.trace(msg)
    threadLock.release()


def get_diary_page_data(account_id, page_count):
    diary_page_url = "http://www.keyakizaka46.com/mob/news/diarKiji.php"
    diary_page_url += "?cd=member&ct=%02d&page=%s&rw=%s" % (int(account_id), page_count - 1, IMAGE_COUNT_PER_PAGE)
    diary_return_code, diary_page = tool.http_request(diary_page_url)[:2]
    if diary_return_code:
        diary_data = tool.find_sub_string(diary_page, '<div class="box-main">', '<div class="box-sideMember">')
        if diary_data:
            return re.findall("<article>([\s|\S]*?)</article>", diary_page)
    return None


class Diary(robot.Robot):
    def __init__(self):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global IS_DOWNLOAD_IMAGE
        global IS_DOWNLOAD_VIDEO

        robot.Robot.__init__(self)

        # 设置全局变量，供子线程调用
        GET_IMAGE_COUNT = self.get_image_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
        IS_DOWNLOAD_IMAGE = self.is_download_image
        IS_DOWNLOAD_VIDEO = self.is_download_video
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

        tool.print_msg("配置文件读取完成")

    def main(self):
        global ACCOUNTS
        
        if not IS_DOWNLOAD_IMAGE and not IS_DOWNLOAD_VIDEO:
            print_error_msg("下载图片和视频都没有开启，请检查配置！")
            tool.process_exit()

        start_time = time.time()

        # 创建图片保存目录
        if IS_DOWNLOAD_IMAGE:
            print_step_msg("创建图片根目录 %s" % IMAGE_DOWNLOAD_PATH)
            if not tool.make_dir(IMAGE_DOWNLOAD_PATH, 0):
                print_error_msg("创建图片根目录 %s 失败" % IMAGE_DOWNLOAD_PATH)
                tool.process_exit()

        # 寻找idlist，如果没有结束进程
        account_list = {}
        if os.path.exists(self.save_data_path):
            # account_id  image_count  last_diary_time
            account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0"])
            ACCOUNTS = account_list.keys()
        else:
            print_error_msg("用户ID存档文件 %s 不存在" % self.save_data_path)
            tool.process_exit()

        # 创建临时存档文件
        new_save_data_file = open(NEW_SAVE_DATA_PATH, "w")
        new_save_data_file.close()

        # 启用线程监控是否需要暂停其他下载线程
        process_control_thread = tool.ProcessControl()
        process_control_thread.setDaemon(True)
        process_control_thread.start()

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(account_list.keys()):
            # 检查正在运行的线程数
            while threading.activeCount() >= self.thread_count + main_thread_count:
                if tool.is_process_end() == 0:
                    time.sleep(10)
                else:
                    break

            # 提前结束
            if tool.is_process_end() > 0:
                break

            # 开始下载
            thread = Download(account_list[account_id])
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            time.sleep(10)

        # 未完成的数据保存
        if len(ACCOUNTS) > 0:
            new_save_data_file = open(NEW_SAVE_DATA_PATH, "a")
            for account_id in ACCOUNTS:
                # account_id  image_count  last_diary_id
                new_save_data_file.write("\t".join(account_list[account_id]) + "\n")
            new_save_data_file.close()

        # 删除临时文件夹
        tool.remove_dir(IMAGE_TEMP_PATH)

        # 重新排序保存存档文件
        account_list = robot.read_save_data(NEW_SAVE_DATA_PATH, 0, [])
        temp_list = [account_list[key] for key in sorted(account_list.keys())]
        tool.write_file(tool.list_to_string(temp_list), self.save_data_path, 2)
        os.remove(NEW_SAVE_DATA_PATH)

        duration_time = int(time.time() - start_time)
        print_step_msg("全部下载完毕，耗时%s秒，共计图片%s张" % (duration_time, TOTAL_IMAGE_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info):
        threading.Thread.__init__(self)
        self.account_info = account_info

    def run(self):
        global TOTAL_IMAGE_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 4 and self.account_info[3]:
            account_name = self.account_info[3]
        else:
            account_name = self.account_info[0]

        try:
            print_step_msg(account_name + " 开始")

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                image_path = os.path.join(IMAGE_TEMP_PATH, account_name)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)

            image_count = 1
            page_count = 1
            first_diary_id = "0"
            is_over = False
            need_make_image_dir = True
            while not is_over:
                # 获取指定时间点后的一页图片信息
                diary_list = get_diary_page_data(account_id, page_count)
                if diary_list is None:
                    print_error_msg(account_name + " 第%s页日志列表解析异常" % page_count)
                    tool.process_exit()

                # 没有获取到任何日志，所有日志已经全部获取完毕了
                if len(diary_list) == 0:
                    break

                for diary_info in diary_list:
                    diary_id = tool.find_sub_string(diary_info, "id=", "&")
                    # 检查是否是上一次的最后视频
                    if int(diary_id) <= int(self.account_info[2]):
                        is_over = True
                        break

                    # 将第一个日志的id做为新的存档记录
                    if first_diary_id == "0":
                        first_diary_id = diary_id

                    trace(account_name + " 日志id %s" % diary_id)

                    diary_info = tool.find_sub_string(diary_info, '<div class="box-article">', '<div class="box-bottom">')
                    # 日志中所有的图片
                    image_list = re.findall('<img src="([^"]*)"', diary_info)
                    for image_url in image_list:
                        if image_url[:7] != "http://" and image_url[:8] != "https://":
                            # 直接使用当前域名下的资源
                            if image_url[0] == "/":
                                image_url = "http://www.keyakizaka46.com%s" % image_url
                            else:
                                image_url = "http://www.keyakizaka46.com/%s" % image_url

                        print_step_msg(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))
                        
                        # 第一张图片，创建目录
                        if need_make_image_dir:
                            if not tool.make_dir(image_path, 0):
                                print_error_msg(account_name + " 创建图片下载目录 %s 失败" % image_path)
                                tool.process_exit()
                            need_make_image_dir = False

                        file_type = image_url.split(".")[-1]
                        file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))

                        if tool.save_net_file(image_url, file_path):
                            print_step_msg(account_name + " 第%s张图片下载成功" % image_count)
                            image_count += 1
                        else:
                            print_error_msg(account_name + " 第%s张图片 %s 获取失败" % (image_count, image_url))

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_IMAGE_COUNT < image_count:
                        is_over = True
                        break

                if not is_over:
                    page_count += 1

            print_step_msg(account_name + " 下载完毕，总共获得%s张图片" % (image_count - 1))

            # 排序
            if IS_SORT and image_count > 1:
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                    print_step_msg(account_name + " 图片从下载目录移动到保存目录成功")
                else:
                    print_error_msg(account_name + " 创建图片子目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_diary_id != "0":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = first_diary_id

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += image_count - 1
            ACCOUNTS.remove(account_id)
            threadLock.release()

            print_step_msg(account_name + " 完成")
        except SystemExit, se:
            if se.code == 0:
                print_step_msg(account_name + " 提前退出")
            else:
                print_error_msg(account_name + " 异常退出")
        except Exception, e:
            print_error_msg(account_name + " 未知异常")
            print_error_msg(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    Diary().main()