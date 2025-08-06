import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from fake_useragent import UserAgent
from datetime import datetime
import os
from selenium.common.exceptions import TimeoutException

# ==== Ayarlar ====
CHROMEDRIVER_PATH = os.path.join(os.getcwd(), 'chromedriver.exe')
ua = UserAgent()
user_agent = ua.random

options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={user_agent}")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

service = Service(executable_path=CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True)



leagues = [
    {"name": "Premier League", "url": "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"},
    {"name": "La Liga", "url": "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures"},
    {"name": "Bundesliga", "url": "https://fbref.com/en/comps/20/schedule/Bundesliga-Scores-and-Fixtures"},
    {"name": "Serie A", "url": "https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures"},
    {"name": "Ligue 1", "url": "https://fbref.com/en/comps/13/schedule/Ligue-1-Scores-and-Fixtures"},

]

all_player_data = []
final_columns = [
    "league", "match_date", "team", "location", "opponent", "score",
    "xg_team", "xg_opponent", "player", "shirtnumber", "nationality", "position", "age", "minutes",
    "goals", "assists", "pens_made", "pens_att", "shots", "shots_on_target",
    "cards_yellow", "cards_red", "touches", "tackles", "interceptions", "blocks",
    "xg", "npxg", "xg_assist", "sca", "gca", "passes_completed", "passes", "passes_pct",
    "progressive_passes", "carries", "progressive_carries", "take_ons", "take_ons_won"
]

