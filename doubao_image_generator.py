import logging
import time
import json
import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from urllib.parse import urlparse, parse_qs

# 配置日志记录
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

class DoubaoImageGenerator:
    def __init__(self, headless=False):
        """初始化豆包图片生成器
        
        Args:
            headless (bool): 是否使用无头模式（建议设为False以便调试）
        """
        self.driver = None
        self.headless = headless
        self.session = requests.Session()
        self.device_id = None
        self.web_id = None
        self.msToken = None
        self.a_bogus = None
        self.setup_driver()
    
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # 添加必要的选项
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 添加更多稳定性选项
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"ChromeDriver设置失败: {e}")
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                raise Exception(f"无法初始化ChromeDriver: {e2}")
        
        self.driver.implicitly_wait(10)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def login_and_extract_params(self):
        """登录豆包并提取必要的参数"""
        try:
            print("正在访问豆包网站...")
            self.driver.get('https://www.doubao.com/chat/')
            
            # 等待页面加载
            time.sleep(5)
            
            # 检查是否需要登录
            try:
                login_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '登录') or contains(text(), '登陆')]|//a[contains(text(), '登录') or contains(text(), '登陆')]"))
                )
                print("检测到需要登录，请手动完成登录过程...")
                print("登录完成后，程序将自动继续...")
                
                # 等待用户手动登录
                WebDriverWait(self.driver, 300).until(
                    lambda driver: "chat" in driver.current_url and len(driver.get_cookies()) > 0
                )
                print("登录成功！")
                
            except:
                print("可能已经登录或无需登录")
            
            # 等待页面完全加载
            time.sleep(3)
            
            # 提取参数
            self.extract_dynamic_params()
            
            return True
            
        except Exception as e:
            print(f"登录过程中出现错误: {e}")
            return False
    
    def extract_dynamic_params(self):
        """从当前页面提取动态参数"""
        try:
            # 获取当前URL中的参数
            current_url = self.driver.current_url
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)
            
            # 从URL中提取参数
            if 'device_id' in query_params:
                self.device_id = query_params['device_id'][0]
            if 'web_id' in query_params:
                self.web_id = query_params['web_id'][0]
            
            # 从cookies中提取msToken
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                if cookie['name'] == 'msToken':
                    self.msToken = cookie['value']
                    break
            
            # 如果URL中没有参数，尝试从页面脚本中提取
            if not self.device_id or not self.web_id:
                page_source = self.driver.page_source
                
                # 查找device_id
                device_id_match = re.search(r'device_id["\']?\s*[:=]\s*["\']?(\d+)', page_source)
                if device_id_match:
                    self.device_id = device_id_match.group(1)
                
                # 查找web_id
                web_id_match = re.search(r'web_id["\']?\s*[:=]\s*["\']?(\d+)', page_source)
                if web_id_match:
                    self.web_id = web_id_match.group(1)
            
            # 如果仍然没有找到，使用默认值
            if not self.device_id:
                self.device_id = "7511556792158717459"
            if not self.web_id:
                self.web_id = "7511556796785526322"
            
            print(f"提取的参数:")
            print(f"device_id: {self.device_id}")
            print(f"web_id: {self.web_id}")
            print(f"msToken: {self.msToken[:20] + '...' if self.msToken else 'None'}")
            
        except Exception as e:
            print(f"提取参数时出现错误: {e}")
    
    def generate_a_bogus(self, url_params):
        """生成a_bogus参数（这是一个简化版本，实际可能需要更复杂的算法）"""
        try:
            # 执行JavaScript来生成a_bogus
            # 这里需要根据豆包的实际算法来实现
            # 暂时返回一个示例值
            script = """
            // 这里应该是豆包的a_bogus生成算法
            // 由于算法复杂，这里返回一个占位符
            return 'generated_a_bogus_placeholder';
            """
            
            result = self.driver.execute_script(script)
            return result
            
        except Exception as e:
            print(f"生成a_bogus时出现错误: {e}")
            return "Dj0nDtUEQxR5cplSYCmSHUo5q2A%252FNBuyusi2W7r57KugG7lPeA15xKpKbxTrCumiVmsiiF279jCjTdnOKb-yU81pqmkkSxvbf0IAV66L2qi4G0iQLrf0CukYeJtclQJwmQo6JA6V1UDOIVA1w3a0UdlyyKaxsO0pzNNfdcUGYIz6gMs9FNqQuPGdNXMC0U2b"
    
    def wait_for_image_generation(self, timeout=120):
        """等待图片生成完成"""
        print(f"⏳ 开始等待图片生成完成，超时时间: {timeout}秒")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                elapsed = int(time.time() - start_time)
                
                # 查找生成状态指示器
                loading_indicators = [
                    "//div[contains(@class, 'loading') or contains(@class, 'generating')]",
                    "//div[contains(text(), '生成中') or contains(text(), '正在生成')]",
                    "//div[contains(@class, 'spinner') or contains(@class, 'progress')]"
                ]
                
                # 检查是否还在生成中
                is_generating = False
                for i, indicator in enumerate(loading_indicators):
                    try:
                        elements = self.driver.find_elements(By.XPATH, indicator)
                        visible_elements = [elem for elem in elements if elem.is_displayed()]
                        if visible_elements:
                            is_generating = True
                            if elapsed % 10 == 0:  # 每10秒打印一次
                                print(f"🔄 [{elapsed}s] 仍在生成中，找到 {len(visible_elements)} 个加载指示器 (选择器{i+1})")
                            break
                    except Exception as e:
                        if elapsed % 20 == 0:  # 每20秒打印一次错误
                            print(f"⚠️ 检查加载指示器时出错: {str(e)[:50]}")
                        continue
                
                # 如果没有生成指示器，检查是否有新的图片出现
                if not is_generating:
                    if elapsed % 5 == 0:  # 每5秒打印一次
                        print(f"🔍 [{elapsed}s] 没有发现生成指示器，开始查找图片...")
                    
                    # 查找图片元素 - 更新选择器以匹配实际的生成图片
                    image_elements = self.driver.find_elements(By.XPATH, "//img[contains(@src, 'http')]")
                    print(f"📊 [{elapsed}s] 页面上共找到 {len(image_elements)} 个img元素")
                    
                    # 检查图片是否真正加载完成
                    valid_images = []
                    for i, img in enumerate(image_elements):
                        try:
                            src = img.get_attribute('src')
                            if not src:
                                continue
                                
                            # 打印每个图片的详细信息
                            if elapsed % 10 == 0:  # 每10秒详细打印
                                print(f"  img[{i}]: {src[:60]}...")
                            
                            # 更新图片识别逻辑 - 检查是否为生成的图片
                            is_generated_image = (
                                # 检查域名和路径
                                ('byteimg.com' in src and 'image_skill' in src) or
                                # 保留原有的检查逻辑作为备用
                                ('doubao' in src or 'bytedance' in src or 'mcs' in src)
                            )
                            is_not_svg = not src.endswith('.svg')
                            is_not_placeholder = 'placeholder' not in src.lower()
                            is_not_loading = 'loading' not in src.lower()
                            is_not_logo = not any(x in src.lower() for x in ['logo', 'icon', 'avatar'])
                            
                            # 检查CSS类和属性
                            css_class = img.get_attribute('class') or ''
                            imagex_type = img.get_attribute('imagex-type')
                            is_react_image = 'image-' in css_class or imagex_type == 'react'
                            
                            if elapsed % 10 == 0:  # 每10秒详细打印
                                print(f"    生成图片: {is_generated_image}, 非SVG: {is_not_svg}, 非占位符: {is_not_placeholder}")
                                print(f"    非加载中: {is_not_loading}, 非Logo: {is_not_logo}, React图片: {is_react_image}")
                            
                            if (src and is_generated_image and is_not_svg and is_not_placeholder and 
                                is_not_loading and is_not_logo and is_react_image):
                                # 检查图片是否真正加载完成
                                is_complete = self.driver.execute_script(
                                    "return arguments[0].complete && arguments[0].naturalWidth > 0;", img
                                )
                                
                                if elapsed % 10 == 0:  # 每10秒详细打印
                                    print(f"    图片加载完成: {is_complete}")
                                
                                if is_complete:
                                    valid_images.append(src)
                                    if elapsed % 5 == 0:  # 每5秒打印找到的有效图片
                                        print(f"  ✅ 找到有效图片[{len(valid_images)}]: {src[:60]}...")
                        except Exception as e:
                            if elapsed % 20 == 0:  # 每20秒打印一次错误
                                print(f"    ⚠️ 处理图片元素时出错: {str(e)[:50]}")
                            continue
                    
                    if valid_images:
                        print(f"🎉 图片生成完成！总共找到 {len(valid_images)} 张有效图片")
                        for i, url in enumerate(valid_images, 1):
                            print(f"  有效图片[{i}]: {url[:80]}...")
                    
                    # 直接下载找到的有效图片
                    downloaded_images = []
                    for i, url in enumerate(valid_images, 1):
                        try:
                            print(f"正在下载图片 {i}/{len(valid_images)}: {url[:60]}...")
                            actual_filename = f"generated_image_{i}"
                            success = self.download_image(url, actual_filename)
                            if success:
                                downloaded_images.append(actual_filename)  # 添加实际文件名
                                print(f"✅ 图片 {i} 下载成功: {actual_filename}")
                            else:
                                print(f"❌ 图片 {i} 下载失败")
                        except Exception as e:
                            print(f"❌ 下载图片 {i} 时出错: {str(e)}")
                    
                    return downloaded_images
                
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ 等待图片生成时出错: {str(e)}")
                time.sleep(2)
        
        print(f"⏰ 等待超时 ({timeout}秒)，尝试获取当前页面的图片")
        return self.get_current_images()
    
    def get_current_images(self):
        """获取当前页面的所有生成图片"""
        # 首先尝试网络监控方法
        print("尝试通过网络监控获取图片...")
        network_images = self.get_current_images_with_network_monitoring()
        
        if network_images:
            return network_images
        
        # 如果网络监控失败，回退到原来的方法
        print("网络监控失败，使用传统方法...")
        return self.get_current_images_traditional()

    def find_images_with_javascript(self):
        """使用JavaScript查找图片"""
        script = """
        // 查找所有包含特定域名的图片
        const images = Array.from(document.querySelectorAll('img'))
            .filter(img => {
                const src = img.src || '';
                return src.includes('byteimg.com') && 
                       src.includes('image_skill') &&
                       img.offsetWidth > 100 && 
                       img.offsetHeight > 100;
            })
            .map(img => ({
                src: img.src,
                alt: img.alt,
                width: img.offsetWidth,
                height: img.offsetHeight,
                visible: img.offsetParent !== null
            }));
        return images;
        """
        
        try:
            image_data = self.driver.execute_script(script)
            print(f"JavaScript找到 {len(image_data)} 张图片")
            
            # 根据JavaScript返回的数据查找实际元素
            all_images = []
            for data in image_data:
                try:
                    img_element = self.driver.find_element(By.XPATH, f"//img[@src='{data['src']}']")
                    all_images.append(img_element)
                except:
                    continue
                    
            return all_images
        except Exception as e:
            print(f"JavaScript查找失败: {e}")
            return []

    def get_current_images_traditional(self):
        """传统的图片获取方法（通过多种策略获取所有生成的原图）"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            # 等待页面完全加载
            time.sleep(3)
            
            # 首先尝试JavaScript方法
            js_images = self.find_images_with_javascript()
            if js_images:
                print(f"JavaScript方法找到 {len(js_images)} 张图片")
                all_images = js_images
            else:
                print("JavaScript方法失败，使用传统选择器")
                # 针对豆包新版界面的精确选择器（更新后的选择器）
                image_selectors = [
                    # 主要选择器：图片网格项中的图片
                    "//div[contains(@class, 'image-box-grid-item')]//img[contains(@class, 'image-') and contains(@src, 'http')]",
                    # 备用选择器：通过data-testid定位
                    "//div[@data-testid='mdbox_image']//img[contains(@src, 'http')]",
                    # 图片包装器中的图片
                    "//div[contains(@class, 'image-wrapper')]//img[contains(@src, 'http')]",
                    # 更新的豆包域名图片选择器 - 关键：byteimg.com + image_skill
                    "//img[contains(@src, 'byteimg.com') and contains(@src, 'image_skill')]",
                    "//img[contains(@src, 'flow-imagex-sign.byteimg.com')]",
                    "//img[contains(@src, 'ocean-cloud-tos')]",
                    # 通过特殊属性定位 - imagex-type='react'是关键特征
                    "//img[@imagex-type='react']",
                    "//img[contains(@class, 'image-')]",
                    # picture元素中的img
                    "//picture//img[contains(@src, 'http')]"
                ]
                
                all_images = []
                
                # 收集所有可能的图片元素
                for selector in image_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        all_images.extend(elements)
                        print(f"选择器 '{selector}' 找到 {len(elements)} 张图片")
                    except Exception as e:
                        print(f"选择器 '{selector}' 执行失败: {e}")
                        continue
            
            # 添加调试信息
            print("\n=== 调试信息：所有找到的图片 ===")
            for i, img in enumerate(all_images):
                try:
                    src = img.get_attribute('src')
                    imagex_type = img.get_attribute('imagex-type')
                    img_class = img.get_attribute('class')
                    print(f"图片 {i+1}:")
                    print(f"  URL: {src}")
                    print(f"  imagex-type: {imagex_type}")
                    print(f"  class: {img_class}")
                    print(f"  is_likely_generated: {self.is_likely_generated_image(src)}")
                    print("---")
                except Exception as e:
                    print(f"获取图片 {i+1} 信息失败: {e}")
            
            # 去重并筛选有效图片
            unique_images = []
            seen_srcs = set()
            
            for img in all_images:
                try:
                    src = img.get_attribute('src')
                    if not src or src in seen_srcs:
                        continue
                    
                    # 检查特殊属性 - 这些是豆包生成图片的关键标识
                    has_imagex_type = img.get_attribute('imagex-type') == 'react'
                    has_image_class = 'image-' in (img.get_attribute('class') or '')
                    
                    # 更严格的图片URL验证 - 排除logo等非生成图片
                    is_not_logo = 'logo' not in src.lower()
                    is_not_icon = 'icon' not in src.lower()
                    is_not_avatar = 'avatar' not in src.lower()
                    
                    if (self.is_likely_generated_image(src) and 
                        (has_imagex_type or has_image_class) and
                        is_not_logo and is_not_icon and is_not_avatar):
                        unique_images.append(img)
                        seen_srcs.add(src)
                        print(f"发现有效图片: {src[:60]}...")
                        if has_imagex_type:
                            print(f"  ✓ 包含imagex-type='react'属性")
                        if has_image_class:
                            print(f"  ✓ 包含image-类名")
                        print(f"  ✓ 已排除logo/icon/avatar")
                except:
                    continue
                
            print(f"\n总共找到 {len(unique_images)} 张有效的生成图片")
            print("强制测试原图获取功能...")
            
            if unique_images:
                test_img = unique_images[0]
                test_src = test_img.get_attribute('src')
                print(f"测试图片URL: {test_src}")
                original_url = self.get_original_image_url(test_img, test_src)
                print(f"原图获取结果: {original_url}")
            else:
                print("未找到任何图片，尝试等待更长时间...")
                time.sleep(5)
                # 重新尝试最基本的选择器
                basic_images = self.driver.find_elements(By.XPATH, "//img[contains(@src, 'http')]")
                print(f"基础选择器找到 {len(basic_images)} 张图片")
                for img in basic_images:
                    try:
                        src = img.get_attribute('src')
                        imagex_type = img.get_attribute('imagex-type')
                        img_class = img.get_attribute('class')
                        print(f"  - {src[:80]}...")
                        print(f"    imagex-type: {imagex_type}")
                        print(f"    class: {img_class}")
                    except:
                        pass
                return []
            
            print("\n开始处理图片，获取原图URL...")  # 添加这行调试信息
            
            valid_images = []
                
            # 处理每张图片
            for i, img in enumerate(unique_images, 1):
                try:
                    src = img.get_attribute('src')
                    print(f"\n=== 处理第 {i} 张图片 ===")
                    print(f"缩略图URL: {src}")
                    
                    # 滚动到图片位置
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img)
                    time.sleep(1)
                    
                    # 尝试多种方法获取原图
                    original_url = self.get_original_image_url(img, src)
                    
                    if original_url and original_url != src:
                        print(f"✅ 成功获取原图URL: {original_url}")
                        print(f"📏 URL长度对比 - 缩略图: {len(src)}, 原图: {len(original_url)}")
                        valid_images.append(original_url)
                    else:
                        print(f"❌ 原图获取失败，使用缩略图: {src}")
                        # 尝试手动转换URL
                        converted_url = self.convert_to_original_url_enhanced(src)
                        if converted_url != src:
                            print(f"🔄 尝试URL转换: {converted_url}")
                            valid_images.append(converted_url)
                        else:
                            valid_images.append(src)
                    
                except Exception as e:
                    print(f"处理第 {i} 张图片时出现错误: {e}")
                    continue
            
            print(f"\n最终获取到 {len(valid_images)} 张原图URL")
            return valid_images
            
        except Exception as e:
            print(f"获取图片时出现错误: {e}")
            return []

    def get_original_image_url(self, img_element, thumbnail_url):
        """获取图片的原图URL"""
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(self.driver)
        original_url_found = None
        
        try:
            # 方法1: 从picture元素的source标签获取原图
            print("[get_original_image_url] 尝试方法1: 从picture元素获取原图")
            picture_url = self.get_original_url_from_picture_element(img_element)
            if picture_url and picture_url != thumbnail_url:
                print(f"[get_original_image_url] ✅ 从picture元素获取到原图URL: {picture_url}")
                return picture_url
            
            # 方法2: 尝试从图片元素属性获取并转换
            print("[get_original_image_url] 尝试方法2: 从元素属性获取并转换")
            try:
                real_url = self.get_image_real_url(img_element)
                if real_url and real_url != thumbnail_url:
                    print(f"[get_original_image_url] ✅ 通过元素属性获取到原图URL: {real_url}")
                    original_url_found = real_url
            except Exception as e:
                print(f"[get_original_image_url] 从元素属性获取URL时出错: {e}")
            
            if original_url_found:
                return original_url_found
            
            # 方法3: 查找下载按钮
            print("[get_original_image_url] 尝试方法3: 查找下载按钮")
            
            # 先滚动到图片位置
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img_element)
            time.sleep(1)
            
            # 鼠标悬停到图片上
            actions.move_to_element(img_element).perform()
            time.sleep(3)
            
            # 下载按钮选择器
            download_selectors = [
                "//div[contains(@class, 'image-') or contains(@class, 'img-')]//button[contains(@class, 'download') or contains(@title, 'download') or contains(@aria-label, 'download')]",
                "//div[contains(@class, 'image-') or contains(@class, 'img-')]//a[contains(@class, 'download') or contains(@title, 'download')]",
                ".//ancestor::div[contains(@class, 'image') or contains(@class, 'img') or contains(@class, 'picture')]//button",
                ".//ancestor::div[1]//button[contains(@class, 'download') or contains(@title, '下载') or contains(@aria-label, 'download') or contains(text(), '下载') or contains(@class, 'btn')]",
                ".//ancestor::div[2]//button[contains(@class, 'download') or contains(@title, '下载') or contains(@aria-label, 'download') or contains(text(), '下载') or contains(@class, 'btn')]",
                ".//ancestor::div[3]//button[contains(@class, 'download') or contains(@title, '下载') or contains(@aria-label, 'download') or contains(text(), '下载') or contains(@class, 'btn')]",
                "//button[contains(@style, 'visible') or contains(@style, 'block')][contains(@class, 'download') or contains(@title, 'download') or contains(@aria-label, 'download')]",
                "//div[contains(@style, 'visible') or contains(@style, 'block')]//button",
                "//button[contains(@class, 'download') or contains(@title, '下载') or contains(@aria-label, 'download') or contains(text(), '下载')]",
                "//a[contains(@class, 'download') or contains(@href, 'download') or contains(@title, '下载')]",
                ".//ancestor::div[1]//button[not(contains(@style, 'display: none')) and not(contains(@style, 'visibility: hidden'))]",
                ".//ancestor::div[2]//button[not(contains(@style, 'display: none')) and not(contains(@style, 'visibility: hidden'))]",
            ]
            
            for i, selector in enumerate(download_selectors):
                try:
                    if selector.startswith('.//'):  # 相对于图片元素查找
                        buttons = img_element.find_elements(By.XPATH, selector)
                    else:  # 全局查找
                        buttons = self.driver.find_elements(By.XPATH, selector)
                    
                    for j, button in enumerate(buttons):
                        try:
                            if button.is_displayed() and button.is_enabled():
                                # 点击按钮
                                try:
                                    button.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", button)
                                
                                time.sleep(4)
                                
                                # 检查是否有新窗口或下载链接
                                download_url = self.get_download_url_from_browser()
                                if download_url and download_url != thumbnail_url:
                                    print(f"[get_original_image_url] ✅ 通过下载按钮获取到原图URL: {download_url}")
                                    original_url_found = download_url
                                    break
                        except Exception as e:
                            continue
                    
                    if original_url_found:
                        break
                except Exception as e:
                    continue
            
            if original_url_found:
                return original_url_found
            
            # 方法4: 右键菜单获取原图
            print("[get_original_image_url] 尝试方法4: 右键菜单获取原图")
            try:
                actions.context_click(img_element).perform()
                time.sleep(1)
                
                # 查找"在新标签页中打开图片"选项
                context_options = [
                    "//div[contains(text(), '在新标签页中打开图片') or contains(text(), 'Open image in new tab')]",
                    "//span[contains(text(), '在新标签页中打开图片') or contains(text(), 'Open image in new tab')]"
                ]
                
                for option_xpath in context_options:
                    try:
                        option = self.driver.find_element(By.XPATH, option_xpath)
                        if option.is_displayed():
                            option.click()
                            time.sleep(2)
                            
                            # 切换到新标签页获取URL
                            if len(self.driver.window_handles) > 1:
                                original_window = self.driver.current_window_handle
                                new_window = [h for h in self.driver.window_handles if h != original_window][0]
                                self.driver.switch_to.window(new_window)
                                
                                current_url = self.driver.current_url
                                if self.is_valid_image_url(current_url) and current_url != thumbnail_url:
                                    print(f"[get_original_image_url] ✅ 通过右键菜单获取到原图URL: {current_url}")
                                    self.driver.close()
                                    self.driver.switch_to.window(original_window)
                                    original_url_found = current_url
                                    break
                                else:
                                    self.driver.close()
                                    self.driver.switch_to.window(original_window)
                            break
                    except:
                        continue
                
                # 按ESC关闭右键菜单
                actions.send_keys(Keys.ESCAPE).perform()
                
                if original_url_found:
                    return original_url_found
            except Exception as e:
                print(f"[get_original_image_url] 右键菜单方法出错: {e}")
            
        except Exception as e:
            print(f"[get_original_image_url] 获取原图URL时出现错误: {e}")
        
        return thumbnail_url

    def get_original_url_from_picture_element(self, img_element):
        """从picture元素中获取原图URL"""
        try:
            # 查找父级的picture元素
            picture_element = None
            current = img_element
            
            # 向上查找picture元素（最多查找5层）
            for _ in range(5):
                try:
                    current = current.find_element(By.XPATH, "./parent::*")
                    if current.tag_name.lower() == 'picture':
                        picture_element = current
                        break
                except:
                    break
            
            if not picture_element:
                # 如果img不在picture内，尝试查找同级的picture
                try:
                    picture_element = img_element.find_element(By.XPATH, "./ancestor::*[contains(@class, 'image') or contains(@class, 'img')]//picture")
                except:
                    return None
            
            if picture_element:
                print(f"[get_original_url_from_picture_element] 找到picture元素")
                
                # 优先获取AVIF格式的source元素
                source_selectors = [
                    ".//source[@type='image/avif']",
                    ".//source[contains(@srcset, 'avif')]",
                    ".//source[@type='image/webp']", 
                    ".//source[contains(@srcset, 'webp')]"
                ]
                
                for selector in source_selectors:
                    try:
                        sources = picture_element.find_elements(By.XPATH, selector)
                        for source in sources:
                            # 获取srcset或src属性
                            srcset = source.get_attribute('srcset') or source.get_attribute('src')
                            if srcset:
                                # 从srcset中提取第一个URL（通常是1x的版本）
                                url = srcset.split(' ')[0].split(',')[0].strip()
                                if url and 'byteimg.com' in url:
                                    print(f"[get_original_url_from_picture_element] 从{source.get_attribute('type')}获取到URL: {url}")
                                    
                                    # 转换为原图URL（去除水印标识）
                                    original_url = self.convert_to_original_url_enhanced(url)
                                    if original_url != url:
                                        print(f"[get_original_url_from_picture_element] 转换后的原图URL: {original_url}")
                                        return original_url
                                    else:
                                        return url
                    except Exception as e:
                        print(f"[get_original_url_from_picture_element] 处理source元素时出错: {e}")
                        continue
            
            return None
            
        except Exception as e:
            print(f"[get_original_url_from_picture_element] 获取picture元素URL时出错: {e}")
            return None

    def convert_to_original_url_enhanced(self, thumbnail_url):
        """增强的URL转换方法"""
        try:
            import re
            original_url = thumbnail_url
            
            print(f"原始缩略图URL: {thumbnail_url}")
            
            # 豆包特定的转换规则 - 更全面的缩略图转原图处理
            doubao_conversions = [
                # 移除所有类型的缩略图和水印标识
                (r'~tplv-[^?]+', ''),  # 移除整个tplv参数
                
                # 专门处理各种水印和缩略图标识
                (r'-web-thumb-watermark-v2', ''),  # v2版本水印
                (r'-web-thumb-watermark', ''),     # 标准水印
                (r'-web-thumb-wm', ''),            # 简化水印标识
                (r'-watermark-v2', ''),            # v2水印
                (r'-watermark', ''),               # 水印
                (r'-thumb', ''),                   # 缩略图
                (r'-wm', ''),                      # 简化水印
                
                # 移除格式转换后缀
                (r'-avif\.avif$', ''),            # 移除avif格式
                (r'-webp\.webp$', ''),            # 移除webp格式
                (r'\.avif$', '.jpeg'),            # avif转jpeg
                (r'\.webp$', '.jpeg'),            # webp转jpeg
                
                # 移除URL参数中的处理参数
                (r'\?[^?]*tplv[^&]*', ''),         # 移除URL参数中的tplv
                (r'&[^&]*tplv[^&]*', ''),
                
                # 移除尺寸和质量限制参数
                (r'[?&]w=\d+', ''),
                (r'[?&]h=\d+', ''),
                (r'[?&]s=\d+', ''),
                (r'[?&]size=\d+', ''),
                (r'[?&]quality=\d+', ''),
                (r'[?&]format=\w+', ''),
                (r'[?&]f=\w+', ''),
                
                # 移除签名参数（这些参数可能导致原图访问失败）
                (r'[?&]rk3s=[^&]*', ''),
                (r'[?&]x-expires=[^&]*', ''),
                (r'[?&]x-signature=[^&]*', ''),
            ]
            
            # 应用转换规则
            for pattern, replacement in doubao_conversions:
                old_url = original_url
                original_url = re.sub(pattern, replacement, original_url)
                if old_url != original_url:
                    print(f"✓ 应用规则 '{pattern}': 移除了缩略图标识")
            
            # 清理多余的参数分隔符
            original_url = re.sub(r'[?&]+$', '', original_url)
            original_url = re.sub(r'[?]&', '?', original_url)
            original_url = re.sub(r'&&+', '&', original_url)
            
            print(f"转换后原图URL: {original_url}")
            
            # 如果转换后的URL与原URL相同，尝试更激进的方法
            if original_url == thumbnail_url:
                print("常规转换无效，尝试提取基础URL...")
                # 提取基础URL（去掉所有处理参数）
                base_match = re.match(r'(https://[^~?]+)', thumbnail_url)
                if base_match:
                    base_url = base_match.group(1)
                    # 确保是jpeg格式
                    if not base_url.endswith(('.jpg', '.jpeg', '.png')):
                        base_url += '.jpeg'
                    print(f"使用基础URL: {base_url}")
                    return base_url
                else:
                    print("无法提取基础URL，尝试手动构建...")
                    # 手动构建原图URL
                    # 从缩略图URL中提取图片ID
                    id_match = re.search(r'image_skill/([^~]+)', thumbnail_url)
                    if id_match:
                        image_id = id_match.group(1)
                        # 构建原图URL（不带任何处理参数）
                        domain_match = re.match(r'(https://[^/]+)', thumbnail_url)
                        if domain_match:
                            domain = domain_match.group(1)
                            constructed_url = f"{domain}/ocean-cloud-tos/image_skill/{image_id}.jpeg"
                            print(f"构建的原图URL: {constructed_url}")
                            return constructed_url
            
            return original_url
            
        except Exception as e:
            print(f"URL转换失败: {e}")
            return thumbnail_url

    def is_likely_generated_image(self, url):
        """判断URL是否为生成的图片"""
        if not url or not isinstance(url, str):
            return False
        
        # 排除明显的非图片URL
        exclude_patterns = [
            'data:image/svg+xml',  # SVG占位符
            'avatar',              # 头像
            'icon',                # 图标
            'logo',                # 标志
            'placeholder',         # 占位符
            'loading',             # 加载图片
            'default',             # 默认图片
            'thumb_',              # 某些缩略图前缀
            'profile',             # 个人资料图片
        ]
        
        url_lower = url.lower()
        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False
        
        # 豆包生成图片的特征（更新后的识别条件）
        doubao_patterns = [
            # 新的域名识别 - 关键特征：byteimg.com + image_skill
            ('byteimg.com', 'image_skill'),  # 需要同时包含这两个
            ('doubao', 'generated'),
            ('bytedance', 'ai'),
            # 原有的模式
            'flow-imagex-sign.byteimg.com',
            'ocean-cloud-tos',
            'tplv-',
            'web-thumb-watermark',
            'web-watermark'
        ]
        
        # 检查是否包含豆包图片特征
        for pattern in doubao_patterns:
            if isinstance(pattern, tuple):
                # 需要同时包含两个条件
                if all(p in url for p in pattern):
                    return True
            else:
                # 单个条件
                if pattern in url:
                    return True
        
        # 通用图片URL检查
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.avif']
        return any(ext in url_lower for ext in image_extensions)

    def enable_network_logging(self):
        """启用网络请求日志记录"""
        try:
            # 如果浏览器已经启动，需要重新启动
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
            
            # 重新创建带有日志功能的浏览器
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--enable-logging')
            options.add_argument('--log-level=0')
            
            # 使用新的Selenium 4.x语法启用性能日志
            options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            
            self.driver = webdriver.Chrome(options=options)
            print("✅ 网络日志记录已启用")
            
        except Exception as e:
            print(f"❌ 启用网络日志失败: {e}")

    def get_network_requests(self, filter_pattern=None):
        """获取网络请求记录"""
        try:
            logs = self.driver.get_log('performance')
            requests = []
            
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    response = message['message']['params']['response']
                    url = response['url']
                    
                    # 过滤图片请求
                    if filter_pattern:
                        if filter_pattern in url.lower():
                            requests.append({
                                'url': url,
                                'mimeType': response.get('mimeType', ''),
                                'status': response.get('status', 0),
                                'headers': response.get('headers', {})
                            })
                    elif any(img_type in response.get('mimeType', '').lower() for img_type in ['image/', 'png', 'jpg', 'jpeg', 'webp']):
                        requests.append({
                            'url': url,
                            'mimeType': response.get('mimeType', ''),
                            'status': response.get('status', 0),
                            'headers': response.get('headers', {})
                        })
            
            return requests
            
        except Exception as e:
            print(f"获取网络请求失败: {e}")
            return []

    def get_current_images_with_network_monitoring(self):
        """通过网络监控获取图片（增强版：获取原图）"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            # 等待页面完全加载
            time.sleep(3)
            
            # 优先使用JavaScript方法查找图片
            print("=== 使用JavaScript方法查找图片 ===")
            unique_images = self.find_images_with_javascript()
            
            if not unique_images:
                print("JavaScript方法未找到图片，回退到传统选择器方法")
                # 回退到传统选择器方法
                image_selectors = [
                    "//div[contains(@class, 'image-box-grid-item')]//img[contains(@class, 'image-') and contains(@src, 'http')]",
                    "//div[@data-testid='mdbox_image']//img[contains(@src, 'http')]",
                    "//div[contains(@class, 'image-wrapper')]//img[contains(@src, 'http')]"
                ]
                
                all_images = []
                for selector in image_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        all_images.extend(elements)
                        print(f"选择器找到 {len(elements)} 张图片")
                    except Exception as e:
                        continue
                
                # 去重
                unique_images = []
                seen_srcs = set()
                for img in all_images:
                    try:
                        src = img.get_attribute('src')
                        if src and src not in seen_srcs and self.is_likely_generated_image(src):
                            unique_images.append(img)
                            seen_srcs.add(src)
                    except:
                        continue
            
            print(f"找到 {len(unique_images)} 张有效图片")
            
            valid_image_urls = []
            actions = ActionChains(self.driver)
            
            for i, img in enumerate(unique_images):
                try:
                    print(f"\n=== 处理第 {i+1} 张图片 ===")
                    
                    # 获取缩略图URL
                    thumbnail_url = img.get_attribute('src')
                    print(f"缩略图URL: {thumbnail_url[:80]}...")
                    
                    # 滚动到图片位置
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img)
                    time.sleep(1)
                    
                    # 尝试获取原图URL
                    original_url = self.get_original_image_url(img, thumbnail_url)
                    
                    if original_url and original_url != thumbnail_url:
                        print(f"✅ 获取到原图URL: {original_url[:80]}...")
                        valid_image_urls.append(original_url)
                    else:
                        print(f"⚠️ 未能获取原图，使用缩略图: {thumbnail_url[:80]}...")
                        valid_image_urls.append(thumbnail_url)
                    
                except Exception as e:
                    print(f"处理第 {i+1} 张图片时出错: {e}")
                    # 如果出错，至少保存缩略图
                    try:
                        thumbnail_url = img.get_attribute('src')
                        valid_image_urls.append(thumbnail_url)
                    except:
                        continue
            
            print(f"\n最终获取到 {len(valid_image_urls)} 张图片URL")
            return valid_image_urls
            
        except Exception as e:
            print(f"网络监控方法执行失败: {e}")
            print(f"错误类型: {type(e).__name__}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return []

    def get_download_url_from_browser(self):
        """从浏览器获取下载URL"""
        try:
            # 检查是否有新的标签页或窗口打开
            current_handles = self.driver.window_handles
            if len(current_handles) > 1:
                # 切换到新窗口
                self.driver.switch_to.window(current_handles[-1])
                current_url = self.driver.current_url
                
                # 如果新窗口的URL是图片URL，返回它
                if self.is_valid_image_url(current_url):
                    # 切换回原窗口
                    self.driver.switch_to.window(current_handles[0])
                    return current_url
                
                # 关闭新窗口并切换回原窗口
                self.driver.close()
                self.driver.switch_to.window(current_handles[0])
            
            # 检查浏览器的下载历史或网络请求
            # 这里可以通过浏览器的开发者工具API获取最新的网络请求
            logs = self.driver.get_log('performance')
            for log in logs[-10:]:  # 检查最近的10个网络请求
                message = json.loads(log['message'])
                if (message.get('message', {}).get('method') == 'Network.responseReceived'):
                    response = message['message']['params']['response']
                    url = response.get('url', '')
                    if self.is_valid_image_url(url) and 'download' in url.lower():
                        return url
            
            return None
            
        except Exception as e:
            print(f"获取下载URL时出现错误: {e}")
            return None
    
    def get_image_real_url(self, img_element):
        """获取图片元素的真实URL"""
        try:
            # 尝试多种方法获取真实URL
            methods = [
                lambda: img_element.get_attribute('data-original'),
                lambda: img_element.get_attribute('data-src'),
                lambda: img_element.get_attribute('data-full-url'),
                lambda: img_element.get_attribute('src'),
            ]
            
            for method in methods:
                try:
                    url = method()
                    if url and self.is_valid_image_url(url):
                        # 尝试转换为原图URL
                        original_url = self.convert_to_original_url_enhanced(url)
                        return original_url
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"获取真实URL时出现错误: {e}")
            return None
    
    def download_image_via_browser(self, image_url, filename):
        """通过浏览器下载图片（支持下载按钮方式）"""
        try:
            print(f"正在下载图片: {image_url[:50]}...")
            
            # 如果URL看起来像是通过下载按钮获取的，直接下载
            if 'download' in image_url.lower() or 'original' in image_url.lower():
                return self.download_image(image_url, filename)
            
            # 否则，尝试在新标签页中打开图片
            original_window = self.driver.current_window_handle
            
            # 在新标签页中打开图片
            self.driver.execute_script(f"window.open('{image_url}', '_blank');")
            time.sleep(2)
            
            # 切换到新标签页
            new_window = [handle for handle in self.driver.window_handles if handle != original_window][0]
            self.driver.switch_to.window(new_window)
            
            # 获取新标签页的URL（可能是重定向后的真实图片URL）
            real_url = self.driver.current_url
            
            # 关闭新标签页并切换回原窗口
            self.driver.close()
            self.driver.switch_to.window(original_window)
            
            # 使用真实URL下载图片
            return self.download_image(real_url, filename)
            
        except Exception as e:
            print(f"通过浏览器下载图片时出现错误: {e}")
            return False
    
    def is_valid_image_url(self, url):
        """检查URL是否为有效的图片URL"""
        if not url or not url.startswith('http'):
            return False
        
        # 排除明显的非图片URL
        invalid_patterns = [
            '.svg', 'placeholder', 'loading', 'icon', 'avatar',
            'logo', 'banner', 'background'
        ]
        
        url_lower = url.lower()
        for pattern in invalid_patterns:
            if pattern in url_lower:
                return False
        
        # 检查是否包含图片相关的域名或路径
        valid_patterns = [
            'doubao', 'bytedance', 'mcs', 'image', 'img', 'photo',
            'picture', 'generated', '.jpg', '.jpeg', '.png', '.webp'
        ]
        
        for pattern in valid_patterns:
            if pattern in url_lower:
                return True
        
        return False
    

    
    def check_for_new_images(self):
        """检查页面上是否出现了新的图片"""
        try:
            # 等待一下让新内容加载
            time.sleep(2)
            
            # 查找最近添加的图片元素
            new_images = []
            recent_images = self.driver.find_elements(By.XPATH, "//img[contains(@src, 'http')]")
            
            for img in recent_images[-5:]:  # 只检查最后5个图片元素
                src = img.get_attribute('src')
                if src and self.is_valid_image_url(src):
                    new_images.append(src)
            
            return new_images
            
        except Exception as e:
            return []
    
    def verify_image_accessibility(self, url):
        """验证图片URL是否可访问且为有效图片"""
        try:
            # 使用HEAD请求检查图片是否存在
            cookies = self.driver.get_cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.doubao.com/'
            }
            
            response = requests.head(url, headers=headers, cookies=cookie_dict, timeout=10)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = response.headers.get('content-length')
                
                # 检查是否为图片类型且大小合理
                if ('image' in content_type and 
                    content_length and 
                    int(content_length) > 10240):  # 大于10KB
                    print(f"验证通过: {url[:50]}... (大小: {int(content_length)/1024:.1f}KB)")
                    return True
            
            return False
            
        except Exception as e:
            print(f"验证图片URL时出现错误: {e}")
            return False
    
    def send_image_request_via_browser(self, prompt):
        """通过浏览器发送图片生成请求"""
        try:
            print(f"🚀 开始生成图片: {prompt}")
            print(f"📍 当前页面URL: {self.driver.current_url}")
            
            # 查找输入框
            input_selectors = [
                "//textarea[@placeholder*='输入' or @placeholder*='消息' or @placeholder*='问题']",
                "//input[@placeholder*='输入' or @placeholder*='消息' or @placeholder*='问题']",
                "//div[@contenteditable='true']",
                "textarea",
                "input[type='text']"
            ]
            
            print(f"🔍 开始查找输入框，共有 {len(input_selectors)} 个选择器")
            input_element = None
            for i, selector in enumerate(input_selectors):
                try:
                    print(f"  尝试选择器 {i+1}: {selector}")
                    if selector.startswith('//'):
                        input_element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        input_element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    print(f"  ✅ 成功找到输入框: {selector}")
                    break
                except Exception as e:
                    print(f"  ❌ 选择器失败: {str(e)[:100]}")
                    continue
            
            if not input_element:
                print("❌ 所有输入框选择器都失败了")
                # 尝试打印页面上所有可能的输入元素
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                all_textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
                all_contenteditable = self.driver.find_elements(By.XPATH, "//div[@contenteditable='true']")
                
                print(f"📊 页面统计: input元素{len(all_inputs)}个, textarea元素{len(all_textareas)}个, contenteditable元素{len(all_contenteditable)}个")
                
                for i, inp in enumerate(all_inputs[:3]):  # 只显示前3个
                    try:
                        placeholder = inp.get_attribute('placeholder') or '无'
                        input_type = inp.get_attribute('type') or '无'
                        print(f"  input[{i}]: type={input_type}, placeholder={placeholder}")
                    except:
                        pass
                        
                for i, ta in enumerate(all_textareas[:3]):  # 只显示前3个
                    try:
                        placeholder = ta.get_attribute('placeholder') or '无'
                        print(f"  textarea[{i}]: placeholder={placeholder}")
                    except:
                        pass
                
                raise Exception("找不到输入框")
            
            # 清空输入框并输入提示词
            print(f"📝 清空输入框并输入提示词: {prompt[:50]}...")
            input_element.clear()
            time.sleep(0.5)  # 等待清空完成
            input_element.send_keys(prompt)
            print(f"✅ 提示词输入完成")
            
            # 发送消息
            print(f"📤 尝试发送消息")
            try:
                input_element.send_keys(Keys.RETURN)
                print(f"✅ 通过回车键发送成功")
            except Exception as e:
                print(f"❌ 回车键发送失败: {e}")
                print(f"🔍 尝试查找发送按钮")
                try:
                    send_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '发送') or contains(text(), '提交')]")
                    send_button.click()
                    print(f"✅ 通过发送按钮发送成功")
                except Exception as e2:
                    print(f"❌ 发送按钮也失败: {e2}")
                    # 尝试查找所有按钮
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    print(f"📊 页面上共有 {len(all_buttons)} 个按钮")
                    for i, btn in enumerate(all_buttons[:5]):  # 只显示前5个
                        try:
                            btn_text = btn.text or btn.get_attribute('aria-label') or '无文本'
                            print(f"  button[{i}]: {btn_text[:30]}")
                        except:
                            pass
                    raise Exception(f"无法发送消息: {e2}")
            
            print(f"⏳ 消息已发送，开始等待图片生成...")
            
            # 等待图片真正生成完成
            result = self.wait_for_image_generation()
            
            # 检查返回结果的类型
            if isinstance(result, list) and result:
                # 如果返回的是文件名列表（新的下载逻辑），直接返回
                if isinstance(result[0], str) and not result[0].startswith('http'):
                    print(f"🎯 图片生成完成，共下载 {len(result)} 张图片")
                    for i, filename in enumerate(result):
                        print(f"  图片[{i+1}]: {filename}")
                    return result  # 直接返回，不再重复下载
                # 如果返回的是URL列表（旧的逻辑），继续下载
                else:
                    print(f"🎯 图片生成完成，共获取到 {len(result)} 个图片URL")
                    # 这里可以添加下载逻辑
                    return result
            else:
                print("❌ 未获取到有效的图片结果")
                return []
            
        except Exception as e:
            print(f"❌ 通过浏览器生成图片时出现错误: {e}")
            import traceback
            print(f"📋 详细错误信息:\n{traceback.format_exc()}")
            return []
    
    def download_image(self, image_url, filename):
        """下载图片"""
        try:
            print(f"正在下载图片: {image_url[:50]}...")
            
            # 使用浏览器的cookies来下载图片
            cookies = self.driver.get_cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.doubao.com/',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }
            
            response = requests.get(image_url, headers=headers, cookies=cookie_dict, timeout=30)
            
            if response.status_code == 200:
                # 检查响应内容是否为有效图片
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                print(f"响应状态: {response.status_code}")
                print(f"内容类型: {content_type}")
                print(f"文件大小: {content_length} 字节")
                
                # 验证是否为有效图片（大小应该大于10KB）
                if content_length > 10240 and 'image' in content_type:
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"✅ 图片已保存为: {filename} (大小: {content_length/1024:.1f}KB)")
                    return True
                else:
                    print(f"❌ 下载的文件不是有效图片 (大小: {content_length} 字节, 类型: {content_type})")
                    return False
            else:
                print(f"❌ 下载图片失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 下载图片时出现错误: {e}")
            return False

    def is_valid_image_content(self, content):
        """通过文件头验证图片格式"""
        if len(content) < 8:
            return False
        
        # 检查常见图片格式的文件头
        image_signatures = {
            b'\xff\xd8\xff': 'JPEG',
            b'\x89PNG\r\n\x1a\n': 'PNG',
            b'GIF87a': 'GIF',
            b'GIF89a': 'GIF',
            b'RIFF': 'WEBP',  # WEBP files start with RIFF
            b'\x00\x00\x00 ftypavif': 'AVIF'
        }
        
        for signature, format_name in image_signatures.items():
            if content.startswith(signature):
                print(f"✅ 检测到有效的{format_name}格式图片")
                return True
            
            # 特殊处理WEBP
            if signature == b'RIFF' and len(content) >= 12:
                if content[8:12] == b'WEBP':
                    print(f"✅ 检测到有效的WEBP格式图片")
                    return True
        
        print(f"❌ 未识别的图片格式，文件头: {content[:16].hex()}")
        return False


    
    def check_for_new_images(self):
        """检查页面上是否出现了新的图片"""
        try:
            # 等待一下让新内容加载
            time.sleep(2)
            
            # 查找最近添加的图片元素
            new_images = []
            recent_images = self.driver.find_elements(By.XPATH, "//img[contains(@src, 'http')]")
            
            for img in recent_images[-5:]:  # 只检查最后5个图片元素
                src = img.get_attribute('src')
                if src and self.is_valid_image_url(src):
                    new_images.append(src)
            
            return new_images
            
        except Exception as e:
            return []
    
    def verify_image_accessibility(self, url):
        """验证图片URL是否可访问且为有效图片"""
        try:
            # 使用HEAD请求检查图片是否存在
            cookies = self.driver.get_cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.doubao.com/'
            }
            
            response = requests.head(url, headers=headers, cookies=cookie_dict, timeout=10)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = response.headers.get('content-length')
                
                # 检查是否为图片类型且大小合理
                if ('image' in content_type and 
                    content_length and 
                    int(content_length) > 10240):  # 大于10KB
                    print(f"验证通过: {url[:50]}... (大小: {int(content_length)/1024:.1f}KB)")
                    return True
            
            return False
            
        except Exception as e:
            print(f"验证图片URL时出现错误: {e}")
            return False
    
    def send_image_request_via_browser(self, prompt):
        """通过浏览器发送图片生成请求"""
        try:
            print(f"🚀 开始生成图片: {prompt}")
            print(f"📍 当前页面URL: {self.driver.current_url}")
            
            # 查找输入框
            input_selectors = [
                "//textarea[@placeholder*='输入' or @placeholder*='消息' or @placeholder*='问题']",
                "//input[@placeholder*='输入' or @placeholder*='消息' or @placeholder*='问题']",
                "//div[@contenteditable='true']",
                "textarea",
                "input[type='text']"
            ]
            
            print(f"🔍 开始查找输入框，共有 {len(input_selectors)} 个选择器")
            input_element = None
            for i, selector in enumerate(input_selectors):
                try:
                    print(f"  尝试选择器 {i+1}: {selector}")
                    if selector.startswith('//'):
                        input_element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        input_element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    print(f"  ✅ 成功找到输入框: {selector}")
                    break
                except Exception as e:
                    print(f"  ❌ 选择器失败: {str(e)[:100]}")
                    continue
            
            if not input_element:
                print("❌ 所有输入框选择器都失败了")
                # 尝试打印页面上所有可能的输入元素
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                all_textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
                all_contenteditable = self.driver.find_elements(By.XPATH, "//div[@contenteditable='true']")
                
                print(f"📊 页面统计: input元素{len(all_inputs)}个, textarea元素{len(all_textareas)}个, contenteditable元素{len(all_contenteditable)}个")
                
                for i, inp in enumerate(all_inputs[:3]):  # 只显示前3个
                    try:
                        placeholder = inp.get_attribute('placeholder') or '无'
                        input_type = inp.get_attribute('type') or '无'
                        print(f"  input[{i}]: type={input_type}, placeholder={placeholder}")
                    except:
                        pass
                        
                for i, ta in enumerate(all_textareas[:3]):  # 只显示前3个
                    try:
                        placeholder = ta.get_attribute('placeholder') or '无'
                        print(f"  textarea[{i}]: placeholder={placeholder}")
                    except:
                        pass
                
                raise Exception("找不到输入框")
            
            # 清空输入框并输入提示词
            print(f"📝 清空输入框并输入提示词: {prompt[:50]}...")
            input_element.clear()
            time.sleep(0.5)  # 等待清空完成
            input_element.send_keys(prompt)
            print(f"✅ 提示词输入完成")
            
            # 发送消息
            print(f"📤 尝试发送消息")
            try:
                input_element.send_keys(Keys.RETURN)
                print(f"✅ 通过回车键发送成功")
            except Exception as e:
                print(f"❌ 回车键发送失败: {e}")
                print(f"🔍 尝试查找发送按钮")
                try:
                    send_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '发送') or contains(text(), '提交')]")
                    send_button.click()
                    print(f"✅ 通过发送按钮发送成功")
                except Exception as e2:
                    print(f"❌ 发送按钮也失败: {e2}")
                    # 尝试查找所有按钮
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    print(f"📊 页面上共有 {len(all_buttons)} 个按钮")
                    for i, btn in enumerate(all_buttons[:5]):  # 只显示前5个
                        try:
                            btn_text = btn.text or btn.get_attribute('aria-label') or '无文本'
                            print(f"  button[{i}]: {btn_text[:30]}")
                        except:
                            pass
                    raise Exception(f"无法发送消息: {e2}")
            
            print(f"⏳ 消息已发送，开始等待图片生成...")
            
            # 等待图片真正生成完成
            result = self.wait_for_image_generation()
            
            # 检查返回结果的类型
            if isinstance(result, list) and result:
                # 如果返回的是文件名列表（新的下载逻辑），直接返回
                if isinstance(result[0], str) and not result[0].startswith('http'):
                    print(f"🎯 图片生成完成，共下载 {len(result)} 张图片")
                    for i, filename in enumerate(result):
                        print(f"  图片[{i+1}]: {filename}")
                    return result  # 直接返回，不再重复下载
                # 如果返回的是URL列表（旧的逻辑），继续下载
                else:
                    print(f"🎯 图片生成完成，共获取到 {len(result)} 个图片URL")
                    # 这里可以添加下载逻辑
                    return result
            else:
                print("❌ 未获取到有效的图片结果")
                return []
            
        except Exception as e:
            print(f"❌ 通过浏览器生成图片时出现错误: {e}")
            import traceback
            print(f"📋 详细错误信息:\n{traceback.format_exc()}")
            return []
    
    def download_image(self, image_url, filename):
        """下载图片"""
        try:
            print(f"正在下载图片: {image_url[:50]}...")
            
            # 使用浏览器的cookies来下载图片
            cookies = self.driver.get_cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.doubao.com/',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }
            
            response = requests.get(image_url, headers=headers, cookies=cookie_dict, timeout=30)
            
            if response.status_code == 200:
                # 检查响应内容是否为有效图片
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                print(f"响应状态: {response.status_code}")
                print(f"内容类型: {content_type}")
                print(f"文件大小: {content_length} 字节")
                
                # 验证是否为有效图片（大小应该大于10KB）
                if content_length > 10240 and 'image' in content_type:
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"✅ 图片已保存为: {filename} (大小: {content_length/1024:.1f}KB)")
                    return True
                else:
                    print(f"❌ 下载的文件不是有效图片 (大小: {content_length} 字节, 类型: {content_type})")
                    return False
            else:
                print(f"❌ 下载图片失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 下载图片时出现错误: {e}")
            return False
    
    def generate_images(self, prompts):
        """批量生成图片"""
        results = []
        
        for i, prompt in enumerate(prompts):
            print(f"\n=== 测试 {i+1}: {prompt} ===")
            
            # 通过浏览器生成图片
            image_urls = self.send_image_request_via_browser(prompt)
            
            if image_urls:
                # 检查返回结果类型
                if isinstance(image_urls[0], str) and not image_urls[0].startswith('http'):
                    # 如果返回的是文件名列表，说明已经下载完成，不需要重复下载
                    downloaded_files = image_urls
                    print(f"✅ 图片已下载完成，共 {len(downloaded_files)} 张图片")
                else:
                    # 如果返回的是URL列表，需要下载
                    downloaded_files = []
                    for j, url in enumerate(image_urls):
                        filename = f"generated_image_{i+1}_{j+1}.jpg"
                        if self.download_image(url, filename):
                            downloaded_files.append(filename)
                    print(f"✅ 生成成功，保存了 {len(downloaded_files)} 张图片")
                
                results.append({
                    'prompt': prompt,
                    'success': True,
                    'image_urls': image_urls,
                    'downloaded_files': downloaded_files
                })
            else:
                results.append({
                    'prompt': prompt,
                    'success': False,
                    'image_urls': [],
                    'downloaded_files': []
                })
                print(f"❌ 生成失败")
            
            # 等待一段时间再处理下一个
            if i < len(prompts) - 1:
                print("等待3秒...")
                time.sleep(3)
        
        return results
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()

# 使用示例
if __name__ == "__main__":
    # 创建图片生成器实例
    generator = DoubaoImageGenerator(headless=False)  # 设置为False以便看到浏览器界面
    
    try:
        # 登录并提取参数
        if generator.login_and_extract_params():
            # 测试图片生成
            test_prompts = [
                 "生成一朵空谷幽兰"
                # "生成一朵空谷幽兰",
                # # "画一只可爱的小猫咪",
                # # "创作一幅山水画",
                # "设计一个现代建筑"
            ]
            
            results = generator.generate_images(test_prompts)
            
            # 保存结果
            with open('image_generation_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print("\n所有测试完成！结果已保存到 image_generation_results.json")
        else:
            print("登录失败，无法继续")
            
    except Exception as e:
        print(f"程序执行出现错误: {e}")
    
    finally:
        generator.close()