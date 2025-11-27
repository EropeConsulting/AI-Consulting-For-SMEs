import time
import re
import pandas as pd
from bs4 import BeautifulSoup

# Selenium 4.x 버전 기준
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scrape_smes_counseling_list(max_pages=2, sleep_sec=2):
    """
    첨부된 HTML 구조:
    <div class="list_table">
        <table>
            <caption>상담사례의 번호, 분야, 제목, 작성일, 조회 정보를 제공...</caption>
            <colgroup>...</colgroup>
            <thead>...</thead>
            <tbody>
                <tr>...</tr> <!-- 데이터 행 -->
                ...
            </tbody>
        </table>
    </div>

    위 구조를 참고하여, 목록만 수집하는 예시 코드 (상세페이지 수집은 추가 작업 필요).

    :param max_pages: 몇 페이지까지 크롤링할지 (테스트용으로 2)
    :param sleep_sec: 페이지 이동 후 기다리는 시간
    :return: pandas.DataFrame
    """

    # 1) 크롬 옵션 (화면 없이 실행)
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # 크롬 109+ 에서는 --headless=new 권장
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 2) 웹드라이버 실행
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)

    collected_data = []

    # 상담사례 목록 페이지(예시)
    list_url = "https://www.smes.go.kr/bizlink/counselingCase/counselingCaseList.do"

    try:
        for page_num in range(1, max_pages + 1):
            print(f"=== {page_num} 페이지 처리 중 ===")

            # (A) 페이지 이동
            driver.get(f"{list_url}?pageIndex={page_num}")
            time.sleep(sleep_sec)  # 페이지 로딩 대기

            # (B) <div class="list_table">가 로딩될 때까지 대기
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.list_table table"))
                )
            except:
                print("[안내] 5초 내에 .list_table table을 찾지 못했습니다.")
                continue

            # (C) 목록 HTML 파싱
            html_list = driver.page_source
            soup = BeautifulSoup(html_list, "html.parser")

            # (C-1) div.list_table 안의 <table> 찾기
            list_table_div = soup.find("div", {"class": "list_table"})
            if not list_table_div:
                print("[안내] .list_table 요소를 찾지 못했습니다.")
                continue

            table = list_table_div.find("table")
            if not table:
                print("[안내] table 태그를 찾지 못했습니다.")
                continue

            # (C-2) tbody -> tr -> td
            tbody = table.find("tbody")
            if not tbody:
                print("[안내] tbody 없음.")
                continue

            rows = tbody.find_all("tr")
            if not rows:
                print("[안내] tr(행)이 없습니다.")
                continue

            for row in rows:
                cols = row.find_all("td")
                # 실제로는 [번호, 분야, 제목, 작성일, 조회수] 등이 있을 가능성
                # 예) len(cols) == 5
                if len(cols) < 5:
                    continue  # 원하는 만큼 칼럼이 없는 경우 스킵

                # 예시 컬럼:
                #   [0] = 번호
                #   [1] = 분야
                #   [2] = 제목
                #   [3] = 작성일
                #   [4] = 조회수
                case_number = cols[0].get_text(strip=True)
                domain = cols[1].get_text(strip=True)
                title = cols[2].get_text(strip=True)
                written_date = cols[3].get_text(strip=True)
                views = cols[4].get_text(strip=True)

                # 추가로, 상세페이지 이동용 a 태그(onclick or href)가 있을 수 있음:
                # detail_a = cols[2].find("a")
                # if detail_a:
                #     ... 자세한 seq 추출 ...

                collected_data.append({
                    "번호": case_number,
                    "분야": domain,
                    "제목": title,
                    "작성일": written_date,
                    "조회수": views
                })

    finally:
        driver.quit()

    # (D) DataFrame 변환
    df = pd.DataFrame(collected_data)
    return df


if __name__ == "__main__":
    result_df = scrape_smes_counseling_list(max_pages=2, sleep_sec=2)
    print(result_df.head())
    result_df.to_csv("smes_counseling_list.csv", encoding="utf-8-sig", index=False)
    print("목록 크롤링 완료")
