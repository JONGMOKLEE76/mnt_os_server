# GLOP Driver Selenium Automation

이 프로젝트는 Python과 Selenium을 사용하여 https://glopp.lge.com/index.jsp 사이트에 접속하고, 웹 브라우저를 자동으로 제어하는 예제입니다.

## 준비 사항
1. Python 3.x 설치
2. [Chrome WebDriver](https://sites.google.com/chromium.org/driver/) 다운로드 및 압축 해제
   - Chrome 브라우저 버전에 맞는 드라이버를 받으세요.
   - 예시: `C:/chromedriver/chromedriver.exe` 경로에 위치시킴
3. 프로젝트 디렉터리에서 아래 명령어로 selenium 설치

```
pip install -r requirements.txt
```

## 사용법
1. `main.py` 파일에서 `CHROME_DRIVER_PATH`를 본인 환경에 맞게 수정
2. 아래 명령어로 실행

```
python main.py
```

## 주요 코드 설명
- `main.py`는 사이트 접속, 요소 탐색, 브라우저 제어의 기본 예시를 포함합니다.
- 추가적인 자동화 작업은 `main.py`에 코드를 추가하여 구현할 수 있습니다.

---
문의 사항이 있으면 언제든 말씀해 주세요.
