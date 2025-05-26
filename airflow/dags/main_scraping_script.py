import re
import os
import time
import json
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def initialize_driver():
    options = Options()
    options.binary_location = "/usr/bin/google-chrome-stable"  # Assure-toi que c'est le bon chemin ici
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--headless")  # Mode headless pour éviter les problèmes graphiques sous WSL
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def random_sleep(min_sleep=2, max_sleep=5):
    time.sleep(random.uniform(min_sleep, max_sleep))

def scroll_to_bottom(driver):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(@class, 'm6QErb DxyBCb kA9KIf') and @aria-label and @tabindex]")
            )
        )
        last_height = driver.execute_script("return arguments[0].scrollHeight", element)
        while True:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", element)
            random_sleep(3, 6)
            new_height = driver.execute_script("return arguments[0].scrollHeight", element)
            if new_height == last_height:
                break
            last_height = new_height
    except Exception as e:
        print(f"Erreur lors du scrolling : {e}")

def collect_agency_links(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return [element.get('href') for element in soup.find_all('a', class_='hfpxzc') if element.get('href')]

def click_all_buttons(driver):
    try:
        buttons = driver.find_elements(By.CLASS_NAME, "w8nwRe")
        for button in buttons:
            try:
                button.click()
                random_sleep(1, 2)
            except Exception:
                continue
    except Exception:
        pass

def extract_agency_data(driver, banque, url):
    all_data = {"Bank_name": banque, "Branches": []}
    print(f"Attempting to access URL: {url}")
    driver.get(url)
    random_sleep(5, 7)
    scroll_to_bottom(driver)
    agencies_links = collect_agency_links(driver)
    print(agencies_links)
    for index, link in enumerate(agencies_links):
        print(link)
        try:
            driver.get(link)
            time.sleep(5)
            try:
                agence_info = driver.find_element(By.CLASS_NAME, "tAiQdd")
                nom_agence = agence_info.find_element(By.CSS_SELECTOR, "h1.DUwDvf.lfPIob").text
                adresse = driver.find_element(By.CLASS_NAME, "CsEnBe").get_attribute("aria-label")
            except Exception:
                continue
            reviews = []
            try:
                avis_button = driver.find_elements(By.CLASS_NAME, "hh2c6")[1]
                avis_button.click()
                time.sleep(5)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "aIFcqe"))
                )
                review_container = driver.find_element(By.CLASS_NAME, "m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde")
                last_count = 0
                while True:
                    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", review_container)
                    time.sleep(2)
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    new_count = len(soup.find_all('div', class_="jftiEf fontBodyMedium"))
                    if new_count == last_count:
                        break
                    last_count = new_count
                click_all_buttons(driver)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                reviews_elements = soup.find_all('div', class_="jftiEf fontBodyMedium")
                print(len(reviews_elements))
                for review in reviews_elements:
                    try:
                        reviews.append({
                            "review_text": review.find(class_="wiI7pd").text if review.find(class_="wiI7pd") else None,
                            "review_rating": review.find(class_="kvMYJc")["aria-label"] if review.find(class_="kvMYJc") else None,
                            "review_date": review.find(class_="rsqaWe").text if review.find(class_="rsqaWe") else None,
                        })
                    except Exception:
                        continue
            except Exception:
                pass
            all_data["Branches"].append({
                "branch_name": nom_agence,
                "location": adresse,
                "reviews": reviews
            })
        except Exception:
            continue
        break
    return all_data

def extract_data(driver, banques):
    all_banks_data = []
    for banque in banques:
        cleaned_banque = re.sub(r'[^a-zA-Z0-9\s]', '', banque.lower()).replace(' ', '+')
        url = f"https://www.google.com/maps/search/{cleaned_banque}+morocco"
        bank_data = extract_agency_data(driver, banque, url)
        all_banks_data.append(bank_data)
    return all_banks_data

def main():
    driver = initialize_driver()
    # URL de recherche des agences au Maroc
    banques = [
        "Attijariwafa Bank",
        "Banque Centrale Populaire (BCP)",
        "Bank of Africa (BOA)",
        "Banque Marocaine pour le Commerce et l'Industrie (BMCI)",
        "Crédit Agricole du Maroc (CAM)",
        "Crédit du Maroc",
        "Société Générale Maroc",
        "CIH Bank",
        "Al Barid Bank",
        "Arab Bank Maroc",
        "CFG Bank",
        "Citibank",
        "Bank Assafa",
        "Al Akhdar Bank (AAB)",
        "Bank Al Yousr",
        "Bank Al-Tamweel wa Al-Inma",
        "Bank As-Safa",
        "Umnia Bank"
    ]
    try:
        all_data = extract_data(driver, banques)
        output_path = os.path.expanduser("~/input/data_of_json_google_map/moroccan_banks_reviews.json")
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(all_data, json_file, ensure_ascii=False, indent=4)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()