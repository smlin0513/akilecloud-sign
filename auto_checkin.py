#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import logging
import os
import sys
import argparse
from datetime import datetime
import schedule
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import warnings
import base64

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("checkin.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 禁用 Selenium 和 urllib3 的警告
warnings.filterwarnings('ignore', category=DeprecationWarning)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('selenium').setLevel(logging.ERROR)
os.environ['WDM_LOG_LEVEL'] = '0'
os.environ['WDM_PRINT_FIRST_LINE'] = 'False'

def get_user_id_from_token(token):
    """从JWT token中解析用户ID"""
    try:
        # 获取payload部分（第二部分）
        payload = token.split('.')[1]
        # 添加padding
        payload += '=' * (-len(payload) % 4)
        # 解码
        decoded = base64.b64decode(payload)
        # 解析JSON
        data = json.loads(decoded)
        return data.get('userId')
    except Exception as e:
        logger.debug(f"从token解析用户ID失败: {str(e)}")
        return None

class AkileCheckin:
    def __init__(self, token=None, token_file=None, debug=False, headless=True):
        self.base_url = "https://akile.io"
        self.debug = debug
        self.headless = headless
        
        # 如果提供了token_file，从文件读取token
        if token_file and os.path.exists(token_file):
            with open(token_file, 'r') as f:
                self.token = f.read().strip()
        else:
            self.token = token
            
        if not self.token:
            raise ValueError("必须提供授权令牌，请通过-t参数或-f参数指定")
        
        # 从token中解析用户ID
        self.user_id = get_user_id_from_token(self.token)
        
        if self.debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug模式已启用")
            if self.user_id:
                logger.debug(f"从token中解析出用户ID: {self.user_id}")
    
    def init_driver(self):
        """初始化浏览器驱动"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--log-level=3')  # 只显示致命错误
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
            })
            
            # 设置localStorage以保存token
            driver.get(self.base_url)
            driver.execute_script(f"localStorage.setItem('token', '{self.token}')")
            
            if self.debug:
                logger.debug("浏览器驱动初始化成功")
            
            return driver
        except Exception as e:
            logger.error(f"初始化浏览器驱动失败: {str(e)}")
            raise
    
    def get_user_info(self, driver):
        """获取用户信息"""
        try:
            driver.get(self.base_url)
            time.sleep(2)  # 等待页面加载
            
            if self.debug:
                logger.debug("正在获取用户信息...")
            
            # 等待用户信息加载
            wait = WebDriverWait(driver, 10)
            user_info = wait.until(lambda d: d.execute_script("""
                return fetch('https://api.akile.io/api/v1/user/info', {
                    headers: {
                        'Authorization': localStorage.getItem('token'),
                        'Content-Type': 'application/json'
                    }
                }).then(r => r.json());
            """))
            
            if self.debug:
                logger.debug(f"用户信息响应: {json.dumps(user_info, ensure_ascii=False)}")
            
            if user_info and user_info.get("status_code") == 0:
                return user_info.get("data")
            else:
                logger.error(f"获取用户信息失败: {user_info.get('status_msg') if user_info else '未知错误'}")
                
        except Exception as e:
            logger.error(f"获取用户信息异常: {str(e)}")
        return None
    
    def checkin(self, driver=None):
        """执行签到操作"""
        should_quit_driver = False
        try:
            if driver is None:
                driver = self.init_driver()
                should_quit_driver = True
            
            logger.info("开始签到...")
            driver.get(self.base_url)
            time.sleep(2)  # 等待页面加载
            
            # 执行签到请求
            result = driver.execute_script("""
                return fetch('https://api.akile.io/api/v1/user/Checkin', {
                    headers: {
                        'Authorization': localStorage.getItem('token'),
                        'Content-Type': 'application/json'
                    }
                }).then(r => r.json());
            """)
            
            if self.debug:
                logger.debug(f"签到响应: {json.dumps(result, ensure_ascii=False)}")
            
            # 检查签到结果
            if result:
                if result.get("status_code") == 0:
                    logger.info(f"签到成功！{result.get('status_msg', '')}")
                    return True
                elif result.get("status_code") == 1 and "今日已签到" in result.get("status_msg", ""):
                    logger.info("今日已签到")
                    return True
                else:
                    logger.warning(f"签到失败: {result.get('status_msg', '未知错误')}")
            else:
                logger.warning("签到失败: 服务器无响应")
            
        except Exception as e:
            logger.error(f"签到过程中发生异常: {str(e)}")
        finally:
            if should_quit_driver and driver:
                driver.quit()
        
        return False

def main():
    parser = argparse.ArgumentParser(description="Akile 自动签到工具")
    parser.add_argument("-t", "--token", help="授权令牌")
    parser.add_argument("-f", "--token-file", help="包含授权令牌的文件路径")
    parser.add_argument("-s", "--schedule", help="设置每日定时签到时间 (格式: HH:MM)", default=None)
    parser.add_argument("--once", action="store_true", help="仅执行一次签到而不是持续运行")
    parser.add_argument("-d", "--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--no-headless", action="store_true", help="显示浏览器界面（默认隐藏）")
    parser.add_argument("-o", "--save-token", help="将授权令牌保存到指定文件")
    
    args = parser.parse_args()
    
    # 如果指定了保存令牌
    if args.save_token and args.token:
        try:
            with open(args.save_token, 'w', encoding='utf-8') as f:
                f.write(args.token)
            logger.info(f"授权令牌已保存到文件: {args.save_token}")
            return
        except Exception as e:
            logger.error(f"保存授权令牌到文件失败: {str(e)}")
            return
    
    try:
        checkin_tool = AkileCheckin(
            token=args.token,
            token_file=args.token_file,
            debug=args.debug,
            headless=not args.no_headless
        )
        
        # 初始化浏览器
        driver = checkin_tool.init_driver()
        
        try:
            # 获取用户信息
            user_info = checkin_tool.get_user_info(driver)
            if user_info:
                logger.info(f"当前登录用户: {user_info.get('username')} (ID: {checkin_tool.user_id})")
                if user_info.get('last_checkin_time'):
                    last_checkin = datetime.fromtimestamp(user_info.get('last_checkin_time'))
                    logger.info(f"上次签到时间: {last_checkin.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 如果是单次运行模式
            if args.once:
                checkin_tool.checkin(driver)
                return
            
            # 设置定时任务
            if args.schedule:
                logger.info(f"设置定时任务，每天 {args.schedule} 进行签到")
                schedule.every().day.at(args.schedule).do(checkin_tool.checkin, driver)
            else:
                # 默认设置为每天早上8:30签到
                default_time = "08:30"
                logger.info(f"未指定时间，默认设置为每天 {default_time} 进行签到")
                schedule.every().day.at(default_time).do(checkin_tool.checkin, driver)
            
            # 启动时先执行一次签到
            checkin_tool.checkin(driver)
            
            # 持续运行定时任务
            logger.info("定时任务已启动，按 Ctrl+C 停止...")
            while True:
                schedule.run_pending()
                time.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("程序已停止")
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")

if __name__ == "__main__":
    main() 