import os
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def login(driver, config: dict, logger: logging.Logger) -> None:
    """ログインページにアクセスしてログインを実行する"""
    login_url = os.getenv("LOGIN_URL")
    login_id = os.getenv("LOGIN_ID")
    login_password = os.getenv("LOGIN_PASSWORD")

    timeout = config["timeout"]["page_load"]
    sel = config["selectors"]["login"]

    logger.info(f"ログインページを開きます: {login_url}")
    driver.get(login_url)

    wait = WebDriverWait(driver, timeout)

    # ID入力
    id_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel["id_field"])))
    id_field.clear()
    id_field.send_keys(login_id)

    # パスワード入力
    password_field = driver.find_element(By.CSS_SELECTOR, sel["password_field"])
    password_field.clear()
    password_field.send_keys(login_password)

    # ログインボタンクリック
    submit_button = driver.find_element(By.CSS_SELECTOR, sel["submit_button"])
    submit_button.click()

    # ページ遷移の完了を待機
    wait.until(EC.staleness_of(submit_button))
    logger.info("ログイン成功")


def click_menu(driver, config: dict, logger: logging.Logger) -> None:
    """ログイン後のメニューをクリックして対象ページへ遷移する"""
    timeout = config["timeout"]["page_load"]
    menu_selector = config["selectors"]["menu"]["target_link"]

    wait = WebDriverWait(driver, timeout)

    # メニューリンクが表示されるまで待機してクリック
    menu_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, menu_selector)))
    menu_link.click()
    logger.info("メニュークリック完了")
