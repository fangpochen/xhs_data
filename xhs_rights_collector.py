#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书维权退保数据采集脚本
用途：自动采集医美/男科等领域的维权/退保/投诉相关内容
可部署于服务器定时执行
"""

import os
import sys
import time
import json
import random
import argparse
import schedule
import pandas as pd
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

# 将Spider_XHS项目路径加入到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "Spider_XHS"))

# 导入Spider_XHS中的相关模块
from Spider_XHS.apis.pc_apis import XHS_Apis
from Spider_XHS.xhs_utils.common_utils import init
from Spider_XHS.xhs_utils.data_util import handle_note_info, download_note, save_to_xlsx


class RightsProtectionCollector:
    """维权数据采集器"""
    
    def __init__(self, base_dir=None, log_level="INFO"):
        """
        初始化采集器
        :param base_dir: 数据存储的基础目录，默认为脚本所在目录下的data文件夹
        :param log_level: 日志级别
        """
        # 设置存储路径
        if base_dir is None:
            base_dir = os.path.join(current_dir, "data")
        
        # 创建数据存储目录
        self.base_dir = base_dir
        self.data_dir = os.path.join(base_dir, "rights_protection")
        self.excel_dir = os.path.join(self.data_dir, "excel")
        self.media_dir = os.path.join(self.data_dir, "media")
        self.log_dir = os.path.join(self.data_dir, "logs")
        
        for directory in [self.data_dir, self.excel_dir, self.media_dir, self.log_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # 配置日志
        self._setup_logger(log_level)
        
        # 加载环境变量
        load_dotenv()
        
        # 初始化Spider_XHS
        self.cookies_str = os.getenv("COOKIES")
        if not self.cookies_str:
            logger.error("Cookie未设置，请在.env文件中设置COOKIES")
            raise ValueError("Cookie未设置")
        
        self.base_path = {
            "excel": self.excel_dir,
            "media": self.media_dir,
        }
        
        # 创建Spider_XHS的API实例
        self.xhs_apis = XHS_Apis()
        
        # 定义关键词列表
        # 医美领域关键词
        self.medical_beauty_keywords = [
            "医美维权", "整形失败", "医美退款", "医美投诉", 
            "整容后悔", "医美纠纷", "注射失败", "整形退款",
            "医美诈骗", "双眼皮失败", "隆鼻失败", "注射事故",
            "医美后遗症", "医美协商", "整形医院投诉", "医美索赔"
        ]
        
        # 男科领域关键词
        self.male_health_keywords = [
            "男科维权", "男科骗局", "男科退款", "保健品骗局", 
            "男科医院投诉", "保健品退款", "男科产品退款", "男科虚假宣传",
            "男科欺诈", "前列腺骗局", "男性保健投诉", "男科药物退款",
            "男科治疗失败", "壮阳产品投诉", "男科产品投诉", "男科诈骗"
        ]
        
        # 综合维权关键词
        self.general_rights_keywords = [
            "消费维权", "退款维权", "商家欺骗", "消费陷阱",
            "消协投诉", "如何退款", "退款技巧", "消费者权益",
            "315投诉", "消费骗局", "行政投诉", "维权经验",
            "投诉有效", "索赔成功", "退款成功", "维权攻略"
        ]
        
        # 需要追踪的用户ID
        self.target_users = []
        
        logger.info("维权数据采集器初始化完成")
    
    def _setup_logger(self, log_level):
        """配置日志"""
        log_file = os.path.join(
            self.log_dir, 
            f"collector_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        # 移除默认的sink
        logger.remove()
        
        # 添加控制台和文件输出
        logger.add(sys.stderr, level=log_level)
        logger.add(
            log_file, 
            level=log_level, 
            rotation="500 MB", 
            retention="10 days",
            compression="zip"
        )
    
    def collect_by_keywords(self, keywords_list, category_name, notes_per_keyword=30, 
                           sort="general", note_type=0, save_choice="all"):
        """
        按关键词采集数据
        :param keywords_list: 关键词列表
        :param category_name: 分类名称，用于文件夹组织
        :param notes_per_keyword: 每个关键词采集的笔记数量
        :param sort: 排序方式，可选 "general"(综合), "popularity_descending"(热度), "time_descending"(最新)
        :param note_type: 笔记类型，0:全部, 1:视频, 2:图文
        :param save_choice: 保存方式，all: 全部, excel: 仅Excel, media: 仅媒体文件
        :return: 采集到的数据统计
        """
        category_dir = os.path.join(self.excel_dir, category_name)
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)
        
        stats = {
            "total_keywords": len(keywords_list),
            "successful_keywords": 0,
            "total_notes": 0,
            "failed_keywords": [],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.info(f"开始采集 {category_name} 类别的关键词，共 {len(keywords_list)} 个")
        
        for idx, keyword in enumerate(keywords_list):
            logger.info(f"正在采集关键词 [{idx+1}/{len(keywords_list)}]: {keyword}")
            
            try:
                # 采集数据
                success, msg, notes = self.xhs_apis.search_some_note(
                    keyword, 
                    notes_per_keyword, 
                    self.cookies_str, 
                    sort, 
                    note_type,
                    None  # 不使用代理
                )
                
                if not success:
                    logger.error(f"采集关键词 {keyword} 失败: {msg}")
                    stats["failed_keywords"].append({
                        "keyword": keyword,
                        "reason": str(msg)
                    })
                    continue
                
                # 过滤笔记
                valid_notes = list(filter(lambda x: x['model_type'] == "note", notes))
                logger.info(f"关键词 {keyword} 成功采集到 {len(valid_notes)} 条笔记")
                
                if not valid_notes:
                    logger.warning(f"关键词 {keyword} 没有找到有效笔记")
                    continue
                
                # 构建笔记URL列表
                note_urls = []
                for note in valid_notes:
                    note_url = f"https://www.xiaohongshu.com/explore/{note['id']}?xsec_token={note['xsec_token']}"
                    note_urls.append(note_url)
                
                # 保存数据
                self._save_notes(note_urls, category_name, keyword, save_choice)
                
                stats["successful_keywords"] += 1
                stats["total_notes"] += len(valid_notes)
                
                # 随机延迟，避免请求过于频繁
                sleep_time = random.uniform(3, 8)
                logger.debug(f"休息 {sleep_time:.2f} 秒")
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.exception(f"处理关键词 {keyword} 时发生错误: {str(e)}")
                stats["failed_keywords"].append({
                    "keyword": keyword,
                    "reason": str(e)
                })
                continue
        
        # 保存统计信息
        stats_file = os.path.join(
            self.data_dir, 
            f"stats_{category_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"{category_name} 类别采集完成，成功: {stats['successful_keywords']}/{stats['total_keywords']}，"
                   f"共采集 {stats['total_notes']} 条笔记")
        
        return stats
    
    def _save_notes(self, note_urls, category, keyword, save_choice="all"):
        """
        保存笔记数据
        :param note_urls: 笔记URL列表
        :param category: 分类名称
        :param keyword: 关键词
        :param save_choice: 保存方式
        """
        note_list = []
        
        # 设置分类目录
        category_excel_dir = os.path.join(self.excel_dir, category)
        category_media_dir = os.path.join(self.media_dir, category, keyword)
        
        if not os.path.exists(category_excel_dir):
            os.makedirs(category_excel_dir)
        
        if (save_choice == "all" or save_choice == "media") and not os.path.exists(category_media_dir):
            os.makedirs(category_media_dir)
        
        # 更新base_path
        base_path = {
            "excel": category_excel_dir,
            "media": category_media_dir
        }
        
        # 采集每个笔记的详情
        for i, note_url in enumerate(note_urls):
            try:
                logger.debug(f"获取第 {i+1}/{len(note_urls)} 个笔记: {note_url}")
                
                success, msg, note_info = self.xhs_apis.get_note_info(note_url, self.cookies_str, None)
                
                if not success or not note_info:
                    logger.warning(f"获取笔记 {note_url} 失败: {msg}")
                    continue
                
                # 提取笔记信息
                note_data = note_info['data']['items'][0]
                note_data['url'] = note_url
                note_data = handle_note_info(note_data)
                
                # 添加额外分类信息
                note_data['search_keyword'] = keyword
                note_data['category'] = category
                note_data['collect_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                note_list.append(note_data)
                
                # 随机延迟
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.exception(f"处理笔记 {note_url} 时发生错误: {str(e)}")
                continue
        
        if not note_list:
            logger.warning(f"关键词 {keyword} 没有成功获取到笔记详情")
            return
        
        # 保存媒体文件
        if save_choice == "all" or save_choice == "media":
            for note_info in note_list:
                try:
                    download_note(note_info, base_path['media'])
                except Exception as e:
                    logger.exception(f"下载笔记媒体 {note_info.get('note_id', '未知')} 时发生错误: {str(e)}")
        
        # 保存Excel
        if save_choice == "all" or save_choice == "excel":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(base_path['excel'], f"{keyword}_{timestamp}.xlsx")
            try:
                save_to_xlsx(note_list, file_path)
                logger.info(f"成功保存到Excel: {file_path}")
            except Exception as e:
                logger.exception(f"保存Excel {file_path} 时发生错误: {str(e)}")
    
    def collect_by_user(self, user_url, category_name="known_users", save_choice="all"):
        """
        采集指定用户的所有笔记
        :param user_url: 用户URL
        :param category_name: 分类名称
        :param save_choice: 保存方式
        :return: 成功采集的笔记数量
        """
        user_id = user_url.split('/')[-1].split('?')[0]
        logger.info(f"开始采集用户 {user_id} 的笔记")
        
        # 设置分类目录
        category_excel_dir = os.path.join(self.excel_dir, category_name)
        category_media_dir = os.path.join(self.media_dir, category_name, user_id)
        
        if not os.path.exists(category_excel_dir):
            os.makedirs(category_excel_dir)
        
        if (save_choice == "all" or save_choice == "media") and not os.path.exists(category_media_dir):
            os.makedirs(category_media_dir)
        
        base_path = {
            "excel": category_excel_dir,
            "media": category_media_dir
        }
        
        try:
            # 获取用户信息
            success, msg, user_info = self.xhs_apis.get_user_info(user_url, self.cookies_str, None)
            if not success:
                logger.error(f"获取用户信息失败: {msg}")
                return 0
            
            # 获取用户所有笔记
            success, msg, all_notes = self.xhs_apis.get_user_all_notes(user_url, self.cookies_str, None)
            if not success:
                logger.error(f"获取用户笔记失败: {msg}")
                return 0
            
            logger.info(f"用户 {user_id} 共有 {len(all_notes)} 条笔记")
            
            # 构建笔记URL列表
            note_urls = []
            for note in all_notes:
                note_url = f"https://www.xiaohongshu.com/explore/{note['note_id']}?xsec_token={note['xsec_token']}"
                note_urls.append(note_url)
            
            # 保存所有笔记
            self._save_notes(note_urls, category_name, user_id, save_choice)
            
            return len(all_notes)
            
        except Exception as e:
            logger.exception(f"采集用户 {user_id} 时发生错误: {str(e)}")
            return 0
    
    def run_scheduled_collection(self, schedule_time="03:00", keywords_per_run=5):
        """
        定时采集
        :param schedule_time: 每天执行的时间，格式为"HH:MM"
        :param keywords_per_run: 每次执行采集的关键词数量
        """
        def job():
            logger.info(f"开始定时任务，采集每个类别 {keywords_per_run} 个关键词")
            
            # 随机选择指定数量的关键词
            medical_keywords = random.sample(self.medical_beauty_keywords, min(keywords_per_run, len(self.medical_beauty_keywords)))
            male_keywords = random.sample(self.male_health_keywords, min(keywords_per_run, len(self.male_health_keywords)))
            general_keywords = random.sample(self.general_rights_keywords, min(keywords_per_run, len(self.general_rights_keywords)))
            
            # 采集关键词数据
            self.collect_by_keywords(medical_keywords, "medical_beauty", notes_per_keyword=30, sort="general")
            time.sleep(random.uniform(60, 120))  # 类别之间休息一段时间
            
            self.collect_by_keywords(male_keywords, "male_health", notes_per_keyword=30, sort="general")
            time.sleep(random.uniform(60, 120))
            
            self.collect_by_keywords(general_keywords, "general_rights", notes_per_keyword=30, sort="general")
            
            # 如果有目标用户，也采集用户数据
            if self.target_users:
                for user_url in self.target_users:
                    self.collect_by_user(user_url)
                    time.sleep(random.uniform(30, 60))
            
            logger.info("定时任务完成")
        
        # 设置定时任务
        schedule.every().day.at(schedule_time).do(job)
        
        logger.info(f"已设置定时任务，将在每天 {schedule_time} 执行")
        
        # 运行定时循环
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    
    def collect_all_keywords(self):
        """采集所有关键词数据"""
        logger.info("开始采集所有关键词数据")
        
        # 医美领域
        self.collect_by_keywords(
            self.medical_beauty_keywords, 
            "medical_beauty", 
            notes_per_keyword=30, 
            sort="general"
        )
        
        # 男科领域
        self.collect_by_keywords(
            self.male_health_keywords, 
            "male_health", 
            notes_per_keyword=30, 
            sort="general"
        )
        
        # 综合维权
        self.collect_by_keywords(
            self.general_rights_keywords, 
            "general_rights", 
            notes_per_keyword=30, 
            sort="general"
        )
        
        logger.info("所有关键词采集完成")
    
    def set_target_users(self, user_urls):
        """设置需要跟踪的用户列表"""
        self.target_users = user_urls
        logger.info(f"已设置 {len(user_urls)} 个目标用户")


def parse_args():
    parser = argparse.ArgumentParser(description="小红书维权数据采集工具")
    parser.add_argument("--mode", type=str, default="once", choices=["once", "schedule"],
                      help="运行模式：once(一次性运行)，schedule(定时运行)")
    parser.add_argument("--category", type=str, default="all", 
                      choices=["all", "medical_beauty", "male_health", "general_rights"],
                      help="采集类别：all(全部)，medical_beauty(医美)，male_health(男科)，general_rights(综合维权)")
    parser.add_argument("--schedule_time", type=str, default="03:00",
                      help="定时运行时间，格式为HH:MM")
    parser.add_argument("--keywords_per_run", type=int, default=5,
                      help="每次定时任务采集的关键词数量")
    parser.add_argument("--data_dir", type=str, default=None,
                      help="数据保存目录，默认为脚本所在目录下的data文件夹")
    parser.add_argument("--log_level", type=str, default="INFO",
                      choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      help="日志级别")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # 初始化采集器
    collector = RightsProtectionCollector(base_dir=args.data_dir, log_level=args.log_level)
    
    # 设置目标用户 - 这里可以添加专注于维权的用户
    target_users = [
        # 这里添加维权领域的KOL用户主页地址
        # 如: "https://www.xiaohongshu.com/user/profile/用户ID"
    ]
    collector.set_target_users(target_users)
    
    if args.mode == "once":
        if args.category == "all":
            collector.collect_all_keywords()
        elif args.category == "medical_beauty":
            collector.collect_by_keywords(
                collector.medical_beauty_keywords, 
                "medical_beauty", 
                notes_per_keyword=30, 
                sort="general"
            )
        elif args.category == "male_health":
            collector.collect_by_keywords(
                collector.male_health_keywords, 
                "male_health", 
                notes_per_keyword=30, 
                sort="general"
            )
        elif args.category == "general_rights":
            collector.collect_by_keywords(
                collector.general_rights_keywords, 
                "general_rights", 
                notes_per_keyword=30, 
                sort="general"
            )
    elif args.mode == "schedule":
        collector.run_scheduled_collection(
            schedule_time=args.schedule_time,
            keywords_per_run=args.keywords_per_run
        ) 