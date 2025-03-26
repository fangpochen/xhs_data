"""
Spider_XHS测试文件
"""
import pytest
from apis.pc_apis import XHS_Apis

def test_xhs_apis_initialization():
    """测试XHS_Apis初始化"""
    xhs_apis = XHS_Apis()
    assert xhs_apis is not None

def test_note_info_validation():
    """测试笔记信息验证"""
    xhs_apis = XHS_Apis()
    note_url = "https://www.xiaohongshu.com/explore/test"
    success, msg, note_info = xhs_apis.get_note_info(note_url, "", None)
    assert isinstance(success, bool)
    assert isinstance(msg, str)
    assert note_info is None or isinstance(note_info, dict) 