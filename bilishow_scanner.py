#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import json
import sys
import os
import re
from datetime import datetime
from typing import List, Dict, Optional


def get_version():
    try:
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        version_file = os.path.join(base_path, "version_info.txt")
        
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r"StringStruct\(u'ProductVersion',\s*u'([^']+)'\)", content)
                if match:
                    return match.group(1)
        
        return "0.0.0"
    except Exception as e:
        return "未知版本"


def show_muse_banner():
    banner = r"""
          _____                    _____                    _____                    _____          
         /\    \                  /\    \                  /\    \                  /\    \         
        /::\____\                /::\____\                /::\    \                /::\    \        
       /::::|   |               /:::/    /               /::::\    \              /::::\    \       
      /:::::|   |              /:::/    /               /::::::\    \            /::::::\    \      
     /::::::|   |             /:::/    /               /:::/\:::\    \          /:::/\:::\    \     
    /:::/|::|   |            /:::/    /               /:::/__\:::\    \        /:::/__\:::\    \    
   /:::/ |::|   |           /:::/    /                \:::\   \:::\    \      /::::\   \:::\    \   
  /:::/  |::|___|______    /:::/    /      _____    ___\:::\   \:::\    \    /::::::\   \:::\    \  
 /:::/   |::::::::\    \  /:::/____/      /\    \  /\   \:::\   \:::\    \  /:::/\:::\   \:::\    \ 
/:::/    |:::::::::\____\|:::|    /      /::\____\/::\   \:::\   \:::\____\/:::/__\:::\   \:::\____\
\::/    / ~~~~~/:::/    /|:::|____\     /:::/    /\:::\   \:::\   \::/    /\:::\   \:::\   \::/    /
 \/____/      /:::/    /  \:::\    \   /:::/    /  \:::\   \:::\   \/____/  \:::\   \:::\   \/____/ 
             /:::/    /    \:::\    \ /:::/    /    \:::\   \:::\    \       \:::\   \:::\    \     
            /:::/    /      \:::\    /:::/    /      \:::\   \:::\____\       \:::\   \:::\____\    
           /:::/    /        \:::\__/:::/    /        \:::\  /:::/    /        \:::\   \::/    /    
          /:::/    /          \::::::::/    /          \:::\/:::/    /          \:::\   \/____/     
         /:::/    /            \::::::/    /            \::::::/    /            \:::\    \         
        /:::/    /              \::::/    /              \::::/    /              \:::\____\        
        \::/    /                \::/____/                \::/    /                \::/    /        
         \/____/                  ~~                       \/____/                  \/____/                                                                                                        
    """
    print(banner)
    version = get_version()
    print(f"MUSE-BiliShow-Scanner v{version}")
    print("=" * 88)
    print()


