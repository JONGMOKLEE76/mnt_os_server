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
            
            # 페이지 소스 저장
            time.sleep(3) # 확실한 로딩을 위해 추가 대기
            with open("debug_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("페이지 소스가 'debug_source.html'로 저장되었습니다.")
            
        except Exception as e:
            print('로그인/로딩 중 오류:', e)

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
