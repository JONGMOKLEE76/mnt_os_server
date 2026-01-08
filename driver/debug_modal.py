import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Chrome WebDriver 경로 (main.py와 동일)
CHROME_DRIVER_PATH = 'D:\\GLOP Driver\\chromedriver.exe'

def main():
    chrome_options = Options()
    # chrome_options.add_argument('--headless') 
    
    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # 사이트 접속
        driver.get('https://glopp.lge.com/index.jsp')
        time.sleep(1)

        # 로그인
        try:
            id_input = driver.find_element(By.ID, 'userId')
            pw_input = driver.find_element(By.ID, 'userPwd')
            id_input.send_keys('paul76.lee')
            pw_input.send_keys('paul243756')
            
            login_img = driver.find_element(By.XPATH, "//img[contains(@src, 'login_btn.png')]")
            try:
                login_img.click()
            except Exception:
                parent_form = login_img.find_element(By.XPATH, './ancestor::form')
                submit_btn = parent_form.find_element(By.XPATH, ".//input[@type='submit' or @type='image']")
                submit_btn.click()
            print('로그인 시도 완료')
            
            # 로딩 대기
            WebDriverWait(driver, 20).until(
                lambda d: "L-hide-display" in d.find_element(By.ID, "L-gen4").get_attribute("class")
            )
            print('로딩 완료')
            
            # OPEN 탭 클릭
            print("우측 'OPEN' 탭 클릭 시도...")
            open_tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@id='quickMenu']//img"))
            )
            open_tab.click()
            print("'OPEN' 탭 클릭 완료")
            
            # Global Menu 모달 팝업 및 iframe 확인
            print("iframe 대기 중...")
            time.sleep(3) # iframe 로딩 대기
            
            # iframe 찾기 (iframe 태그가 하나만 있다고 가정하거나, src로 찾기)
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"발견된 iframe 개수: {len(iframes)}")
            
            for i, iframe in enumerate(iframes):
                print(f"--- iframe {i} 분석 ---")
                try:
                    # iframe으로 전환
                    driver.switch_to.frame(iframe)
                    print("iframe 전환 성공")
                    
                    # 소스 저장
                    with open(f"debug_modal_iframe_{i}.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    print(f"iframe {i} 소스 저장 완료: debug_modal_iframe_{i}.html")
                    
                    # 다시 메인 컨텐츠로 복귀
                    driver.switch_to.default_content()
                except Exception as e:
                    print(f"iframe {i} 접근 실패: {e}")
                    driver.switch_to.default_content()

            
        except Exception as e:
            print('오류 발생:', e)

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