class BilibiliShowScanner:
    
    def __init__(self, filters: Dict = None):
        self.api_url = "https://show.bilibili.com/api/ticket/project/getV2?id="
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://show.bilibili.com/',
        })
        self.matched_projects = []
        self.scan_results = []
        self.filters = filters or {}
        
    def get_project_info(self, project_id: int) -> Optional[Dict]:
        try:
            url = f"{self.api_url}{project_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') == 0:
                return data.get('data')
            elif data.get('code') == -404:
                return None
            else:
                print(f"\n[API错误] ID {project_id} - Code: {data.get('code')}, Message: {data.get('message', '未知错误')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"\n[请求失败] ID {project_id}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            print(f"\n[解析失败] ID {project_id}: {str(e)}")
            return None
        except Exception as e:
            print(f"\n[未知错误] ID {project_id}: {str(e)}")
            return None
    
    def scan_project(self, project_id: int) -> Dict:
        result = {
            'id': project_id,
            'match': False,
            'name': None,
            'status': 'unknown',
            'error': None,
            'data': None,
            'sale_start': None,
            'sale_end': None
        }
        
        project_info = self.get_project_info(project_id)
        
        if project_info is None:
            result['status'] = 'not_found'
            return result
        
        result['name'] = project_info.get('name', '未知项目')
        result['status'] = 'success'
        result['data'] = project_info
        result['sale_start'] = project_info.get('sale_start')
        result['sale_end'] = project_info.get('sale_end')
        
        is_match = True
        
        if 'sale_flag' in self.filters and self.filters['sale_flag']:
            if str(project_info.get('sale_flag', '')) not in self.filters['sale_flag']:
                is_match = False
        
        if is_match and 'pick_seat' in self.filters and self.filters['pick_seat']:
            if project_info.get('pick_seat') not in self.filters['pick_seat']:
                is_match = False
                
        if is_match and 'id_bind' in self.filters and self.filters['id_bind']:
            if project_info.get('id_bind') not in self.filters['id_bind']:
                is_match = False
                
        if is_match and 'need_contact' in self.filters and self.filters['need_contact']:
            if project_info.get('need_contact') not in self.filters['need_contact']:
                is_match = False
                
        if is_match and 'delivery_type' in self.filters and self.filters['delivery_type']:
            screen_list = project_info.get('screen_list', [])
            if screen_list:
                delivery_type = screen_list[0].get('delivery_type')
                
                selected_no = '0' in self.filters['delivery_type']
                selected_other = '1' in self.filters['delivery_type']
                
                if selected_no and selected_other:
                    pass
                elif selected_no:
                    if delivery_type != 1:
                        is_match = False
                elif selected_other:
                    if delivery_type == 1:
                        is_match = False
            else:
                is_match = False
            
        if is_match:
            result['match'] = True
            self.matched_projects.append(result)
            
        return result
    
    def scan_backward(self, start_id: int, count: int, interval: float = 0.5):
        print(f"开始向前扫描项目，起始ID: {start_id}，扫描数量: {count}")
        print(f"扫描间隔: {interval}秒")
        print(f"过滤条件: {self.filters}")
        print("-" * 60)
        
        scanned_count = 0
        match_count = 0
        
        start_time = datetime.now()
        
        for i in range(count):
            project_id = start_id - i
            if project_id <= 0:
                break
                
            scanned_count += 1
            
            progress = (scanned_count / count) * 100
            print(f"[{progress:.1f}%] 扫描ID: {project_id}", end=" ")
            
            result = self.scan_project(project_id)
            self.scan_results.append(result)
            
            if result['status'] == 'not_found':
                print("❌ 未找到项目")
            elif result['match']:
                match_count += 1
                start_str = datetime.fromtimestamp(result['sale_start']).strftime('%Y-%m-%d %H:%M') if result['sale_start'] else "未知"
                end_str = datetime.fromtimestamp(result['sale_end']).strftime('%Y-%m-%d %H:%M') if result['sale_end'] else "未知"
                print(f"✅ 匹配: {result['name']} (售票: {start_str} 至 {end_str})")
            else:
                print(f"不匹配: {result['name']}")
            
            if i < count - 1:
                time.sleep(interval)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("-" * 60)
        print("扫描完成!")
        print(f"总耗时: {duration}")
        print(f"扫描总数: {scanned_count}")
        print(f"符合条件项目: {match_count}")
        
        if self.matched_projects:
            print("\n符合条件项目列表:")
            for project in self.matched_projects:
                start_str = datetime.fromtimestamp(project['sale_start']).strftime('%Y-%m-%d %H:%M') if project['sale_start'] else "未知"
                end_str = datetime.fromtimestamp(project['sale_end']).strftime('%Y-%m-%d %H:%M') if project['sale_end'] else "未知"
                print(f"  ID: {project['id']} - {project['name']} (售票: {start_str} 至 {end_str})")
    
    def save_results(self, filename: str = None):
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bilibili_match_results_{timestamp}.json"
        
        results_data = {
            'scan_time': datetime.now().isoformat(),
            'total_scanned': len(self.scan_results),
            'match_count': len(self.matched_projects),
            'filters': self.filters,
            'matched_projects': self.matched_projects
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, ensure_ascii=False, indent=2)
            print(f"\n扫描结果已保存到: {filename}")
        except Exception as e:
            print(f"❌ 保存结果失败: {str(e)}")


def get_user_input():
    while True:
        try:
            start_id = int(input("请输入起始ID: "))
            if start_id <= 0:
                print("❌ 起始ID必须大于0")
                continue
            break
        except ValueError:
            print("❌ 请输入有效的数字")
    
    while True:
        try:
            count = int(input("请输入向前扫描的项目数量: "))
            if count <= 0:
                print("❌ 数量必须大于0")
                continue
            break
        except ValueError:
            print("❌ 请输入有效的数字")

    filters = {}
    print("\n--- 过滤条件设置 (直接回车表示不限制该项, 多选请用逗号/空格分隔) ---")
    
    sale_flag_input = input("售票状态 (例如: 未开售, 预售中, etc.): ").replace(',', ' ').strip()
    if sale_flag_input:
        filters['sale_flag'] = [s.strip() for s in sale_flag_input.split() if s.strip()]
    
    pick_seat_input = input("选座 (0:否, 1:是): ").replace(',', ' ').strip()
    if pick_seat_input:
        filters['pick_seat'] = [int(s) for s in pick_seat_input.split() if s.strip().isdigit()]
        
    id_bind_input = input("实名 (0:否, 1:单实名, 2:多实名): ").replace(',', ' ').strip()
    if id_bind_input:
        filters['id_bind'] = [int(s) for s in id_bind_input.split() if s.strip().isdigit()]
        
    need_contact_input = input("联系人 (0:否, 1:是): ").replace(',', ' ').strip()
    if need_contact_input:
        filters['need_contact'] = [s == '1' for s in need_contact_input.split() if s.strip().isdigit()]
        
    delivery_input = input("邮寄 (0:否, 1:其他): ").replace(',', ' ').strip()
    if delivery_input:
        filters['delivery_type'] = [s.strip() for s in delivery_input.split() if s.strip()]
        
    return start_id, count, filters


def main():
    while True:
        try:
            show_muse_banner()
            
            start_id, count, filters = get_user_input()
            
            scanner = BilibiliShowScanner(filters=filters)
            
            scanner.scan_backward(start_id, count)
            
            if scanner.matched_projects:
                save_choice = input("\n是否保存匹配结果到文件? (y/n): ").lower().strip()
                if save_choice in ['y', 'yes', '是', '保存']:
                    scanner.save_results()
            
            print("\n程序执行完毕!")
            
        except KeyboardInterrupt:
            print("\n\n用户中断扫描")
        except Exception as e:
            import traceback
            print(f"\n❌ 程序执行出错: {str(e)}")
            print("\n完整错误详情:")
            print(traceback.format_exc())
        
        while True:
            choice = input("\n退出(T)/重新开始(S): ").strip().upper()
            if choice == 'T':
                print("程序已退出")
                return
            elif choice == 'S':
                print("\n重新开始程序...\n")
                break
            else:
                print("请输入 T 或 S")


if __name__ == "__main__":
    main()