for league in leagues:
    print(f"\n📄 {league['name']} fikstür sayfası açılıyor...")
    driver.get(league["url"])

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'sched_')]"))
    )

    try:
        accept_cookies = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'AGREE')]"))
        )
        accept_cookies.click()
        print("🍪 Çerezler kabul edildi")
    except:
        pass


    match_links = []
    try:
        table = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'sched_')]"))
        )
        rows = table.find_elements(By.XPATH, ".//tbody/tr[not(contains(@class, 'thead'))]")

        for row in rows:
            try:
                date_cell = row.find_element(By.XPATH, ".//td[@data-stat='date']")
                date_str = date_cell.get_attribute("csk") or date_cell.text.strip()
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                except:
                    try:
                        date_obj = datetime.strptime(date_str, "%Y%m%d")
                    except:
                        continue

                if not (datetime(2024, 7, 1) <= date_obj <= datetime(2025, 6, 30)):
                    continue

                home_team = row.find_element(By.XPATH, ".//td[@data-stat='home_team']//a").text.strip()
                away_team = row.find_element(By.XPATH, ".//td[@data-stat='away_team']//a").text.strip()
                try:
                    score = row.find_element(By.XPATH, ".//td[@data-stat='score']//a").text.strip()
                    if score in ["", "-"]:
                        continue
                    home_goals, away_goals = score.split("–") if "–" in score else score.split("-")
                    formatted_score = f"{home_goals.strip()} - {away_goals.strip()}"
                except:
                    continue

                try:
                    home_xg = row.find_element(By.XPATH, ".//td[@data-stat='home_xg']").text.strip()
                    away_xg = row.find_element(By.XPATH, ".//td[@data-stat='away_xg']").text.strip()
                    home_xg = "0" if home_xg in ["", "-"] else home_xg
                    away_xg = "0" if away_xg in ["", "-"] else away_xg
                except:
                    home_xg = away_xg = "0"

                match_url = row.find_element(By.XPATH, ".//td[@data-stat='match_report']//a").get_attribute("href")

                match_links.append({
                    "url": match_url,
                    "date": date_obj.strftime("%Y-%m-%d"),
                    "home_team": home_team,
                    "away_team": away_team,
                    "score": formatted_score,
                    "home_xg": home_xg,
                    "away_xg": away_xg
                })

            except:
                continue

        print(f"🔍 {len(match_links)} maç linki bulundu")

        # Bundesliga veya Ligue 1 ise son 2 maçı çıkar
        if league["name"] in ["Bundesliga", "Ligue 1"] and len(match_links) > 2:
            match_links = match_links[:-2]
            print(f"✂️ Son 2 maç çıkarıldı → Yeni sayısı: {len(match_links)}")

    except Exception as e:
        print(f"❌ Tablo alınırken hata: {e}")
        continue

    for i, match in enumerate(match_links, 1):
        try:
            print(f"\n➔ {i}/{len(match_links)} - Maç raporu açılıyor: {match['home_team']} vs {match['away_team']}")
            driver.get(match['url'])

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//div[starts-with(@id, 'div_stats_') and contains(@id, '_summary')]//tbody/tr"))
            )

            team_blocks = WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[starts-with(@id, 'div_stats_') and contains(@id, '_summary')]"))
            )
            team_ids = [el.get_attribute("id").replace("div_stats_", "").replace("_summary", "") for el in team_blocks]

            for team_id, team_name, location in zip(team_ids, [match["home_team"], match["away_team"]], ["home", "away"]):
                try:
                    stats_section = driver.find_element(By.ID, f"div_stats_{team_id}_summary")
                    players = stats_section.find_elements(By.XPATH, ".//tbody/tr[not(contains(@class, 'thead'))]")

                    print(f"👥 {len(players)} oyuncu bulundu → {team_name} ({location})")

                    for player in players:
                        row_data = {
                            "league": league["name"],
                            "match_date": match["date"],
                            "team": team_name,
                            "location": location,
                            "opponent": match["away_team"] if location == "home" else match["home_team"],
                            "score": match["score"] if location == "home" else f"{match['score'].split(' - ')[1]} - {match['score'].split(' - ')[0]}",
                            "xg_team": match["home_xg"] if location == "home" else match["away_xg"],
                            "xg_opponent": match["away_xg"] if location == "home" else match["home_xg"]
                        }

                        try:
                            player_name = player.find_element(By.XPATH, ".//th[@data-stat='player']").text.strip()
                        except:
                            continue

                        row_data["player"] = player_name

                        cells = player.find_elements(By.TAG_NAME, "td")
                        for cell in cells:
                            key = cell.get_attribute("data-stat")
                            if not key:
                                continue
                            value = cell.text.strip()
                            if value == "":
                                value = "0.0"

                            # Nationality düzeltmesi: "eng ENG" gibi olanı sadece büyük harf olanla al
                            if key == "nationality":
                                if " " in value:
                                    value = value.split()[-1].upper()
                                else:
                                    value = value.upper()

                            row_data[key] = value

                        # Takım adı düzeltmesi
                        if row_data["team"] == "Nott'ham Forest":
                            row_data["team"] = "Nottingham Forest"
                        if row_data["opponent"] == "Nott'ham Forest":
                            row_data["opponent"] = "Nottingham Forest"

                        all_player_data.append(row_data)
                        print(f"  ✔ {player_name} eklendi")

                    if i % 10 == 0 and all_player_data:
                        temp_df = pd.DataFrame(all_player_data)
                        temp_df = temp_df.reindex(columns=final_columns)
                        temp_df.to_csv("temp_output.csv", index=False, encoding="utf-8-sig")
                        print("💾 Ara kayıt yapıldı → temp_output.csv")

                except Exception as e:
                    print(f"❌ {team_name} ({location}) verisi alınamadı: {e}")

        except Exception as e:
            print(f"⚠️ Maç raporu hatası: {e}")
            continue

print("\n🔝 Tarayıcı kapatılıyor...")
driver.quit()

if all_player_data:
    df = pd.DataFrame(all_player_data)
    df = df.reindex(columns=final_columns)
    filename = f"tum_maclar_oyuncular_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"\n🏆 {len(df)} oyuncu satırı kaydedildi → {filename}")
else:
    print("❌ Hiç veri alınamadı.")
