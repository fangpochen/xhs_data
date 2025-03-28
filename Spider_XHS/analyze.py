import json
import pandas as pd
from collections import Counter
from typing import List, Dict, Any
from loguru import logger

class LoanAnalyzer:
    def __init__(self, data_file: str = 'loan_data.json'):
        self.data_file = data_file
        self.data = self.load_data()
        
    def load_data(self) -> List[Dict[str, Any]]:
        """加载数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            return []
            
    def analyze_user_profile(self) -> Dict[str, Any]:
        """分析用户画像"""
        users = []
        for item in self.data:
            user = item['user']
            users.append({
                'user_id': user['user_id'],
                'nickname': user['nickname'],
                'followers': user['followers'],
                'following': user['following'],
                'desc': user['desc'],
            })
            
        df = pd.DataFrame(users)
        
        return {
            'total_users': len(users),
            'avg_followers': df['followers'].mean(),
            'avg_following': df['following'].mean(),
            'top_keywords': self.analyze_keywords(),
            'user_distribution': self.analyze_user_distribution(df),
        }
        
    def analyze_keywords(self) -> List[Dict[str, int]]:
        """分析关键词分布"""
        keywords = [item['keyword'] for item in self.data]
        return [{'keyword': k, 'count': v} for k, v in Counter(keywords).most_common()]
        
    def analyze_user_distribution(self, df: pd.DataFrame) -> Dict[str, int]:
        """分析用户分布"""
        return {
            'high_followers': len(df[df['followers'] > 1000]),
            'medium_followers': len(df[(df['followers'] > 100) & (df['followers'] <= 1000)]),
            'low_followers': len(df[df['followers'] <= 100]),
        }
        
    def analyze_comments(self) -> Dict[str, Any]:
        """分析评论"""
        comments = []
        for item in self.data:
            comments.extend(item['comments'])
            
        df = pd.DataFrame(comments)
        
        return {
            'total_comments': len(comments),
            'unique_users': len(df['user_id'].unique()),
            'comment_distribution': self.analyze_comment_distribution(df),
        }
        
    def analyze_comment_distribution(self, df: pd.DataFrame) -> Dict[str, int]:
        """分析评论分布"""
        return {
            'high_activity': len(df[df['content'].str.len() > 50]),
            'medium_activity': len(df[(df['content'].str.len() > 20) & (df['content'].str.len() <= 50)]),
            'low_activity': len(df[df['content'].str.len() <= 20]),
        }
        
    def generate_report(self):
        """生成分析报告"""
        report = {
            'user_profile': self.analyze_user_profile(),
            'comments_analysis': self.analyze_comments(),
            'summary': {
                'total_notes': len(self.data),
                'total_users': len(set(item['user']['user_id'] for item in self.data)),
                'total_comments': sum(len(item['comments']) for item in self.data),
            }
        }
        
        # 保存报告
        with open('loan_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        logger.info("分析报告已生成: loan_analysis_report.json")
        return report

if __name__ == '__main__':
    analyzer = LoanAnalyzer()
    report = analyzer.generate_report()
    print(json.dumps(report, ensure_ascii=False, indent=2)) 