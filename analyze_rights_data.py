#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书维权数据分析工具
用途：分析采集到的维权相关数据，生成报告和可视化结果
"""

import os
import sys
import json
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import jieba
import jieba.analyse
from wordcloud import WordCloud
from datetime import datetime
import argparse
from collections import Counter

# 设置中文字体
try:
    font_path = 'SimHei.ttf'  # 系统中文字体路径，Linux和Windows路径可能不同
    font = FontProperties(fname=font_path)
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置字体
    plt.rcParams['axes.unicode_minus'] = False    # 正常显示负号
except:
    print("警告: 未找到中文字体文件，图表中的中文可能无法正确显示")


class RightsDataAnalyzer:
    """维权数据分析器"""
    
    def __init__(self, data_dir=None):
        """
        初始化分析器
        :param data_dir: 数据目录，默认为当前目录下的data文件夹
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if data_dir is None:
            data_dir = os.path.join(current_dir, "data", "rights_protection")
        
        self.data_dir = data_dir
        self.excel_dir = os.path.join(data_dir, "excel")
        self.output_dir = os.path.join(data_dir, "analysis")
        
        # 创建分析结果输出目录
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 分类目录
        self.categories = ["medical_beauty", "male_health", "general_rights"]
        
        # 停用词列表
        self.stopwords = self._load_stopwords()
        
        # 加载行业特定词汇
        jieba.load_userdict(os.path.join(current_dir, "industry_dict.txt"))
        
        print(f"数据分析器初始化完成，数据目录: {self.data_dir}")
    
    def _load_stopwords(self):
        """加载停用词"""
        stopwords = set()
        # 基本停用词
        basic_stopwords = [
            "的", "了", "和", "是", "就", "都", "而", "及", "与", "这", "那", "你", "我", "他", 
            "们", "会", "过", "可以", "还是", "还有", "只是", "但是", "就是", "这个", "那个", 
            "一个", "现在", "因为", "所以", "如果", "已经", "不是", "这样", "那样", "这些", 
            "那些", "怎么", "什么", "为什么", "怎么样", "这么", "那么", "一些", "有些"
        ]
        stopwords.update(basic_stopwords)
        return stopwords
    
    def load_all_data(self):
        """
        加载所有Excel数据
        :return: 包含所有数据的DataFrame
        """
        all_data = []
        
        for category in self.categories:
            category_dir = os.path.join(self.excel_dir, category)
            if not os.path.exists(category_dir):
                print(f"警告: 目录不存在 {category_dir}")
                continue
                
            excel_files = glob.glob(os.path.join(category_dir, "*.xlsx"))
            print(f"在 {category} 类别中找到 {len(excel_files)} 个Excel文件")
            
            for excel_file in excel_files:
                try:
                    df = pd.read_excel(excel_file)
                    # 添加类别信息
                    if 'category' not in df.columns:
                        df['category'] = category
                    if 'search_keyword' not in df.columns:
                        keyword = os.path.basename(excel_file).split('_')[0]
                        df['search_keyword'] = keyword
                    
                    all_data.append(df)
                except Exception as e:
                    print(f"无法读取文件 {excel_file}: {str(e)}")
        
        if not all_data:
            print("错误: 未找到数据文件")
            return None
            
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"共加载 {len(combined_df)} 条记录")
        return combined_df
    
    def analyze_text(self, df, text_column='desc', top_n=20):
        """
        分析文本内容
        :param df: 数据框
        :param text_column: 要分析的文本列
        :param top_n: 返回前N个高频词
        :return: 词频统计
        """
        if df is None or len(df) == 0:
            return {}
            
        # 合并所有文本
        all_text = ' '.join(df[text_column].dropna().astype(str))
        
        # 使用jieba进行分词和关键词提取
        words = jieba.cut(all_text)
        words = [word for word in words if word not in self.stopwords and len(word) > 1]
        
        # 计算词频
        word_freq = Counter(words)
        top_words = word_freq.most_common(top_n)
        
        # 提取关键词 (TF-IDF)
        keywords_tfidf = jieba.analyse.extract_tags(all_text, topK=top_n, withWeight=True)
        
        # 提取关键词 (TextRank)
        keywords_textrank = jieba.analyse.textrank(all_text, topK=top_n, withWeight=True)
        
        return {
            'word_freq': top_words,
            'keywords_tfidf': keywords_tfidf,
            'keywords_textrank': keywords_textrank
        }
    
    def generate_wordcloud(self, text_analysis, title, output_file):
        """
        生成词云图
        :param text_analysis: 文本分析结果
        :param title: 词云标题
        :param output_file: 输出文件路径
        """
        # 使用词频数据
        word_freq = dict(text_analysis['word_freq'])
        
        # 创建词云
        wordcloud = WordCloud(
            font_path='SimHei.ttf',  # 使用中文字体
            width=800, 
            height=400,
            background_color='white',
            max_words=100,
            max_font_size=150,
            random_state=42
        ).generate_from_frequencies(word_freq)
        
        # 绘制词云图
        plt.figure(figsize=(12, 8))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(title, fontsize=20)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300)
        plt.close()
        
        print(f"词云图已保存至: {output_file}")
    
    def analyze_user_metrics(self, df):
        """
        分析用户指标
        :param df: 数据框
        :return: 用户指标统计
        """
        if df is None or len(df) == 0:
            return {}
            
        metrics = {}
        
        # 按类别统计
        if 'category' in df.columns:
            category_counts = df['category'].value_counts().to_dict()
            metrics['category_distribution'] = category_counts
        
        # 按关键词统计
        if 'search_keyword' in df.columns:
            keyword_counts = df['search_keyword'].value_counts().head(20).to_dict()
            metrics['keyword_distribution'] = keyword_counts
        
        # 点赞数统计
        if 'like_count' in df.columns:
            metrics['avg_likes'] = df['like_count'].mean()
            metrics['max_likes'] = df['like_count'].max()
            
            # 最受欢迎的帖子
            top_liked = df.sort_values('like_count', ascending=False).head(10)
            metrics['top_liked_posts'] = top_liked[['note_id', 'title', 'like_count', 'url']].to_dict('records')
        
        # 评论数统计
        if 'comment_count' in df.columns:
            metrics['avg_comments'] = df['comment_count'].mean()
            metrics['max_comments'] = df['comment_count'].max()
            
            # 讨论最热烈的帖子
            top_commented = df.sort_values('comment_count', ascending=False).head(10)
            metrics['top_commented_posts'] = top_commented[['note_id', 'title', 'comment_count', 'url']].to_dict('records')
        
        # 收藏数统计
        if 'collect_count' in df.columns:
            metrics['avg_collects'] = df['collect_count'].mean()
            metrics['max_collects'] = df['collect_count'].max()
        
        # 用户分析
        if 'user_name' in df.columns:
            user_post_counts = df['user_name'].value_counts().head(20).to_dict()
            metrics['top_users'] = user_post_counts
        
        return metrics
    
    def plot_metrics(self, metrics, output_dir):
        """
        绘制指标图表
        :param metrics: 指标数据
        :param output_dir: 输出目录
        """
        if not metrics:
            return
            
        # 类别分布图
        if 'category_distribution' in metrics:
            plt.figure(figsize=(10, 6))
            categories = list(metrics['category_distribution'].keys())
            counts = list(metrics['category_distribution'].values())
            
            plt.bar(categories, counts)
            plt.title('各类别数据分布')
            plt.xlabel('类别')
            plt.ylabel('数量')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'category_distribution.png'), dpi=300)
            plt.close()
        
        # 关键词分布图
        if 'keyword_distribution' in metrics:
            plt.figure(figsize=(12, 8))
            keywords = list(metrics['keyword_distribution'].keys())
            counts = list(metrics['keyword_distribution'].values())
            
            # 按数量排序
            sorted_indices = np.argsort(counts)[::-1]
            keywords = [keywords[i] for i in sorted_indices]
            counts = [counts[i] for i in sorted_indices]
            
            plt.bar(keywords[:15], counts[:15])
            plt.title('热门关键词分布 (Top 15)')
            plt.xlabel('关键词')
            plt.ylabel('数量')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'keyword_distribution.png'), dpi=300)
            plt.close()
        
        # 用户分布图
        if 'top_users' in metrics:
            plt.figure(figsize=(12, 8))
            users = list(metrics['top_users'].keys())
            counts = list(metrics['top_users'].values())
            
            # 按数量排序
            sorted_indices = np.argsort(counts)[::-1]
            users = [users[i] for i in sorted_indices]
            counts = [counts[i] for i in sorted_indices]
            
            plt.bar(users[:10], counts[:10])
            plt.title('最活跃用户 (Top 10)')
            plt.xlabel('用户')
            plt.ylabel('发布笔记数')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'top_users.png'), dpi=300)
            plt.close()
    
    def generate_report(self, df, text_analysis, metrics):
        """
        生成分析报告
        :param df: 数据框
        :param text_analysis: 文本分析结果
        :param metrics: 用户指标统计
        :return: 报告HTML内容
        """
        if df is None or len(df) == 0:
            return "没有数据可供分析"
            
        # 基本统计信息
        total_notes = len(df)
        total_categories = len(metrics.get('category_distribution', {}))
        total_keywords = len(metrics.get('keyword_distribution', {}))
        
        # 生成时间
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 高频词和关键词
        top_words = ""
        for word, count in text_analysis.get('word_freq', [])[:20]:
            top_words += f"<tr><td>{word}</td><td>{count}</td></tr>"
        
        top_keywords = ""
        for word, weight in text_analysis.get('keywords_tfidf', [])[:20]:
            top_keywords += f"<tr><td>{word}</td><td>{weight:.4f}</td></tr>"
        
        # 热门帖子
        top_liked_posts = ""
        for post in metrics.get('top_liked_posts', []):
            title = post.get('title', '无标题')
            likes = post.get('like_count', 0)
            url = post.get('url', '')
            top_liked_posts += f"<tr><td><a href='{url}' target='_blank'>{title}</a></td><td>{likes}</td></tr>"
        
        # 生成HTML报告
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>小红书维权数据分析报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
                h1, h2, h3 {{ color: #d81e06; }}
                h1 {{ border-bottom: 2px solid #d81e06; padding-bottom: 10px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ text-align: left; padding: 12px; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .image-container {{ margin: 20px 0; text-align: center; }}
                img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>小红书维权数据分析报告</h1>
                <p>生成时间: {now}</p>
                
                <div class="summary">
                    <h2>数据概览</h2>
                    <p>总笔记数量: <strong>{total_notes}</strong></p>
                    <p>分析类别数量: <strong>{total_categories}</strong></p>
                    <p>分析关键词数量: <strong>{total_keywords}</strong></p>
                    <p>平均点赞数: <strong>{metrics.get('avg_likes', 0):.2f}</strong></p>
                    <p>平均评论数: <strong>{metrics.get('avg_comments', 0):.2f}</strong></p>
                    <p>平均收藏数: <strong>{metrics.get('avg_collects', 0):.2f}</strong></p>
                </div>
                
                <h2>文本分析</h2>
                <h3>高频词汇 (Top 20)</h3>
                <table>
                    <tr>
                        <th>词汇</th>
                        <th>出现次数</th>
                    </tr>
                    {top_words}
                </table>
                
                <h3>关键词分析 (TF-IDF)</h3>
                <table>
                    <tr>
                        <th>关键词</th>
                        <th>权重</th>
                    </tr>
                    {top_keywords}
                </table>
                
                <div class="image-container">
                    <h3>词云图</h3>
                    <img src="wordcloud.png" alt="词云图">
                </div>
                
                <h2>交互指标分析</h2>
                <h3>点赞最多的笔记</h3>
                <table>
                    <tr>
                        <th>标题</th>
                        <th>点赞数</th>
                    </tr>
                    {top_liked_posts}
                </table>
                
                <div class="image-container">
                    <h3>类别分布</h3>
                    <img src="category_distribution.png" alt="类别分布">
                </div>
                
                <div class="image-container">
                    <h3>关键词分布</h3>
                    <img src="keyword_distribution.png" alt="关键词分布">
                </div>
                
                <div class="image-container">
                    <h3>最活跃用户</h3>
                    <img src="top_users.png" alt="最活跃用户">
                </div>
                
                <h2>结论与建议</h2>
                <p>1. 根据词频和关键词分析，用户在维权话题中最关注的问题是【数据驱动的见解】</p>
                <p>2. 医美和男科领域的维权帖子普遍获得较高的互动率，说明这两个领域的消费者维权意识较强</p>
                <p>3. 建议关注词云中的高频词对应的行业问题，针对性地开展维权工作</p>
                <p>4. 可以进一步分析高点赞帖子的内容特点，了解有效维权的方法和途径</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def run_analysis(self):
        """运行数据分析流程"""
        # 1. 加载数据
        df = self.load_all_data()
        if df is None:
            print("错误: 未能加载数据")
            return False
        
        # 2. 文本分析
        text_analysis = self.analyze_text(df, text_column='desc', top_n=50)
        
        # 3. 用户指标分析
        user_metrics = self.analyze_user_metrics(df)
        
        # 4. 生成词云
        self.generate_wordcloud(
            text_analysis, 
            "维权数据关键词词云", 
            os.path.join(self.output_dir, "wordcloud.png")
        )
        
        # 5. 绘制指标图表
        self.plot_metrics(user_metrics, self.output_dir)
        
        # 6. 生成分析报告
        report_html = self.generate_report(df, text_analysis, user_metrics)
        report_file = os.path.join(self.output_dir, "report.html")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        print(f"分析报告已生成: {report_file}")
        
        # 7. 保存分析数据
        analysis_data = {
            'text_analysis': {
                'word_freq': dict(text_analysis.get('word_freq', [])),
                'keywords_tfidf': dict(text_analysis.get('keywords_tfidf', [])),
                'keywords_textrank': dict(text_analysis.get('keywords_textrank', []))
            },
            'user_metrics': user_metrics,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        analysis_file = os.path.join(self.output_dir, "analysis_data.json")
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2)
        
        print(f"分析数据已保存: {analysis_file}")
        
        return True


def parse_args():
    parser = argparse.ArgumentParser(description="小红书维权数据分析工具")
    parser.add_argument("--data_dir", type=str, default=None,
                      help="数据目录路径，默认为当前目录下的data/rights_protection文件夹")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # 创建分析器并运行分析
    analyzer = RightsDataAnalyzer(data_dir=args.data_dir)
    analyzer.run_analysis() 