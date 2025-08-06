from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
import time
import csv
import os

print("🟢 Script başladı!")

league_urls = [
    {"name": "La Liga", "url": "https://www.sofascore.com/tournament/football/spain/laliga/8"},
    {"name": "Premier League", "url": "https://www.sofascore.com/tournament/football/england/premier-league/17"},
    {"name": "Bundesliga", "url": "https://www.sofascore.com/tournament/football/germany/bundesliga/35"},
    {"name": "Serie A", "url": "https://www.sofascore.com/tournament/football/italy/serie-a/23"},
    {"name": "Ligue 1", "url": "https://www.sofascore.com/tournament/football/france/ligue-1/34"}
]

def get_teams_from_league(url, driver):
    print(f"🌍 Lig sayfasına gidiliyor: {url}")
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/team/football/"]'))
    )
    time.sleep(3)

    elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/team/football/"]')
    team_links = []
    for elem in elements:
        href = elem.get_attribute("href")
        if "/team/football/" in href and href not in team_links:
            team_links.append(href)

    print(f"📊 {len(team_links)} takım bulundu.")
    return team_links

def get_players_from_team(team_url, driver):
    players = []
    unique_players = set()

    try:
        print(f"⚽ Takım sayfasına gidiliyor: {team_url}")
        driver.get(team_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/main/div[2]/div/div[2]/div[1]/div[1]/div/div[2]/div/div[1]/div[2]/div[1]/h2'))
        )
        time.sleep(3)

        team_name = driver.find_element(By.XPATH, '/html/body/div[1]/main/div[2]/div/div[2]/div[1]/div[1]/div/div[2]/div/div[1]/div[2]/div[1]/h2').text

        squad_box = driver.find_element(By.XPATH, '/html/body/div[1]/main/div[2]/div/div[2]/div[1]/div[5]/div/div[3]')
        player_elements = squad_box.find_elements(By.CSS_SELECTOR, 'a[href*="/player/"]')

        players_in_team = []
        for elem in player_elements:
            name = elem.text
            url = elem.get_attribute("href")
            if name.strip() and url:
                players_in_team.append({"name": name, "url": url})

        print(f"🔵 {team_name} | 👕 {len(players_in_team)} oyuncu bulundu")

        for player in players_in_team:
            unique_key = player["url"].lower()
            if unique_key in unique_players:
                continue

            try:
                driver.get(player["url"])

                # Yaş
                try:
                    WebDriverWait(driver, 7).until(
                        EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/main/div[2]/div/div[2]/div[1]/div[2]/div/div[1]/div[2]/div[2]/div[2]'))
                    )
                    age = driver.find_element(By.XPATH, '/html/body/div[1]/main/div[2]/div/div[2]/div[1]/div[2]/div/div[1]/div[2]/div[2]/div[2]').text
                except:
                    age = ''

                # Özellikler
                try:
                    attack = driver.find_element(By.XPATH, '/html/body/div[1]/main/div[2]/div/div[2]/div[2]/div[1]/div/div[2]/div[1]/div/div[1]/div/div/span').text
                    technique = driver.find_element(By.XPATH, '/html/body/div[1]/main/div[2]/div/div[2]/div[2]/div[1]/div/div[2]/div[1]/div/div[2]/div/div/span').text
                    tactic = driver.find_element(By.XPATH, '/html/body/div[1]/main/div[2]/div/div[2]/div[2]/div[1]/div/div[2]/div[1]/div/div[3]/div/div/span').text
                    defense = driver.find_element(By.XPATH, '/html/body/div[1]/main/div[2]/div/div[2]/div[2]/div[1]/div/div[2]/div[1]/div/div[4]/div/div/span').text
                    creativity = driver.find_element(By.XPATH, '/html/body/div[1]/main/div[2]/div/div[2]/div[2]/div[1]/div/div[2]/div[1]/div/div[5]/div/div/span').text
                except Exception as e:
                    print(f"⚠️ Stat verileri alınamadı: {str(e)}")
                    attack = technique = tactic = defense = creativity = ''

                players.append({
                    "team": team_name,
                    "name": player["name"],
                    "age": age,
                    "att": attack,
                    "cre": creativity,
                    "def": defense,
                    "tac": tactic,
                    "tec": technique
                })
                unique_players.add(unique_key)
                print(f"✅ {player['name']} verileri çekildi")
                time.sleep(1)
            except Exception as e:
                print(f"❌ {player['name']} verileri alınamadı: {str(e)}")
    except Exception as e:
        print(f"‼️ Takım hatası ({team_url}): {str(e)}")

    return players

def main():
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument("--window-size=1280,720")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Servisi tanımla: çalıştığın dizindeki chromedriver.exe'yi kullan
    chrome_path = os.path.join(os.getcwd(), 'chromedriver.exe')
    service = Service(executable_path=chrome_path)

    driver = webdriver.Chrome(service=service, options=options)

    # Stealth entegrasyonu
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            run_on_insecure_origins=False)

    all_players = []

    try:
        for league in league_urls:
            print(f"\n🏆 {league['name']} için işlemler başlıyor...\n")
            team_links = get_teams_from_league(league["url"], driver)
            for team_url in team_links:
                players = get_players_from_team(team_url, driver)
                all_players.extend(players)
    except Exception as e:
        print(f"🚨 Ana hata: {str(e)}")
    finally:
        driver.quit()
        print("🛑 Tarayıcı kapatıldı")

    if all_players:
        with open('tum_ligler_oyuncular.csv', 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Takım", "Oyuncu", "Yaş", "ATTH", "CRE", "DEF", "TAC", "TEC"])
            for p in all_players:
                writer.writerow([p["team"], p["name"], p["age"], p["att"], p["cre"], p["def"], p["tac"], p["tec"]])
        print(f"✅ Toplam {len(all_players)} oyuncu kaydedildi!")
    else:
        print("⚠️ Hiçbir oyuncu verisi alınamadı!")

main()
