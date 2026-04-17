import logging
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def search_by_id(driver: WebDriver, target_id: str, config: dict, logger: logging.Logger) -> str:
    """
    検索欄にIDを入力して結果を取得する。
    1分以内に結果が見つかればその内容を返す。
    見つからなければ config で指定した not_found_text を返す。
    """
    timeout_result = config["timeout"]["result_wait"]
    not_found_text = config["csv"]["not_found_text"]
    sel = config["selectors"]

    wait = WebDriverWait(driver, timeout_result)

    try:
        # 検索入力欄が操作可能になるまで待機
        search_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, sel["search"]["input_field"]))
        )
        search_input.clear()
        search_input.send_keys(target_id)
        logger.debug(f"ID={target_id} を検索欄に入力しました")

        # 検索ボタンをクリック
        search_btn = driver.find_element(By.CSS_SELECTOR, sel["search"]["submit_button"])
        search_btn.click()

        # 結果エリアが表示されるまで待機（最大 result_wait 秒）
        result_area = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, sel["search"]["result_area"]))
        )
        result_text = result_area.text.strip()
        logger.info(f"ID={target_id} → 結果取得: {result_text[:50]}")
        return result_text

    except TimeoutException:
        # タイムアウト：結果が見つからなかった
        logger.warning(f"ID={target_id} → タイムアウト（{timeout_result}秒以内に結果なし）")
        return not_found_text
