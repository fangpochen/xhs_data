import json
import time
import random
from typing import List, Dict, Any
from loguru import logger
from .api import XHS
from .utils import load_keywords

class LoanSpider:
    def __init__(self):
        self.api = XHS()
        self.keywords = load_keywords('loan_keywords.txt')
        self.results = []
        
    def search_notes(self, keyword: str, page: int = 1) -> List[Dict[str, Any]]:
        """搜索笔记"""
        try:
            notes = self.api.get_note_by_keyword(keyword, page)
            return notes
        except Exception as e:
            logger.error(f"搜索笔记失败: {e}")
            return []
            
    def get_note_detail(self, note_id: str) -> Dict[str, Any]:
        """获取笔记详情"""
        try:
            detail = self.api.get_note_by_id(note_id)
            return detail
        except Exception as e:
            logger.error(f"获取笔记详情失败: {e}")
            return {}
            
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """获取用户信息"""
        try:
            user = self.api.get_user_info(user_id)
            return user
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return {}
            
    def get_note_comments(self, note_id: str, page: int = 1) -> List[Dict[str, Any]]:
        """获取笔记评论"""
        try:
            comments = self.api.get_note_comments(note_id, page)
            return comments
        except Exception as e:
            logger.error(f"获取笔记评论失败: {e}")
            return []
            
    def collect_data(self):
        """收集数据"""
        for keyword in self.keywords:
            logger.info(f"开始搜索关键词: {keyword}")
            page = 1
            
            while True:
                notes = self.search_notes(keyword, page)
                if not notes:
                    break
                    
                for note in notes:
                    # 获取笔记详情
                    detail = self.get_note_detail(note['id'])
                    if not detail:
                        continue
                        
                    # 获取用户信息
                    user = self.get_user_info(detail['user']['user_id'])
                    
                    # 获取评论
                    comments = self.get_note_comments(note['id'])
                    
                    # 整理数据
                    data = {
                        'note_id': note['id'],
                        'title': detail.get('title', ''),
                        'desc': detail.get('desc', ''),
                        'type': detail.get('type', ''),
                        'user': {
                            'user_id': user.get('user_id', ''),
                            'nickname': user.get('nickname', ''),
                            'desc': user.get('desc', ''),
                            'followers': user.get('followers', 0),
                            'following': user.get('following', 0),
                        },
                        'comments': [{
                            'user_id': comment.get('user', {}).get('user_id', ''),
                            'nickname': comment.get('user', {}).get('nickname', ''),
                            'content': comment.get('content', ''),
                            'time': comment.get('time', ''),
                        } for comment in comments],
                        'keyword': keyword,
                        'collect_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    
                    self.results.append(data)
                    
                    # 随机延迟
                    time.sleep(random.uniform(1, 3))
                    
                page += 1
                time.sleep(random.uniform(2, 4))
                
    def save_data(self, filename: str = 'loan_data.json'):
        """保存数据"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            
    def run(self):
        """运行爬虫"""
        try:
            self.collect_data()
            self.save_data()
        except Exception as e:
            logger.error(f"爬虫运行失败: {e}")

if __name__ == '__main__':
    spider = LoanSpider()
    spider.run() 