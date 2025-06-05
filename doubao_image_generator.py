import logging
import time
import json
import requests
import re
import os
from PIL import Image
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
            logger.info("ChromeDriver initialized via WebDriverManager.")
        except Exception as e:
            logger.error(f"ChromeDriver设置失败 (WebDriverManager): {e}", exc_info=True)
            try:
                logger.info("Attempting to initialize ChromeDriver with default options...")
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("ChromeDriver initialized with default options (fallback).")
            except Exception as e2:
                logger.error(f"无法初始化ChromeDriver (fallback attempt): {e2}", exc_info=True)
                raise Exception(f"无法初始化ChromeDriver: {e2}")
        
        self.driver.implicitly_wait(10)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def login_and_extract_params(self):
        """登录豆包并提取必要的参数"""
        try:
            logger.info("正在访问豆包网站 https://www.doubao.com/chat/ ...")
            self.driver.get('https://www.doubao.com/chat/')
            
            logger.info("等待页面加载 (5s)...")
            time.sleep(5)
            
            try:
                login_button_xpath = "//button[contains(text(), '登录') or contains(text(), '登陆')]|//a[contains(text(), '登录') or contains(text(), '登陆')]"
                login_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, login_button_xpath))
                )
                logger.info("检测到需要登录，请在浏览器中手动完成登录过程。程序将等待最多5分钟。")
                
                WebDriverWait(self.driver, 300).until( # Wait up to 5 minutes for login
                    lambda driver: "chat" in driver.current_url and len(driver.get_cookies()) > 5
                )
                logger.info("登录成功或已继续！")
                
            except Exception: # TimeoutException or other
                logger.info("可能已经登录或无需登录，未找到明确的登录按钮或等待超时。")
            
            logger.info("等待页面参数加载 (3s)...")
            time.sleep(3)
            
            self.extract_dynamic_params()
            return True
            
        except Exception as e:
            logger.error(f"登录过程中出现错误: {e}", exc_info=True)
            return False
    
    def extract_dynamic_params(self):
        """从当前页面提取动态参数"""
        try:
            logger.info("开始提取动态参数...")
            current_url = self.driver.current_url
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)
            
            self.device_id = query_params.get('device_id', [self.device_id])[0]
            self.web_id = query_params.get('web_id', [self.web_id])[0]
            
            cookies = self.driver.get_cookies()
            self.msToken = next((cookie['value'] for cookie in cookies if cookie['name'] == 'msToken'), self.msToken)

            if not self.device_id or not self.web_id:
                logger.info("Device ID或Web ID未在URL中找到，尝试从页面源中提取...")
                page_source = self.driver.page_source
                
                device_id_match = re.search(r'device_id["\']?\s*[:=]\s*["\']?(\d+)', page_source)
                if device_id_match: self.device_id = device_id_match.group(1)
                
                web_id_match = re.search(r'web_id["\']?\s*[:=]\s*["\']?(\d+)', page_source)
                if web_id_match: self.web_id = web_id_match.group(1)
            
            # Fallback to defaults if still not found
            if not self.device_id:
                self.device_id = "7511556792158717459"
                logger.info(f"Device ID未找到, 使用默认值: {self.device_id}")
            if not self.web_id:
                self.web_id = "7511556796785526322"
                logger.info(f"Web ID未找到, 使用默认值: {self.web_id}")
            
            logger.info(f"提取的参数: device_id={self.device_id}, web_id={self.web_id}, msToken={'存在' if self.msToken else '未找到'}")
            if self.msToken:
                 logger.debug(f"msToken: {self.msToken[:20]}...")

        except Exception as e:
            logger.error(f"提取参数时出现错误: {e}", exc_info=True)
    
    def generate_a_bogus(self, url_params):
        """生成a_bogus参数（这是一个简化版本，实际可能需要更复杂的算法）"""
        try:
            logger.debug("尝试生成a_bogus参数 (当前为占位符实现)...")
            script = """
            // Placeholder for Doubao's a_bogus generation algorithm
            return 'generated_a_bogus_placeholder';
            """
            result = self.driver.execute_script(script)
            logger.debug(f"a_bogus占位符生成结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"生成a_bogus时出现错误: {e}", exc_info=True)
            return "Dj0nDtUEQxR5cplSYCmSHUo5q2A%252FNBuyusi2W7r57KugG7lPeA15xKpKbxTrCumiVmsiiF279jCjTdnOKb-yU81pqmkkSxvbf0IAV66L2qi4G0iQLrf0CukYeJtclQJwmQo6JA6V1UDOIVA1w3a0UdlyyKaxsO0pzNNfdcUGYIz6gMs9FNqQuPGdNXMC0U2b"
    
    def wait_for_image_generation(self, timeout=120):
        """
        Waits for image generation to complete, then attempts to find, get original URLs,
        and download the generated images. Returns a list of successfully downloaded filenames.
        """
        from selenium.common.exceptions import StaleElementReferenceException
        logger.info(f"⏳ Starting to wait for image generation, timeout: {timeout}s")
        start_time = time.time()
        # Counter for unique filenames within this specific call
        download_counter_this_call = 0

        while time.time() - start_time < timeout:
            elapsed = int(time.time() - start_time)
            try:
                # Check for loading indicators
                loading_indicators_xpath = "//div[contains(@class, 'loading') or contains(@class, 'generating') or contains(@class, 'spinner') or contains(@class, 'progress') or contains(text(), '生成中') or contains(text(), '正在生成')]"
                is_generating = False
                try:
                    visible_loaders = [el for el in self.driver.find_elements(By.XPATH, loading_indicators_xpath) if el.is_displayed()]
                    if visible_loaders:
                        is_generating = True
                        if elapsed % 10 == 0:
                            logger.debug(f"🔄 [{elapsed}s] Still generating, {len(visible_loaders)} loading indicators found.")
                except Exception as e_loader:
                    logger.warning(f"⚠️ [{elapsed}s] Error checking loading indicators: {e_loader}, assuming generation is ongoing.")
                    is_generating = True
                
                if not is_generating:
                    logger.info(f"🔍 [{elapsed}s] No loading indicators. Attempting to find and download images.")
                    # get_current_images_traditional returns a list of WebElements
                    image_elements = self.get_current_images_traditional()

                    if image_elements:
                        logger.info(f"🎉 Found {len(image_elements)} potential image elements.")
                        downloaded_files_this_cycle = []
                        for i, img_element in enumerate(image_elements):
                            try:
                                thumbnail_url = img_element.get_attribute('src')
                                if not thumbnail_url:
                                    logger.warning(f"Image element {i} has no src attribute. Skipping.")
                                    continue

                                logger.info(f"Processing image element {i+1}/{len(image_elements)} with src: {thumbnail_url[:70]}...")
                                # get_original_image_url handles verification internally
                                original_url = self.get_original_image_url(img_element, thumbnail_url)

                                if original_url: # get_original_image_url should return a verified URL or None
                                    timestamp_ms = int(time.time() * 1000)
                                    base_filename = f"generated_image_{timestamp_ms}_{download_counter_this_call}"
                                    download_counter_this_call += 1

                                    logger.info(f"Attempting to download image from: {original_url[:70]}... with base name {base_filename}")
                                    # download_image now returns full filename with extension or None
                                    actual_filename_with_ext = self.download_image(original_url, base_filename)
                                    if actual_filename_with_ext:
                                        logger.info(f"✅ Successfully downloaded and verified: {actual_filename_with_ext} from {original_url[:70]}.")
                                        downloaded_files_this_cycle.append(actual_filename_with_ext)
                                    else:
                                        # download_image already logs reasons for failure
                                        logger.warning(f"❌ Failed to download or verify image from {original_url[:70]}.")
                                else:
                                    logger.warning(f"No verifiable original URL found for image with thumbnail: {thumbnail_url[:70]}.")
                            except StaleElementReferenceException:
                                logger.warning(f"StaleElementReferenceException while processing image element {i}. Skipping.")
                                continue
                            except Exception as e_img_proc:
                                logger.error(f"Error processing image element {i}: {e_img_proc}", exc_info=True)
                                continue

                        if downloaded_files_this_cycle:
                            logger.info(f"Successfully downloaded {len(downloaded_files_this_cycle)} images in this cycle.")
                            return downloaded_files_this_cycle # Return list of filenames
                        else:
                            logger.info("No images were successfully downloaded in this cycle, though elements were found. Waiting for more.")
                    else:
                        logger.debug(f"[{elapsed}s] No image elements found by get_current_images_traditional in this cycle.")
                
                time.sleep(3) # Polling interval: increased slightly to 3s
                
            except Exception as e_loop:
                logger.error(f"❌ Error during wait_for_image_generation loop: {e_loop}", exc_info=True)
                time.sleep(3) # Wait before retrying loop
        
        # Timeout handling
        logger.warning(f"⏰ Timeout after {timeout}s waiting for image generation. Attempting to get current images one last time.")
        final_image_elements = self.get_current_images_traditional()
        final_downloaded_files = []
        if final_image_elements:
            logger.info(f"Timeout fallback: Found {len(final_image_elements)} potential image elements.")
            for i, img_element in enumerate(final_image_elements):
                try:
                    thumbnail_url = img_element.get_attribute('src')
                    if not thumbnail_url:
                        logger.warning(f"Timeout fallback: Image element {i} has no src. Skipping.")
                        continue

                    logger.info(f"Timeout fallback: Processing image {i+1}/{len(final_image_elements)} with src: {thumbnail_url[:70]}...")
                    original_url = self.get_original_image_url(img_element, thumbnail_url)

                    if original_url:
                        timestamp_ms = int(time.time() * 1000)
                        base_filename = f"generated_image_timeout_{timestamp_ms}_{download_counter_this_call}"
                        download_counter_this_call +=1

                        logger.info(f"Timeout fallback: Attempting download from {original_url[:70]}... with base name {base_filename}")
                        actual_filename_with_ext = self.download_image(original_url, base_filename)
                        if actual_filename_with_ext:
                            logger.info(f"Timeout fallback: ✅ Successfully downloaded and verified {actual_filename_with_ext}.")
                            final_downloaded_files.append(actual_filename_with_ext)
                        else:
                            logger.warning(f"Timeout fallback: ❌ Failed to download or verify from {original_url[:70]}.")
                    else:
                        logger.warning(f"Timeout fallback: No verifiable original URL for {thumbnail_url[:70]}.")
                except StaleElementReferenceException:
                    logger.warning(f"Timeout fallback: StaleElementReferenceException for image element {i}. Skipping.")
                except Exception as e_timeout_proc:
                    logger.error(f"Timeout fallback: Error processing image element {i}: {e_timeout_proc}", exc_info=True)

        if final_downloaded_files:
            logger.info(f"Timeout fallback: Successfully downloaded {len(final_downloaded_files)} images.")
        else:
            logger.warning("Timeout fallback: No images were downloaded.")
        return final_downloaded_files

    def get_current_images(self):
        """获取当前页面的所有生成图片"""
        logger.info("尝试通过JS辅助方法获取图片...") # Changed print to logger.info
        network_images = self.get_current_images_with_network_monitoring() # This name is historical
        
        if network_images:
            logger.info(f"JS辅助方法找到 {len(network_images)} 张图片。") # Changed print to logger.info
            return network_images
        
        logger.warning("JS辅助方法失败或未找到图片，回退到传统XPath方法...") # Changed print to logger.warning
        return self.get_current_images_traditional()

    def find_images_with_javascript(self):
        """使用JavaScript查找图片"""
        script = """
        const images = Array.from(document.querySelectorAll('img'));
        const uiKeywords = ['logo', 'icon', 'avatar', 'profile', 'button', 'menu', 'banner', 'ad', 'sprite', 'captcha', 'placeholder', 'loading', 'default', 'static', 'assets', 'ui', 'css', 'js', 'track', 'pixel', 'beacon', 'share', 'social', 'favicon', 'emoji', 'sticker'];
        let generatedImages = [];

        images.forEach(img => {
            const src = (img.src || '').toLowerCase();
            const alt = (img.alt || '').toLowerCase();

            // Basic checks for presence of src and minimum dimensions
            if (!src || img.naturalWidth < 50 || img.naturalHeight < 50) { // Use naturalWidth for actual image size if loaded
                return;
            }

            // Check if src or alt contains any UI keywords
            let isUIElement = false;
            for (const keyword of uiKeywords) {
                if (src.includes(keyword) || alt.includes(keyword)) {
                    isUIElement = true;
                    break;
                }
            }
            if (isUIElement) {
                return;
            }

            // Doubao specific checks (byteimg.com and image_skill are strong indicators)
            // Also check for imagex-type='react' or class 'image-' as positive signals
            const imagexType = (img.getAttribute('imagex-type') || '').toLowerCase();
            const className = (img.className || '').toLowerCase();

            if ( (src.includes('byteimg.com') && src.includes('image_skill')) ||
                 imagexType === 'react' ||
                 className.includes('image-') ) {
                // Additional check for reasonable size (offsetWidth might be 0 if not visible)
                if (img.offsetWidth > 100 && img.offsetHeight > 100 && img.offsetParent !== null) {
                     generatedImages.push({
                        src: img.src, // Keep original casing for src
                        alt: img.alt, // Keep original casing for alt
                        width: img.offsetWidth,
                        height: img.offsetHeight,
                        visible: true
                    });
                }
            }
        });
        return generatedImages;
        """
        
        try:
            image_data_list = self.driver.execute_script(script)
            logger.info(f"[find_images_with_javascript] JavaScript found {len(image_data_list)} potential images.")
            
            all_images = []
            if image_data_list:
                for data in image_data_list:
                    try:
                        if data and data['src']:
                            # Find by src, ensure it's exactly the one JS found
                            # Using a more precise XPath to avoid ambiguity if multiple images have similar processed URLs
                            img_element = self.driver.find_element(By.XPATH, f"//img[@src='{data['src']}' and @width='{data['width']}' and @height='{data['height']}']")
                            all_images.append(img_element)
                        else:
                            logger.debug("[find_images_with_javascript] Skipping image data with no src or dimensions.")
                    except Exception as e_find:
                        logger.debug(f"[find_images_with_javascript] Could not precisely find element for src {data.get('src', 'N/A')} with reported dimensions: {e_find}")
                        # Fallback to just src if precise match fails
                        try:
                            img_element = self.driver.find_element(By.XPATH, f"//img[@src='{data['src']}']")
                            all_images.append(img_element)
                            logger.debug(f"[find_images_with_javascript] Found element with src {data.get('src', 'N/A')} using fallback XPath.")
                        except Exception as e_find_fallback:
                             logger.debug(f"[find_images_with_javascript] Fallback XPath also failed for src {data.get('src', 'N/A')}: {e_find_fallback}")
                        continue
            return all_images
        except Exception as e:
            logger.error(f"[find_images_with_javascript] JavaScript execution or processing failed: {e}", exc_info=True)
            return []

    def get_current_images_traditional(self):
        """传统的图片获取方法（通过多种策略获取所有生成的原图）"""
        try:
            # from selenium.webdriver.common.action_chains import ActionChains # Not used directly here
            from selenium.common.exceptions import StaleElementReferenceException

            logger.info("[get_current_images_traditional] Starting traditional image retrieval.")
            time.sleep(1) # Reduced sleep, page should be mostly stable

            candidate_elements = []
            js_images = self.find_images_with_javascript() # Use improved JS function
            if js_images:
                logger.info(f"[get_current_images_traditional] Found {len(js_images)} candidate images via JavaScript.")
                candidate_elements.extend(js_images)
            else:
                logger.info("[get_current_images_traditional] JavaScript method found no images, trying XPath selectors.")
                # Refined and more specific selectors
                image_selectors = [
                    "//img[@imagex-type='react' and contains(@src, 'byteimg.com/image_skill/') and not(contains(@src, 'gif'))]",
                    "//div[contains(@class, 'image-box') or contains(@class, 'img-list-item')]//img[contains(@src, 'byteimg.com/image_skill/')]",
                    "//img[contains(@class, 'image-') and contains(@src, 'byteimg.com') and contains(@src, 'image_skill')]",
                    "//img[contains(@src, 'ocean-cloud-tos') and contains(@src, 'image_skill') and not(contains(@src, 'gif'))]",
                    "//picture[contains(@class, 'image-card')]//img[contains(@src, 'byteimg.com')]" # Picture elements often wrap generated images
                ]
                
                raw_elements_from_selectors = []
                for idx, selector in enumerate(image_selectors):
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        if elements:
                            logger.debug(f"[get_current_images_traditional] Selector {idx+1} ('{selector[:50]}...') found {len(elements)} elements.")
                            raw_elements_from_selectors.extend(elements)
                    except Exception as e_sel:
                        logger.warning(f"[get_current_images_traditional] Selector '{selector[:50]}...' failed: {e_sel}")

                if raw_elements_from_selectors:
                    candidate_elements.extend(list(dict.fromkeys(raw_elements_from_selectors))) # Deduplicate elements from XPath
            
            if not candidate_elements:
                logger.warning("[get_current_images_traditional] No candidate image elements found from JS or XPath.")
                return []

            logger.info(f"[get_current_images_traditional] Collected {len(candidate_elements)} raw candidate image elements in total.")
            unique_images_elements = list(dict.fromkeys(candidate_elements)) # Final deduplication
            logger.info(f"[get_current_images_traditional] Deduplicated to {len(unique_images_elements)} unique candidate elements.")


            filtered_image_elements = []
            seen_srcs = set()
            
            for i, img_element in enumerate(unique_images_elements):
                try:
                    src = img_element.get_attribute('src')
                    if not src or src in seen_srcs:
                        if src in seen_srcs:
                            logger.debug(f"[get_current_images_traditional] Skipping already seen src: {src[:60]}...")
                        continue

                    if not self.is_likely_generated_image(src):
                        logger.debug(f"[get_current_images_traditional] Filtered out by is_likely_generated_image: {src[:60]}...")
                        continue
                    
                    # Structural checks (attributes, class)
                    imagex_type = img_element.get_attribute('imagex-type')
                    img_class = img_element.get_attribute('class') or ''
                    
                    is_positive_indicator = (imagex_type == 'react') or \
                                            ('image-' in img_class) or \
                                            ('generated' in img_class) or \
                                            ('creation' in img_class)

                    # Dimension check
                    try:
                        # Ensure element is visible for size check to be meaningful
                        if not img_element.is_displayed():
                            logger.debug(f"[get_current_images_traditional] Skipping non-displayed image: {src[:60]}...")
                            continue
                        width = img_element.size.get('width', 0)
                        height = img_element.size.get('height', 0)
                        if not (width > 80 and height > 80): # Slightly reduced minimum dimensions
                            logger.debug(f"[get_current_images_traditional] Filtered out by size ({width}x{height}): {src[:60]}...")
                            continue
                    except StaleElementReferenceException:
                        logger.warning(f"[get_current_images_traditional] Stale element for image {src[:60]} during size check, skipping.")
                        continue
                    except Exception as e_size:
                        logger.warning(f"[get_current_images_traditional] Error checking size for {src[:60]}...: {e_size}, proceeding with caution.")

                    # If it has positive structural indicators OR is from a highly trusted source pattern
                    if is_positive_indicator or ('byteimg.com/image_skill/' in src) or ('ocean-cloud-tos' in src and 'image_skill' in src) :
                        filtered_image_elements.append(img_element)
                        seen_srcs.add(src)
                        logger.info(f"[get_current_images_traditional] Added valid image element: {src[:60]} (Indicator: {is_positive_indicator}, Class: {img_class})")
                    else:
                        logger.debug(f"[get_current_images_traditional] Filtered out (lacked strong indicators & not from primary CDN path): {src[:60]}...")

                except StaleElementReferenceException:
                    logger.warning(f"[get_current_images_traditional] Stale element for element at index {i}, skipping.")
                    continue
                except Exception as e_filter: # Catch other errors during this complex filtering
                    logger.error(f"[get_current_images_traditional] Error filtering image at index {i}: {e_filter}", exc_info=True)
                    continue
            
            logger.info(f"[get_current_images_traditional] Filtered down to {len(filtered_image_elements)} strong candidate image elements.")
            
            if not filtered_image_elements:
                logger.warning("[get_current_images_traditional] No valid generated images found after all filtering.")
                return []

            valid_image_urls = []
            for i, img_element_to_process in enumerate(filtered_image_elements, 1):
                src_to_process = "N/A"
                try:
                    src_to_process = img_element_to_process.get_attribute('src')
                    if not src_to_process: continue # Should have src if it passed filters

                    logger.info(f"[get_current_images_traditional] Processing URL for image {i}/{len(filtered_image_elements)}: {src_to_process[:70]}...")
                    
                    self.driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", img_element_to_process)
                    time.sleep(0.3) # Shorter sleep, just for scroll to settle
                    
                    original_url = self.get_original_image_url(img_element_to_process, src_to_process) # This now calls verify_image_accessibility
                    
                    # get_original_image_url itself now handles verification and logging of success/failure
                    # It returns the original URL if found and verified, otherwise the (verified) thumbnail.
                    # So, we just add what it returns, provided it's a URL.
                    if original_url and isinstance(original_url, str) and original_url.startswith('http'):
                         valid_image_urls.append(original_url)
                    elif src_to_process: # Fallback if original_url is somehow invalid
                         logger.warning(f"[get_current_images_traditional] get_original_image_url did not return a valid URL for {src_to_process}, using src after conversion and verification.")
                         fallback_url = self.convert_to_original_url_enhanced(src_to_process)
                         if self.verify_image_accessibility(fallback_url):
                            valid_image_urls.append(fallback_url)
                         else:
                            logger.error(f"[get_current_images_traditional] Fallback URL {fallback_url} also not accessible for {src_to_process}.")

                except StaleElementReferenceException:
                    logger.warning(f"[get_current_images_traditional] Stale element when processing image {i} ({src_to_process[:70]}...), skipping.")
                except Exception as e_proc:
                    logger.error(f"[get_current_images_traditional] Error processing image {i} ({src_to_process[:70]}...): {e_proc}", exc_info=True)
                    if src_to_process and src_to_process.startswith('http'): # Last resort, add original src if known
                        valid_image_urls.append(src_to_process)
                    continue
            
            final_urls = list(dict.fromkeys(valid_image_urls)) # Deduplicate final list
            logger.info(f"[get_current_images_traditional] Final list of {len(final_urls)} image URLs prepared.")
            return final_urls
            
        except Exception as e:
            logger.error(f"[get_current_images_traditional] Major error in image retrieval: {e}", exc_info=True)
            return []

    def get_original_image_url(self, img_element, thumbnail_url):
        """获取图片的原图URL"""
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.keys import Keys # Ensure Keys is imported
        actions = ActionChains(self.driver)
        
        # Method 1: Check picture element
        logger.info("[get_original_image_url] Attempting method 1: Get URL from picture element")
        try:
            picture_url = self.get_original_url_from_picture_element(img_element)
            if picture_url and picture_url != thumbnail_url and self.verify_image_accessibility(picture_url):
                logger.info(f"[get_original_image_url] Original URL found via picture element: {picture_url}")
                return picture_url
        except Exception as e:
            logger.error(f"[get_original_image_url] Error getting URL from picture element: {e}")

        # Method 2: Find and interact with a download button
        logger.info("[get_original_image_url] Attempting method 2: Find and interact with download button")
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img_element)
            time.sleep(1)
            actions.move_to_element(img_element).perform()
            time.sleep(1) # Reduced sleep time after hover

            download_selectors = [
                ".//ancestor::div[contains(@class, 'image-actions')]//button[contains(@aria-label, '下载') or contains(@title, '下载')]", # More specific
                "//div[contains(@class, 'image-') or contains(@class, 'img-')]//button[contains(@class, 'download') or contains(@title, 'download') or contains(@aria-label, 'download')]",
                "//div[contains(@class, 'image-') or contains(@class, 'img-')]//a[contains(@class, 'download') or contains(@title, 'download')]",
                ".//ancestor::div[contains(@class, 'image') or contains(@class, 'img') or contains(@class, 'picture')]//button[contains(., '下载') or contains(@aria-label, '下载')]",
                ".//ancestor::div[1]//button[contains(@class, 'download') or contains(@title, '下载') or contains(@aria-label, 'download') or contains(text(), '下载') or contains(@class, 'btn')]",
                ".//ancestor::div[2]//button[contains(@class, 'download') or contains(@title, '下载') or contains(@aria-label, 'download') or contains(text(), '下载') or contains(@class, 'btn')]",
                "//button[contains(@class, 'download') or contains(@title, '下载') or contains(@aria-label, '下载') or contains(text(), '下载')]",
            ]
            
            for selector in download_selectors:
                buttons = []
                if selector.startswith('.//'):
                    try:
                        buttons = img_element.find_elements(By.XPATH, selector)
                    except: continue
                else:
                    try:
                        buttons = self.driver.find_elements(By.XPATH, selector)
                    except: continue
                
                for button in buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            # Attempt to get URL from href if it's an <a> tag
                            if button.tag_name == 'a' and button.get_attribute('href'):
                                potential_url = button.get_attribute('href')
                                if self.verify_image_accessibility(potential_url):
                                    logger.info(f"[get_original_image_url] Original URL found via download button (href): {potential_url}")
                                    return potential_url
                            
                            # Click the button and check for new URL
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(2) # Wait for action to complete

                            download_url = self.get_download_url_from_browser() # Assumes this method checks network or new tab
                            if download_url and download_url != thumbnail_url and self.verify_image_accessibility(download_url):
                                logger.info(f"[get_original_image_url] Original URL found via download button (click): {download_url}")
                                return download_url
                    except Exception as e:
                        logger.warning(f"[get_original_image_url] Error interacting with download button (selector: {selector}): {e}")
                        continue
        except Exception as e:
            logger.error(f"[get_original_image_url] Error finding/interacting with download button: {e}")

        # Method 3: Check image attributes
        logger.info("[get_original_image_url] Attempting method 3: Get URL from image attributes")
        try:
            attributes_to_check = ['data-original', 'data-src', 'data-full-url', 'src']
            for attr in attributes_to_check:
                potential_url = img_element.get_attribute(attr)
                if potential_url:
                    # Try converting to a more "original" version if needed
                    converted_url = self.convert_to_original_url_enhanced(potential_url)
                    if converted_url and converted_url != thumbnail_url and self.verify_image_accessibility(converted_url):
                        logger.info(f"[get_original_image_url] Original URL found via attribute '{attr}': {converted_url}")
                        return converted_url
                    # Check original potential_url if conversion is not different or not better
                    if potential_url != thumbnail_url and self.verify_image_accessibility(potential_url):
                        logger.info(f"[get_original_image_url] Original URL found via attribute '{attr}' (no conversion): {potential_url}")
                        return potential_url
        except Exception as e:
            logger.error(f"[get_original_image_url] Error getting URL from attributes: {e}")

        # Method 4: Context menu (lower priority)
        logger.info("[get_original_image_url] Attempting method 4: Get URL from context menu")
        try:
            actions.context_click(img_element).perform()
            time.sleep(1)

            context_options = [
                "//div[contains(text(), '在新标签页中打开图片') or contains(text(), 'Open image in new tab')]",
                "//span[contains(text(), '在新标签页中打开图片') or contains(text(), 'Open image in new tab')]"
            ]

            for option_xpath in context_options:
                try:
                    option = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, option_xpath))
                    )
                    if option.is_displayed():
                        option.click()
                        time.sleep(2)

                        if len(self.driver.window_handles) > 1:
                            original_window = self.driver.current_window_handle
                            new_window = [h for h in self.driver.window_handles if h != original_window][0]
                            self.driver.switch_to.window(new_window)

                            current_url = self.driver.current_url
                            self.driver.close() # Close new tab
                            self.driver.switch_to.window(original_window) # Switch back

                            if current_url and current_url != thumbnail_url and self.verify_image_accessibility(current_url):
                                logger.info(f"[get_original_image_url] Original URL found via context menu: {current_url}")
                                return current_url
                        break
                except:
                    continue
            
            # Press ESC to close context menu if it's still open
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)

        except Exception as e:
            logger.error(f"[get_original_image_url] Error with context menu method: {e}")
            # Ensure ESC is sent if an error occurs during context menu interaction
            try:
                actions.send_keys(Keys.ESCAPE).perform()
            except:
                pass

        logger.warning(f"[get_original_image_url] No original URL found, returning thumbnail: {thumbnail_url}")
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
                logger.debug(f"[get_original_url_from_picture_element] 找到picture元素 for img_element.")
                source_selectors = [
                    ".//source[@type='image/avif']", ".//source[contains(@srcset, 'avif')]",
                    ".//source[@type='image/webp']", ".//source[contains(@srcset, 'webp')]",
                    ".//source" # Fallback to any source
                ]
                
                for selector in source_selectors:
                    try:
                        sources = picture_element.find_elements(By.XPATH, selector)
                        for source in sources:
                            srcset = source.get_attribute('srcset') or source.get_attribute('src')
                            if srcset:
                                url = srcset.split(' ')[0].split(',')[0].strip() # Get first URL from srcset
                                if url and 'byteimg.com' in url: # Ensure it's a relevant domain
                                    logger.debug(f"[get_original_url_from_picture_element] 从 <source {source.get_attribute('type') or ''}> 获取到URL: {url}")
                                    # URL conversion happens in get_original_image_url before verification
                                    return url
                    except Exception as e_src:
                        logger.debug(f"[get_original_url_from_picture_element] 处理source元素时出错 (selector: {selector}): {e_src}")
                        continue
            else:
                logger.debug("[get_original_url_from_picture_element] 未找到父级picture元素。")
            return None
            
        except Exception as e:
            logger.error(f"[get_original_url_from_picture_element] 获取picture元素URL时出错: {e}", exc_info=True)
            return None

    def convert_to_original_url_enhanced(self, thumbnail_url):
        """增强的URL转换方法"""
        if not thumbnail_url: # Ensure re is imported
            return thumbnail_url

        # Ensure re is available, it should be imported at the top of the file
        # import re

        original_url = thumbnail_url
        logger.info(f"[convert_to_original_url_enhanced] Original thumbnail URL: {thumbnail_url}")

        # General and Doubao-specific conversion rules
        conversion_rules = [
            # Remove Doubao specific tplv parameters (often includes processing instructions)
            (r'~tplv-[^?&]+', ''),

            # Remove common web thumbnail/watermark identifiers
            (r'-web-thumb-watermark-v2', ''),
            (r'-web-thumb-watermark', ''),
            (r'-web-thumb-wm', ''),
            (r'-watermark-v2', ''),
            (r'-watermark', ''),
            (r'-thumb', ''),
            (r'-wm', ''),
            (r'_thumb\b', ''), # Suffix _thumb
            (r'\.thumb\b', ''), # .thumb before extension

            # Remove format specific suffixes that might indicate conversion
            (r'-avif\.avif$', ''),
            (r'-webp\.webp$', ''),

            # Attempt to change suspicious formats to a common original format (JPEG or PNG)
            # These rules are more aggressive and should be placed after specific removals
            (r'\.avif(\?|$)', '.jpeg\\1'), # Convert .avif to .jpeg, keeping query params
            (r'\.webp(\?|$)', '.jpeg\\1'), # Convert .webp to .jpeg, keeping query params

            # Remove specific path segments indicating thumbnails or previews
            (r'/thumb/', '/'),
            (r'/preview/', '/'),
            (r'/small/', '/'),
            (r'/medium/', '/'),
            (r'/large/', '/'), # Sometimes 'large' is still not original

            # Remove common CDN query parameters for resizing, quality, format
            (r'[?&](w|h|width|height|size|s|dim)=\d+&?', '', True), # Dimension params
            (r'[?&](quality|q)=\d+&?', '', True),                  # Quality params
            (r'[?&](format|fm|f)=(jpeg_thumb|jpg_thumb|png_thumb|webp_thumb|avif_thumb|jpeg|png|webp|avif)&?', '', True), # Format params
            (r'[?&]Strip=all&?', '', True),                       # Stripping metadata
            (r'[?&]fit=(min|max|crop|fill|scale)&?', '', True),    # Fit params
            (r'[?&]crop=[^&]+&?', '', True),                       # Crop params
            (r'[?&]auto=compress&?', '', True),                   # Auto compress

            # Remove Doubao/Bytedance specific query parameters if they weren't caught by tplv
            (r'\?[^?]*tplv[^&]*', '', False), # More generic tplv in query
            (r'&[^&]*tplv[^&]*', '', False),

            # Remove signature parameters (often tied to specific thumbnail settings)
            (r'[?&]rk3s=[^&]*', '', False),
            (r'[?&]x-expires=[^&]*', '', False),
            (r'[?&]x-signature=[^&]*', '', False),
            (r'[?&]sign=[^&]*', '', False),
        ]

        for rule_set in conversion_rules:
            pattern, replacement = rule_set[0], rule_set[1]
            is_query_param_removal = rule_set[2] if len(rule_set) > 2 else False

            old_url = original_url

            if is_query_param_removal:
                # Iteratively remove query parameters to handle multiple occurrences and ordering
                temp_url = original_url
                while True:
                    # Ensure the pattern correctly handles being the first, middle or last param
                    # Adjusted regex to better handle leading ? or &
                    # e.g. (?<=[?&])param=value&?  or  \?param=value&? (for first param)
                    # For simplicity, we'll just remove and then clean up ?, & later
                    updated_url = re.sub(pattern, replacement, temp_url, count=1)
                    if updated_url == temp_url: # No more occurrences of this pattern
                        break
                    temp_url = updated_url
                original_url = temp_url
            else:
                original_url = re.sub(pattern, replacement, original_url)

            if old_url != original_url:
                logger.debug(f"URL before rule '{pattern}': {old_url}")
                logger.debug(f"URL after rule '{pattern}': {original_url}")

        # Clean up URL structure
        # Remove trailing '?' or '&'
        original_url = re.sub(r'[?&]+$', '', original_url)
        # Replace '?&' with '?'
        original_url = re.sub(r'\?&', '?', original_url)
        # Replace '&&' with '&'
        original_url = re.sub(r'&&+', '&', original_url)
        # Ensure '?' is only if there are params
        if '?' in original_url and not original_url.split('?', 1)[1]:
            original_url = original_url.split('?', 1)[0]

        logger.info(f"[convert_to_original_url_enhanced] URL after all rules: {original_url}")

        # Fallback logic: if URL hasn't changed much or still seems like a thumbnail
        if original_url == thumbnail_url or "thumb" in original_url or "preview" in original_url:
            logger.debug("[convert_to_original_url_enhanced] Fallback: Attempting to extract base URL or reconstruct.")
            # Try to get the base part of the URL, removing query string and common thumbnail markers
            base_match = re.match(r'(https://[^?#]+)', original_url)
            if base_match:
                base_url = base_match.group(1)
                # Further clean common suffixes if any are left
                base_url = re.sub(r'(_(small|medium|large|thumb|preview))?\.(jpg|jpeg|png|webp|avif)$', '', base_url, flags=re.IGNORECASE)
                
                # Prefer .png or .jpeg as high-quality original formats
                if not base_url.lower().endswith(('.png', '.jpeg', '.jpg')):
                    base_url += '.jpeg'
                
                if base_url != original_url:
                    logger.debug(f"[convert_to_original_url_enhanced] Fallback: Using base URL: {base_url}")
                    original_url = base_url
                else:
                    # If base_url extraction didn't significantly change, try Doubao specific reconstruction
                    id_match = re.search(r'image_skill/([^~?]+)', thumbnail_url)
                    if id_match:
                        image_id = id_match.group(1).split('.')[0] # Get ID before any format suffix
                        domain_match = re.match(r'(https://[^/]+)', thumbnail_url)
                        if domain_match:
                            domain = domain_match.group(1)
                            constructed_url = f"{domain}/ocean-cloud-tos/image_skill/{image_id}.png" # Try PNG first
                            logger.debug(f"[convert_to_original_url_enhanced] Fallback: Constructed Doubao URL (PNG): {constructed_url}")
                            # Here, one might add a check if .png is valid, then try .jpeg if not.
                            # For now, we'll assume .png or .jpeg are good defaults.
                            original_url = constructed_url
            else:
                logger.debug("[convert_to_original_url_enhanced] Fallback: Could not extract base URL.")

        logger.info(f"[convert_to_original_url_enhanced] Final converted URL: {original_url}")
        return original_url
            
        # except Exception as e: # This broad except might catch NameError for re if not imported
        #     logger.error(f"[convert_to_original_url_enhanced] URL conversion failed: {e}")
        #     return thumbnail_url

    def is_likely_generated_image(self, url):
        """判断URL是否为生成的图片 (Improved)."""
        if not url or not isinstance(url, str) or not url.startswith('http'):
            logger.debug(f"[is_likely_generated_image] Invalid URL provided: {url}")
            return False
        
        url_lower = url.lower()

        # More comprehensive exclusion list for UI elements, ads, trackers, etc.
        # Added 'banner', 'ad', 'sprite', 'captcha', and path-based exclusions.
        exclude_patterns = [
            'data:image/svg+xml', 'data:image/gif', # Common placeholders or tiny images
            'avatar', 'icon', 'logo', 'profile', 'button', 'menu', 'banner', 'ad', 'sprite', 'captcha', 'badge', 'flag',
            'placeholder', 'loading', 'default', 'bg-', '-bg', 'background', 'spinner', 'shimmer', 'skeleton',
            'static', 'assets', 'ui', 'css', 'js', 'track', 'pixel', 'beacon', 'share', 'social', 'payment', 'card',
            'thumb_', '_thumb', '.thumb', '_small', '.small', '_ico', '.ico', '_thumbnail', '.thumbnail', # Thumbnail indicators
            'favicon', 'apple-touch-icon', 'emoji', 'sticker', # Often not generated content
            '/ads/', '/banners/', '/buttons/', '/icons/', '/logos/', '/avatars/', '/widgets/', '/static/', '/assets/', '/img/ui/',
            '1x1', 'pixel.gif', 'blank.gif', 'empty.png', # Common tracking pixels or spacers
            'sprite', 'spritesheet', 'gradient', 'pattern', # CSS related images
            'logo-white', 'logo-dark', # Variations of logos
            'example.com', 'via.placeholder.com', # Placeholder services
            'gravatar.com', # Specific avatar service
        ]
        
        for pattern in exclude_patterns:
            if pattern in url_lower:
                logger.debug(f"[is_likely_generated_image] URL excluded by pattern '{pattern}': {url_lower[:70]}...")
                return False
        
        # Refined Doubao/Bytedance patterns - prioritize more specific ones
        doubao_specific_patterns = [
            ('byteimg.com', 'image_skill'),
            ('sf-cdn.com', 'obj/eden-cn/'), # Another potential CDN for Doubao
            ('pstatp.com', 'origin/tos-cn-i-'), # CDN used by Bytedance products
            ('douyinpic.com', 'obj/') # Douyin (related) picture CDN
        ]

        general_generated_keywords = [
            'flow-imagex-sign.byteimg.com', # Strong Doubao/Bytedance signal
            'ocean-cloud-tos',             # Strong Bytedance CDN signal when combined with image paths
            'tplv-',                       # Bytedance image processing, often on generated or uploaded images
            # Keywords that might appear in paths or filenames of generated images.
            # Use cautiously as they can be part of user prompts or UI text.
            # 'ai_generated', 'aigc', 'diffusion', 'gan', 'neural', 'art_work'
        ]
        
        # Check for specific Doubao/Bytedance hosting and path patterns
        for domain, path_segment in doubao_specific_patterns:
            if domain in url_lower and path_segment in url_lower:
                logger.debug(f"[is_likely_generated_image] URL matched Doubao specific pattern ('{domain}', '{path_segment}'): {url_lower[:70]}...")
                return True

        # Check for general keywords associated with generated content CDNs or processing
        for pattern in general_generated_keywords:
            if pattern in url_lower:
                 # If 'tplv-' is found, it's highly likely a Bytedance image, could be original or processed.
                 # convert_to_original_url_enhanced handles stripping tplv- parameters.
                logger.debug(f"[is_likely_generated_image] URL matched general pattern '{pattern}': {url_lower[:70]}...")
                return True
        
        # Final check for image extensions - this is the weakest signal
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.avif']
        has_image_extension = any(url_lower.endswith(ext) or f"{ext}?" in url_lower for ext in image_extensions)

        if has_image_extension:
            # If it has an image extension but didn't match stronger patterns,
            # it's less certain. It might be a UI element not caught by exclude_patterns.
            # Rely on structural indicators (like imagex-type, class, size) in the calling functions.
            logger.debug(f"[is_likely_generated_image] URL has image extension but no strong generated patterns: {url_lower[:70]}.... Will rely on further checks.")
            return True # Tentatively true, expect more checks in calling function

        logger.debug(f"[is_likely_generated_image] URL did not match any exclusion or strong inclusion criteria: {url_lower[:70]}...")
        return False

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
            logger.info("网络日志记录已启用 (通过goog:loggingPrefs性能日志)。")
            
        except Exception as e:
            logger.error(f"启用网络日志失败: {e}", exc_info=True)

    def get_network_requests(self, filter_pattern=None):
        """获取网络请求记录 - Basic implementation, may need refinement for specific needs."""
        try:
            logger.debug(f"尝试获取性能日志 (filter: {filter_pattern})...")
            logs = self.driver.get_log('performance')
            requests_data = []
            
            for log_entry in logs:
                message = json.loads(log_entry['message'])
                if message.get('message', {}).get('method') == 'Network.responseReceived':
                    response = message['message']['params'].get('response', {})
                    url = response.get('url', '')
                    mime_type = response.get('mimeType', '')
                    
                    if filter_pattern:
                        if filter_pattern.lower() in url.lower():
                            requests_data.append({
                                'url': url, 'mimeType': mime_type,
                                'status': response.get('status', 0),
                                'headers': response.get('headers', {})
                            })
                    elif any(img_type in mime_type.lower() for img_type in ['image/png', 'image/jpeg', 'image/webp', 'image/avif', 'image/gif']):
                        requests_data.append({
                            'url': url, 'mimeType': mime_type,
                            'status': response.get('status', 0),
                            'headers': response.get('headers', {})
                        })
            
            logger.debug(f"[get_network_requests] Found {len(requests_data)} requests matching criteria.")
            return requests_data
            
        except Exception as e:
            logger.error(f"[get_network_requests] Error getting network requests: {e}", exc_info=True)
            return []

    def get_current_images_with_network_monitoring(self):
        """
        Retrieves current images, primarily using the JavaScript-based find_images_with_javascript.
        The name "network_monitoring" is a misnomer from previous versions if not actively parsing network logs here.
        """
        try:
            # from selenium.webdriver.common.action_chains import ActionChains # Not directly used
            from selenium.common.exceptions import StaleElementReferenceException

            logger.info("[get_current_images_with_network_monitoring] Starting image retrieval using JS-based finder.")
            time.sleep(0.5) # Shorter sleep, allowing for quick dynamic updates

            candidate_image_elements = self.find_images_with_javascript()
            
            if not candidate_image_elements:
                logger.warning("[get_current_images_with_network_monitoring] No candidate images found by JavaScript method. Consider fallback if necessary.")
                return [] # No images found
            
            logger.info(f"[get_current_images_with_network_monitoring] Found {len(candidate_image_elements)} candidate image elements via JavaScript.")
            
            valid_image_urls = []
            processed_src_urls = set()

            for i, img_element in enumerate(candidate_image_elements, 1):
                thumbnail_url_attr = "N/A"
                try:
                    thumbnail_url_attr = img_element.get_attribute('src')
                    if not thumbnail_url_attr or thumbnail_url_attr in processed_src_urls :
                        if thumbnail_url_attr in processed_src_urls:
                             logger.debug(f"[get_current_images_with_network_monitoring] Skipping already processed src: {thumbnail_url_attr[:70]}...")
                        continue # Skip if no src or already processed

                    logger.info(f"[get_current_images_with_network_monitoring] Processing element {i}/{len(candidate_image_elements)}: {thumbnail_url_attr[:70]}...")
                    processed_src_urls.add(thumbnail_url_attr)

                    # Scroll to image element to ensure it's interactable for get_original_image_url
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", img_element)
                        time.sleep(0.3)
                    except Exception as e_scroll:
                        logger.warning(f"[get_current_images_with_network_monitoring] Failed to scroll to image {thumbnail_url_attr[:70]}: {e_scroll}")
                        # Continue anyway, get_original_image_url might still work

                    # get_original_image_url now includes verification
                    original_url = self.get_original_image_url(img_element, thumbnail_url_attr)
                    
                    if original_url and original_url.startswith('http'):
                        # Ensure verify_image_accessibility was effectively called in get_original_image_url
                        # or call it explicitly here if get_original_image_url's contract changes.
                        # Current get_original_image_url should return a verified URL or verified thumbnail.
                        valid_image_urls.append(original_url)
                        logger.info(f"[get_current_images_with_network_monitoring] Added URL: {original_url[:70]}")
                    else:
                        logger.warning(f"[get_current_images_with_network_monitoring] No valid original or verified thumbnail URL obtained for {thumbnail_url_attr[:70]}")
                    
                except StaleElementReferenceException:
                    logger.warning(f"[get_current_images_with_network_monitoring] Stale element reference for image {i} ({thumbnail_url_attr[:70]}...), skipping.")
                except Exception as e: # Catch any other error during processing of a single image
                    logger.error(f"[get_current_images_with_network_monitoring] Error processing image {i} ({thumbnail_url_attr[:70]}...): {e}", exc_info=True)
            
            final_unique_urls = list(dict.fromkeys(valid_image_urls)) # Deduplicate
            logger.info(f"[get_current_images_with_network_monitoring] Final list of {len(final_unique_urls)} unique image URLs.")
            return final_unique_urls
            
        except Exception as e: # Catch errors for the whole function
            logger.error(f"[get_current_images_with_network_monitoring] Major error in function: {e}", exc_info=True)
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
            logger.error(f"[get_download_url_from_browser] Error getting download URL: {e}", exc_info=True)
            return None
    
    def get_image_real_url(self, img_element):
        """获取图片元素的真实URL"""
        try:
            logger.debug(f"尝试从元素属性获取真实URL: {img_element.tag_name}")
            methods = [
                lambda: img_element.get_attribute('data-original'),
                lambda: img_element.get_attribute('data-src'),
                lambda: img_element.get_attribute('data-full-url'),
                lambda: img_element.get_attribute('src'), # Last resort
            ]
            
            for i, method in enumerate(methods):
                try:
                    url = method()
                    logger.debug(f"  方法 {i+1} 得到URL: {url[:70] if url else 'None'}...")
                    if url and self.is_valid_image_url(url): # Basic check
                        # Conversion and deeper validation happens in get_original_image_url
                        return self.convert_to_original_url_enhanced(url)
                except Exception as e_attr:
                    logger.debug(f"  获取属性时出错 (方法 {i+1}): {e_attr}")
                    continue
            
            logger.warning(f"未能从元素属性中找到有效的图片URL: {img_element.tag_name}")
            return None
            
        except Exception as e:
            logger.error(f"获取真实URL时出现错误: {e}", exc_info=True)
            return None
    
    def download_image_via_browser(self, image_url, base_filename): # Changed 'filename' to 'base_filename'
        """通过浏览器下载图片（支持下载按钮方式）"""
        try:
            logger.info(f"尝试通过浏览器下载图片: {image_url[:70]}... as {base_filename}")
            
            if 'download' in image_url.lower() or 'original' in image_url.lower():
                return self.download_image(image_url, base_filename) # download_image handles extension
            
            original_window = self.driver.current_window_handle
            self.driver.execute_script(f"window.open('{image_url}', '_blank');")
            time.sleep(2) # Wait for new tab
            
            new_window = [handle for handle in self.driver.window_handles if handle != original_window][0]
            self.driver.switch_to.window(new_window)
            
            real_url = self.driver.current_url # URL might change/resolve in new tab
            logger.debug(f"URL in new tab for browser download: {real_url[:70]}...")
            
            self.driver.close()
            self.driver.switch_to.window(original_window)
            
            return self.download_image(real_url, base_filename) # download_image handles extension
            
        except Exception as e:
            logger.error(f"通过浏览器下载图片时出现错误: {e}", exc_info=True)
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
                    logger.info(f"[verify_image_accessibility] Verification passed for {url[:50]}... (Size: {int(content_length)/1024:.1f}KB, Type: {content_type})")
                    return True
                else: # This else was slightly misaligned in previous version, corrected.
                    logger.warning(f"[verify_image_accessibility] Verification failed for {url[:50]}... Status: {response.status_code}, Type: {content_type}, Length: {content_length}")
            
            return False
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"[verify_image_accessibility] Network error verifying URL {url[:50]}...: {e}")
            return False
        except Exception as e:
            logger.error(f"[verify_image_accessibility] Error verifying image URL {url[:50]}...: {e}", exc_info=True)
            return False
    
    def send_image_request_via_browser(self, prompt):
        """通过浏览器发送图片生成请求"""
        try:
            logger.info(f"🚀 开始生成图片: {prompt[:50]}...")
            logger.debug(f"📍 当前页面URL: {self.driver.current_url}")
            
            input_selectors = [
                "//textarea[@placeholder*='输入' or @placeholder*='消息' or @placeholder*='问题']",
                "//input[@placeholder*='输入' or @placeholder*='消息' or @placeholder*='问题']",
                "//div[@contenteditable='true']",
                "textarea[aria-label*='message']",
                "input[type='text'][placeholder*='Send']"
            ]
            
            logger.debug(f"🔍 开始查找输入框，共有 {len(input_selectors)} 个选择器")
            input_element = None
            for i, selector in enumerate(input_selectors):
                try:
                    logger.debug(f"  尝试选择器 {i+1}: {selector}")
                    element_type = "XPATH" if selector.startswith("//") else "CSS_SELECTOR"
                    input_element = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((getattr(By, element_type), selector))
                    )
                    logger.info(f"  ✅ 成功找到输入框: {selector}")
                    break
                except Exception:
                    logger.debug(f"  ❌ 选择器失败: {selector}")
                    continue
            
            if not input_element:
                logger.error("❌ 所有输入框选择器都失败了。无法发送提示词。")
                page_sample = self.driver.page_source[:500] # Log small part of page for context
                logger.debug(f"Page source sample for debugging input failure: {page_sample}")
                raise Exception("找不到输入框")
            
            logger.info(f"📝 清空输入框并输入提示词: {prompt[:50]}...")
            input_element.clear()
            time.sleep(0.2)
            input_element.send_keys(prompt)
            logger.debug("✅ 提示词输入完成")
            
            logger.info("📤 尝试发送消息...")
            try:
                input_element.send_keys(Keys.RETURN)
                logger.info("✅ 通过回车键发送成功")
            except Exception as e_return:
                logger.warning(f"❌ 回车键发送失败: {e_return}. 尝试查找发送按钮...")
                try:
                    send_button_xpath = "//button[contains(text(), '发送') or contains(text(), '提交') or contains(@aria-label, 'Send') or contains(@aria-label, 'Submit') or descendant::*[local-name()='svg' and (@aria-label='send' or @aria-label='发送')]]"
                    send_button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, send_button_xpath))
                    )
                    send_button.click()
                    logger.info("✅ 通过发送按钮发送成功")
                except Exception as e_button:
                    logger.error(f"❌ 发送按钮也失败: {e_button}", exc_info=True)
                    raise Exception(f"无法发送消息: {e_return} / {e_button}")
            
            logger.info("⏳ 消息已发送，开始等待图片生成...")
            
            result = self.wait_for_image_generation() # This now returns list of downloaded filenames
            
            if isinstance(result, list) and result:
                logger.info(f"🎯 图片生成并下载完成，共 {len(result)} 张图片。")
                return result
            else:
                logger.warning("❌ 未获取到有效的图片结果或下载失败。")
                return []
            
        except Exception as e:
            logger.error(f"❌ 通过浏览器生成图片时出现错误: {e}", exc_info=True)
            return []
    
    def download_image(self, image_url, base_filename):
        """
        Downloads an image from image_url to base_filename with an extension determined by Content-Type.
        Performs verification (size, integrity, dimensions) and returns the full filename if successful, else None.
        """
        try:
            logger.info(f"Attempting to download image: {image_url[:70]}... for base filename: {base_filename}")
            
            cookies = self.driver.get_cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.doubao.com/', # Important for some CDNs
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8', # Prioritize modern formats
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7'
            }
            
            response = requests.get(image_url, headers=headers, cookies=cookie_dict, timeout=30, stream=True)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                extension_map = {
                    'image/jpeg': '.jpg', 'image/jpg': '.jpg',
                    'image/png': '.png',
                    'image/webp': '.webp',
                    'image/avif': '.avif',
                    'image/gif': '.gif'
                }
                extension = '.jpg' # Default extension
                for mime, ext in extension_map.items():
                    if mime == content_type:
                        extension = ext
                        break
                logger.info(f"Determined extension '{extension}' for content-type '{content_type}' from URL: {image_url[:70]}")
                actual_filename_with_ext = base_filename + extension

                with open(actual_filename_with_ext, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192): # Stream content
                        f.write(chunk)
                
                # --- Verification ---
                min_file_size = 10240  # 10KB
                min_dimension = 300   # pixels, e.g., 300x300

                if not os.path.exists(actual_filename_with_ext):
                    logger.error(f"File {actual_filename_with_ext} not found after supposed write for URL: {image_url[:70]}.")
                    return None

                file_size = os.path.getsize(actual_filename_with_ext)
                if file_size < min_file_size:
                    logger.warning(f"Downloaded file {actual_filename_with_ext} is too small ({file_size} bytes). Might be a thumbnail or error page. Deleting.")
                    os.remove(actual_filename_with_ext)
                    return None

                try:
                    img = Image.open(actual_filename_with_ext)
                    img.verify() # Verifies integrity. Raises exception on error.
                    # Reopen after verify for formats that need it (e.g. JPEG)
                    img = Image.open(actual_filename_with_ext)
                    width, height = img.size
                    img.close() # Close image after getting dimensions

                    if width < min_dimension or height < min_dimension:
                        logger.warning(f"Image {actual_filename_with_ext} dimensions ({width}x{height}) are too small. Might be a thumbnail. Deleting.")
                        os.remove(actual_filename_with_ext)
                        return None

                    logger.info(f"✅ Successfully downloaded and verified {actual_filename_with_ext} (Size: {file_size} bytes, Dimensions: {width}x{height})")
                    return actual_filename_with_ext

                except FileNotFoundError: # Should be caught by os.path.exists above, but as a safeguard.
                     logger.error(f"File {actual_filename_with_ext} vanished before Pillow verification for URL: {image_url[:70]}.")
                     return None
                except Image.DecompressionBombError:
                    logger.warning(f"Image {actual_filename_with_ext} triggered DecompressionBombError. Likely too large or malformed. Deleting.")
                    if os.path.exists(actual_filename_with_ext): os.remove(actual_filename_with_ext)
                    return None
                except (IOError, SyntaxError, Image.UnidentifiedImageError) as e_pil: # Catch PIL specific errors
                    logger.warning(f"Image verification failed for {actual_filename_with_ext} using Pillow: {e_pil}. File might be corrupt or not a valid image. Deleting.")
                    if os.path.exists(actual_filename_with_ext): os.remove(actual_filename_with_ext)
                    return None
                except Exception as e_verify: # Other errors during verification
                    logger.error(f"Unexpected error during verification of {actual_filename_with_ext}: {e_verify}. Deleting.", exc_info=True)
                    if os.path.exists(actual_filename_with_ext): os.remove(actual_filename_with_ext)
                    return None
            else:
                logger.warning(f"Failed to download {image_url[:70]}. HTTP Status: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while trying to download {image_url[:70]}.")
            return None
        except requests.exceptions.RequestException as e_req:
            logger.error(f"Network error downloading {image_url[:70]}: {e_req}")
            return None
        except IOError as e_io: # e.g. disk full, permissions
            logger.error(f"File system error saving image to {base_filename} + ext: {e_io}", exc_info=True)
            return None
        except Exception as e_main: # Catch-all for other unexpected errors
            logger.error(f"An unexpected error occurred in download_image for {image_url[:70]}: {e_main}", exc_info=True)
            return None

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
            logger.debug(f"Detected valid {format_name} format for image content.")
                return True
            
            if signature == b'RIFF' and len(content) >= 12: # WEBP specific check
                if content[8:12] == b'WEBP':
                    logger.debug("Detected valid WEBP format for image content.")
                    return True
        
        logger.warning(f"Unrecognized image format. File header (first 16 bytes): {content[:16].hex()}")
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
                    logger.info(f"Image generation returned {len(image_filenames)} downloaded files directly.")
                    downloaded_files.extend(image_filenames) # Assuming image_filenames is a list of actual filenames
                    final_image_urls.extend(image_filenames) # Storing filenames if URLs aren't separately available
                
                elif isinstance(image_filenames, list) and all(isinstance(item, str) and item.startswith('http') for item in image_filenames):
                    # If it's a list of URLs, then download them
                    logger.info(f"Image generation returned {len(image_filenames)} URLs. Attempting downloads.")
                    temp_download_counter = 0
                    for j, url in enumerate(image_filenames):
                        prompt_prefix = re.sub(r'[^\w\s-]', '', prompt[:20]).replace(' ', '_')
                        base_filename = f"generated_{prompt_prefix}_{i+1}_{temp_download_counter}"

                        actual_file = self.download_image(url, base_filename)
                        if actual_file:
                            downloaded_files.append(actual_file)
                        final_image_urls.append(url) # Store original URL attempted
                        temp_download_counter += 1
                else:
                    logger.warning(f"Received unexpected result from send_image_request_via_browser: {type(image_filenames)}. Expected list of filenames or URLs.")

            if downloaded_files:
                logger.info(f"Successfully processed prompt '{prompt[:50]}...', {len(downloaded_files)} images downloaded.")
                results.append({
                    'prompt': prompt,
                    'success': True,
                    'image_urls': final_image_urls,
                    'downloaded_files': downloaded_files
                })
            else:
                logger.error(f"No images successfully downloaded for prompt: '{prompt[:50]}...'")
                results.append({
                    'prompt': prompt,
                    'success': False,
                    'image_urls': final_image_urls, # Still record URLs if any were processed
                    'downloaded_files': []
                })
            
            if i < len(prompts) - 1:
                logger.info("Waiting 3 seconds before next prompt...")
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
            
            logger.info("\n所有测试完成！结果已保存到 image_generation_results.json")
        else:
            logger.error("登录失败，无法继续图片生成测试。")
            
    except Exception as e:
        logger.critical(f"程序执行出现严重错误: {e}", exc_info=True)
    
    finally:
        logger.info("关闭浏览器会话...")
        generator.close()