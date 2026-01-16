import time
import os
import glob
import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import sqlite3

# 다운로드 디렉토리 설정
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# Chrome WebDriver 경로 (driver 폴더 내의 chromedriver.exe 사용)
CHROME_DRIVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chromedriver.exe')

def get_weekname(date):
    """
    특정 datetime 날짜를 입력받아서 해당 날짜에 해당하는 isocalendar 기준의 week name을 text로 생성하는 함수
    """
    if pd.isna(date):
        return None
    firstdayofweek = date - datetime.timedelta(days = date.isocalendar()[2] - 1)
    return f"{firstdayofweek.year}-{firstdayofweek.month:02d}-{firstdayofweek.day:02d}(W{date.isocalendar()[1]:02d})"

def get_month_from_date(date):
    """
    datetime 날짜를 입력받아서 해당 날짜에 해당하는 월(month) 값을 돌려주는 함수
    """
    if pd.isna(date):
        return None
    month_list = []
    for i in range(7):
        month_list.append((date - datetime.timedelta(days=date.isocalendar()[2]-1-i)).month)
    month_list = pd.Series(month_list)
    max_value = month_list.value_counts().max()
    for i in month_list.value_counts().index:
        if month_list.value_counts().loc[i] == max_value:
            return i
    return None

def wait_for_new_file(download_dir, initial_files, timeout=60):
    """
    새로운 파일이 다운로드 완료될 때까지 대기하는 함수
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        current_files = set(os.listdir(download_dir))
        new_files = current_files - initial_files
        
        # .crdownload (크롬 임시 파일) 제외하고 실제 파일이 생겼는지 확인
        finished_files = [f for f in new_files if not f.endswith('.crdownload') and (f.endswith('.xls') or f.endswith('.xlsx'))]
        
        if finished_files:
            # 파일이 완전히 써질 때까지 아주 잠깐 대기
            time.sleep(1)
            return os.path.join(download_dir, finished_files[0])
            
        time.sleep(1)
    return None

def save_to_db(file_path, site_name, data_source, skip_model_filter=False):
    """
    다운로드된 엑셀 파일을 읽어 DB(SQLite)에 저장하는 함수.
    엑셀에 포함된 PO 번호들에 대해서만 기존 데이터를 삭제하고 새로 입력하여
    분할 선적을 처리하고 과거 데이터(3개월 이전)를 보존합니다.
    """
    # 루트 폴더의 통합 DB (mnt_data.db) 사용
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mnt_data.db")
    try:
        if not file_path or not os.path.exists(file_path):
            print(f"파일을 찾을 수 없습니다: {file_path}")
            return

        print(f"DB 저장 중: {os.path.basename(file_path)} (Site: {site_name})")
        
        df = None
        # 1. 엑셀 읽기 (HTML 형식 포함 처리)
        try:
            if file_path.lower().endswith('.xls'):
                try:
                    df = pd.read_excel(file_path, engine='xlrd')
                except:
                    tables = pd.read_html(file_path)
                    if tables:
                        df = tables[0]
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            print(f"엑셀 읽기 실패: {e}")
            return

        if df is not None:
            # 'Unnamed:' 으로 시작하는 불필요한 컬럼 제거
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # 'From Site' 컬럼 추가
            df['From Site'] = site_name
            
            # 'Data Source' 컬럼 추가 (NERP/GERP)
            df['Data Source'] = data_source

            # --- [추가] 특수 Ship To 매핑 (TCL MOKA / Monitor, GERP) ---
            if site_name == 'TCL MOKA / Monitor' and data_source == 'GERP' and 'Ship To' in df.columns:
                original_value = 'ООО "РК Дистрибьюшен"'
                replacement_value = 'ERRA_MINSK_DO'
                mask = df['Ship To'] == original_value
                if mask.any():
                    df.loc[mask, 'Ship To'] = replacement_value
                    print(f"[알림] Ship To '{original_value}' → '{replacement_value}' 로 {mask.sum()}건 변환 완료")

            # --- [추가] 모델 필터링 로직 (PC 업체는 스킵) ---
            if not skip_model_filter:
                try:
                    # DB에서 os_models 조회
                    with sqlite3.connect(db_path) as tmp_conn:
                        os_models_df = pd.read_sql("SELECT Series FROM os_models", tmp_conn)
                    
                    valid_series = set(os_models_df['Series'].dropna().unique())

                    if 'Model' in df.columns:
                        # 모델명에서 Series 추출 (예: 27GQ50F-B.AUS -> 27GQ50F)
                        # 사용자 요청 로직: x.split('-')[0].split('.')[0]
                        temp_series = df['Model'].astype(str).apply(lambda x: x.split('-')[0].split('.')[0])

                        # 제외될 모델 식별
                        excluded_mask = ~temp_series.isin(valid_series)
                        excluded_models = df.loc[excluded_mask, 'Model'].apply(lambda x: x.split('-')[0].split('.')[0]).unique()

                        if len(excluded_models) > 0:
                            print(f"\n[알림] 다음 {len(excluded_models)}개 모델은 os_models에 없어 제외되었습니다:")
                            for m in excluded_models:
                                print(f"- {m}")

                        # 필터링 적용
                        original_count = len(df)
                        df = df[~excluded_mask].copy()
                        print(f"모델 필터링 완료: {original_count} -> {len(df)} 행")

                except Exception as e:
                    print(f"모델 필터링 중 오류 발생: {e}")
            else:
                print(f"[알림] PC 업체 - 모델 필터링 스킵 ({len(df)} 행)")
            
            # --- [추가] 날짜 변환 및 데이터 보강 로직 ---
            
            # 1. RSD 기준 Week 컬럼 업데이트
            if 'RSD' in df.columns:
                df['RSD'] = pd.to_datetime(df['RSD'], errors='coerce')
                df['Week'] = df['RSD'].apply(get_weekname)
            
            # 2. Ship Date 기준 Week Name 및 Month 생성
            if 'Ship Date' in df.columns:
                df['Ship Date'] = pd.to_datetime(df['Ship Date'], errors='coerce')
                df['Week Name'] = df['Ship Date'].apply(get_weekname)
                
                # Month 생성 (yyyy-mm 형식)
                def calculate_month(week_name):
                    if not week_name: return None
                    try:
                        dt = datetime.date.fromisoformat(week_name[:10])
                        iso_year = dt.isocalendar().year
                        month = get_month_from_date(dt)
                        return f"{iso_year}-{month:02d}"
                    except:
                        return None
                
                df['Month'] = df['Week Name'].apply(calculate_month)

            # 3. Site Mapping (Region, Country) 추가 및 검증
            conn = sqlite3.connect(db_path)
            try:
                mapping_df = pd.read_sql("SELECT * FROM site_mapping", conn)
                
                if 'Ship To' in df.columns:
                    # 매핑되지 않는 Ship To 확인
                    excel_ship_tos = set(df['Ship To'].dropna().unique())
                    mapped_tos = set(mapping_df['to_site'].unique())
                    missing_tos = excel_ship_tos - mapped_tos
                    
                    if missing_tos:
                        print(f"\n[알림] 다음 Ship To에 대한 Region/Country 정보가 site_mapping 테이블에 없습니다 (NULL로 저장됨):")
                        for ship_to in missing_tos:
                            print(f"- {ship_to}")
                        # return 제거: 매핑 정보가 없어도 진행 (Left Join으로 인해 NULL로 들어감)
                    
                    # Join 수행
                    df = df.merge(mapping_df[['to_site', 'region', 'country']], 
                                 left_on='Ship To', right_on='to_site', how='left')
                    
                    # 컬럼명 정리 (필요시)
                    df = df.rename(columns={'region': 'Region', 'country': 'Country'})
                    if 'to_site' in df.columns:
                        df = df.drop(columns=['to_site'])

                # --- [기존 로직 계속] ---
                
                cursor = conn.cursor()
                # 2. 테이블 존재 여부 확인 및 컬럼 동기화
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shipment_data'")
                table_exists = cursor.fetchone()
                
                if table_exists:
                    # 기존 컬럼 확인
                    cursor.execute("PRAGMA table_info(shipment_data)")
                    existing_cols = [info[1] for info in cursor.fetchall()]
                    
                    # 새 컬럼이 있으면 추가 (Schema Evolution)
                    for col in df.columns:
                        if col not in existing_cols:
                            try:
                                cursor.execute(f"ALTER TABLE shipment_data ADD COLUMN `{col}` TEXT")
                                print(f"새 컬럼 추가됨: {col}")
                            except Exception as e:
                                print(f"컬럼 추가 중 오류 (무시 가능): {e}")

                    # 3. 이번 엑셀에 포함된 PO 번호 리스트 추출
                    if 'PO No.' in df.columns:
                        po_list = df['PO No.'].dropna().unique().tolist()
                        
                        if po_list:
                            # 해당 업체(From Site)이면서 이번 엑셀에 포함된 PO들만 삭제
                            placeholders = ', '.join(['?'] * len(po_list))
                            query = f"DELETE FROM shipment_data WHERE `From Site` = ? AND `PO No.` IN ({placeholders})"
                            cursor.execute(query, [site_name] + po_list)
                            print(f"기존 [{site_name}]의 {len(po_list)}개 PO 관련 데이터 삭제 완료 (Selective Refresh)")
                
                # 4. 새로운 데이터 삽입
                df.to_sql('shipment_data', conn, if_exists='append', index=False)
                conn.commit()
                print(f"DB 저장 완료: {len(df)} 행 삽입됨")
                
                # 5. 임시 파일 삭제
                try:
                    os.remove(file_path)
                    print(f"임시 파일 삭제 완료: {file_path}")
                except:
                    pass
            finally:
                conn.close()
                
    except Exception as e:
        print(f"DB 저장 중 오류 발생: {e}")

def download_excel_for_companies(driver, target_companies, skip_model_filter=False):
    """
    지정된 업체 목록에 대해 업체 선택, 메뉴 이동 및 엑셀 다운로드를 수행하는 함수
    """

    for company_name in target_companies:
        print(f"\n--- [{company_name}] 처리 시작 ---")
        
        # 커스텀 드롭다운 UI에서 업체 선택
        try:
            trigger_elem = driver.find_element(By.XPATH, "//select[@id='gnbUserCompany']/preceding-sibling::*[1] | //select[@id='gnblserCompany']/following-sibling::*[1]")
            trigger_elem.click()
            time.sleep(1)
            
            # 업체명으로 요소 찾기
            company_xpath = f"//div[@id='gnbUserCompany_DIALOG']//span[text()='{company_name}']"
            company_elem = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, company_xpath))
            )
            company_elem.click()
            print(f'업체 선택 완료: {company_name}')
            
            # 업체 선택 후에도 spin 요소가 사라질 때까지 대기
            try:
                WebDriverWait(driver, 20).until(
                    lambda d: "L-hide-display" in d.find_element(By.ID, "L-gen4").get_attribute("class")
                )
                print('업체 선택 후 로딩 완료')
            except Exception as e:
                print('업체 선택 후 로딩 대기 중 오류:', e)
        except Exception as e:
            print(f'업체 선택 중 오류 ({company_name}):', e)
            continue # 다음 업체로 진행

        # 메뉴 목록 정의 (NERP 및 GERP)
        menus = [
            {'text': 'Shipping & Invoicing (NERP)', 'source': 'NERP', 'type': 'text'},
            {'text': 'Shipping & Invoicing', 'source': 'GERP', 'type': 'href', 'keyword': 'SR00301'}
        ]

        for menu in menus:
            menu_text = menu['text']
            source_name = menu['source']
            print(f"  >> 메뉴 처리 시작: {menu_text} (Source: {source_name})")

            # Shipping & Invoicing 상단 메뉴에 마우스 오버 및 하위 메뉴 클릭
            try:
                menu_li = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "mNavi_2"))
                )
                ActionChains(driver).move_to_element(menu_li).perform()
                print('상단 Shipping & Invoicing 메뉴에 마우스 오버 완료')
                time.sleep(1)
                
                # 메뉴 찾기 (Text 또는 Href)
                if menu['type'] == 'href':
                    # GERP: href 속성에 'SR00301'이 포함된 요소 찾기
                    xpath = f"//a[contains(@href, '{menu['keyword']}')]"
                else:
                    # NERP: 텍스트 정확히 일치하는 메뉴 찾기
                    xpath = f"//a[normalize-space(text())='{menu_text}']"

                submenu = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                submenu.click()
                print(f'하위 {menu_text} 메뉴 클릭 완료')
                
                # 하위 메뉴 클릭 후 spin 요소가 사라질 때까지 대기
                try:
                    # L-gen7 (로딩 패널)이 숨겨질 때까지 대기 (class에 L-hide-display 포함 여부 확인)
                    WebDriverWait(driver, 30).until(
                        lambda d: "L-hide-display" in d.find_element(By.ID, "L-gen7").get_attribute("class")
                    )
                    print('하위 메뉴 이동 후 로딩 완료 (L-gen7 확인)')
                    
                    # spin 사라진 후 엑셀 다운로드 버튼 클릭
                    try:
                        excel_btn = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, "informationExcelDownloadIod"))
                        )
                        
                        # 팝업(alert/confirm)을 무시하고 자동으로 수락하도록 JS 주입
                        driver.execute_script("window.confirm = function(msg){ return true; };")
                        driver.execute_script("window.alert = function(msg){ return true; };")
                        # print("JS Alert/Confirm Override 적용 완료")

                        # 다운로드 클릭 전 파일 목록 캡처
                        initial_files = set(os.listdir(DOWNLOAD_DIR))

                        # [수정] L-gen7 (로딩 패널)이 숨겨질 때까지 대기 (class에 L-hide-display 포함 여부 확인)
                        try:
                            WebDriverWait(driver, 20).until(
                                lambda d: "L-hide-display" in d.find_element(By.ID, "L-gen7").get_attribute("class")
                            )
                            print('로딩 마스크(L-gen7) 해제 확인 완료')
                        except Exception as e:
                            print(f'로딩 대기 중 타임아웃 또는 오류: {e}')
                            pass

                        excel_btn.click()
                        print('엑셀 다운로드 버튼 클릭 완료')

                        # Native Alert 시도 (안전장치)
                        try:
                            WebDriverWait(driver, 3).until(EC.alert_is_present())
                            alert = driver.switch_to.alert
                            alert.accept()
                            print('Native Alert 수락 완료')
                        except:
                            pass
                        
                        # 파일 다운로드 대기 및 업데이트
                        print(f"파일 다운로드 대기 중 (Max 60s)...")
                        new_file = wait_for_new_file(DOWNLOAD_DIR, initial_files)
                        if new_file:
                            print(f"새 파일 감지됨: {new_file}")
                            save_to_db(new_file, company_name, source_name, skip_model_filter)
                        else:
                            print("다운로드된 새 파일을 찾지 못했습니다.")
                            
                    except Exception as e:
                        print('엑셀 다운로드 버튼 클릭 중 오류:', e)

                except Exception as e:
                    print('하위 메뉴 이동 후 로딩 대기 중 오류:', e)
            except Exception as e:
                print(f'메뉴 자동화 중 오류 ({menu_text}):', e)
            
            time.sleep(1) # 메뉴 간 잠시 대기
        
        print(f"--- [{company_name}] 처리 완료 ---\n")
        time.sleep(2)

def main():
    # ========== 사용자 설정 영역 ==========
    product_category = 'pc'  # 'monitor' 또는 'pc'
    supplier_category = 'LGEKR'   # 'LGEKR' 또는 'LGECH'
    # =====================================

    # 업체 목록 정의
    COMPANIES = {
        'LGEKR': {
            'monitor': ['AU OPTRONICS / Monitor', 'BOEVT / MONITOR', 'TCL MOKA / Monitor', 'TCL TTE / Monitor', 'TPV / MNT'],
            'pc': ['PEGATRON / PC', 'QUANTA / PC', 'WANLIDA / PC']
        },
        'LGECH': {
            'monitor': ['GAO CHUANG / Monitor', 'KTC / Commercial Display', 'MO JIA / Monitor'],
            'pc': []  # 현재 LGECH에 PC 업체 없음
        }
    }

    chrome_options = Options()
    # chrome_options.add_argument('--headless')
    
    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()

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
            
            WebDriverWait(driver, 20).until(
                lambda d: "L-hide-display" in d.find_element(By.ID, "L-gen4").get_attribute("class")
            )
            print('로딩 완료, 메뉴 선택 가능')
            print(f"\n[설정] Product: {product_category}, Supplier: {supplier_category}")

            # LGEKR 업체 처리 (LGEKR 선택 시)
            if supplier_category == 'LGEKR':
                target_companies_kr = COMPANIES['LGEKR'].get(product_category, [])
                if target_companies_kr:
                    print(f"\n>>> LGEKR 관할 {product_category.upper()} 업체 처리 시작 <<<")
                    download_excel_for_companies(driver, target_companies_kr, skip_model_filter=(product_category == 'pc'))
                else:
                    print(f"\n[알림] LGEKR에 {product_category} 업체가 없습니다.")

            # LGECH 업체 처리 (LGECH 선택 시)
            elif supplier_category == 'LGECH':
                # 먼저 LGECH로 법인 전환
                try:
                    print("\n>>> 법인 전환 시도 (LGEKR -> LGECH) <<<")
                    open_tab = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@id='quickMenu']//img"))
                    )
                    open_tab.click()
                    print("'OPEN' 탭 클릭 완료")
                    
                    # iframe 전환
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    target_iframe = None
                    for frame in iframes:
                        try:
                            if "goGlobalMap.glop" in frame.get_attribute("src"):
                                target_iframe = frame
                                break
                        except: continue
                    
                    if target_iframe:
                        driver.switch_to.frame(target_iframe)
                    else:
                        WebDriverWait(driver, 15).until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))
                    print("iframe 전환 성공")
                    time.sleep(2)

                    # LGEKR 클릭 (그리드 숨기기)
                    try:
                        lgekr_span = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "LGEKR")))
                        driver.execute_script("arguments[0].click();", lgekr_span.find_element(By.TAG_NAME, "a"))
                        print("'LGEKR' 그리드 숨기기 완료")
                    except: pass
                    time.sleep(1)

                    # LGECH 클릭
                    lgech_span = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "LGECH")))
                    driver.execute_script("arguments[0].click();", lgech_span.find_element(By.TAG_NAME, "a"))
                    print("'LGECH' 선택 완료")
                    time.sleep(3)

                    # GAO CHUANG (GMZ) 선택 (LGECH 첫 업체)
                    supplier_element = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'GAO CHUANG (GMZ)')]"))
                    )
                    driver.execute_script("arguments[0].click();", supplier_element)
                    print("'GAO CHUANG (GMZ)' 업체 선택 완료")
                    time.sleep(2)

                    driver.switch_to.default_content()
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    print("모달 닫기 완료")
                    
                    # 법인 전환 후 로딩 대기
                    WebDriverWait(driver, 20).until(
                        lambda d: "L-hide-display" in d.find_element(By.ID, "L-gen4").get_attribute("class")
                    )
                    print("법인 전환 후 로딩 완료")

                except Exception as e_switch:
                    print(f"법인 전환 실패: {e_switch}")
                    raise e_switch

                # LGECH 업체 처리
                target_companies_ch = COMPANIES['LGECH'].get(product_category, [])
                if target_companies_ch:
                    print(f"\n>>> LGECH 관할 {product_category.upper()} 업체 처리 시작 <<<")
                    download_excel_for_companies(driver, target_companies_ch, skip_model_filter=(product_category == 'pc'))
                else:
                    print(f"\n[알림] LGECH에 {product_category} 업체가 없습니다.")

                # 최종 원복 (LGECH -> LGEKR) 및 AU OPTRONICS (GMZ) 선택
                try:
                    print("\n>>> 최종 원복 시도 (LGECH -> LGEKR) <<<")
                    open_tab = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@id='quickMenu']//img"))
                    )
                    open_tab.click()
                    print("'OPEN' 탭 클릭 완료")
                    
                    # iframe 전환
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    target_iframe = None
                    for frame in iframes:
                        try:
                            if "goGlobalMap.glop" in frame.get_attribute("src"):
                                target_iframe = frame
                                break
                        except: continue
                    
                    if target_iframe:
                        driver.switch_to.frame(target_iframe)
                    else:
                        WebDriverWait(driver, 15).until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))
                    print("iframe 전환 성공")
                    time.sleep(2)

                    # LGEKR 클릭
                    lgekr_span = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "LGEKR")))
                    driver.execute_script("arguments[0].click();", lgekr_span.find_element(By.TAG_NAME, "a"))
                    print("'LGEKR' 선택 완료")
                    time.sleep(3)

                    # AU OPTRONICS (GMZ) 선택
                    supplier_element = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'AU OPTRONICS (GMZ)')]"))
                    )
                    driver.execute_script("arguments[0].click();", supplier_element)
                    print("'AU OPTRONICS (GMZ)' 업체 선택 완료")
                    time.sleep(2)

                    driver.switch_to.default_content()
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    print("모달 닫기 완료 및 최종 원복 성공")

                except Exception as e_revert:
                    print(f"최종 원복 실패: {e_revert}")

        except Exception as e:
            print('자동화 프로세스 중 오류:', e)

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
