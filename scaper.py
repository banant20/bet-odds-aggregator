from bs4 import BeautifulSoup
import requests
import pandas as pd
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import re


def setup_driver():
    options = Options()
    options.add_argument("--headless")  # Run headless Chrome
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def parse_spread(spread_text):
    """Parse the spread text to separate the line and odds."""
    match = re.findall(r"([+-]?\d+(?:\.\d+)?|pk)([+-]?\d+|Even)?", spread_text)
    if match:
        line, odds = match[0]
        return line, odds
    else:
        return None, None

def parse_total(total_text):
    """Parse the total text to extract only the numeric part."""
    match = re.search(r"\d+(\.\d+)?", total_text)
    if match:
        return match.group(0)
    return None

def dk_scraper():
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    
    url = "https://sportsbook.draftkings.com/leagues/football/nfl" 
    # Fetch the data
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, 'lxml')
        games = soup.find_all("div", class_="parlay-card-10-a")

        data = []

        for game in games:
            teams = game.find_all("div", class_="event-cell__name-text")
            if len(teams) == 2:
                away_team = teams[0].text.strip()
                home_team = teams[1].text.strip()
            else:
                continue

            odds = game.find_all("div", class_="sportsbook-outcome-cell__body")

            if len(odds) == 6:  # There should be 6 cells of odds for each game
                away_spread_line = odds[0].find("span", class_="sportsbook-outcome-cell__line")
                away_spread_odds = odds[0].find("span", class_="sportsbook-odds")
                home_spread_line = odds[3].find("span", class_="sportsbook-outcome-cell__line")
                home_spread_odds = odds[3].find("span", class_="sportsbook-odds")
                over_total_line = odds[1].find("span", class_="sportsbook-outcome-cell__line")
                away_moneyline = odds[2].find("span", class_="sportsbook-odds")
                home_moneyline = odds[5].find("span", class_="sportsbook-odds")
                
                game_info = {
                    "Away": away_team,
                    "Home": home_team,
                    "HSPR": {
                        "draftkings": home_spread_line.text.strip() if home_spread_line else None
                    },
                    "HSPRO": {
                        "draftkings": home_spread_odds.text.strip() if home_spread_odds else None
                    },
                    "ASPR": {
                        "draftkings": away_spread_line.text.strip() if away_spread_line else None
                    },
                    "ASPRO": {
                        "draftkings": away_spread_odds.text.strip() if away_spread_odds else None
                    },
                    "O/U": {
                        "draftkings": over_total_line.text.strip() if over_total_line else None
                    },
                    "AML": {
                        "draftkings": away_moneyline.text.strip() if away_moneyline else None
                    },
                    "HML": {
                        "draftkings": home_moneyline.text.strip() if home_moneyline else None
                    }
                }

                data.append(game_info)
        
        df = pd.DataFrame(data)
        print(df)
                
        # MongoDB Instance
        client = MongoClient("localhost", 27017)
        # Create Database
        db = client['sportsbooks']
        collection = db['dk_nfl_odds']
        
        
        # Clear the collection and insert new data
        collection.delete_many({})
        collection.insert_many(data)

        return {
            'statusCode': 200,
            'body': 'DraftKings NFL odds scraping and database update successful'
        }
        
        # data = list(collection.find())
        # for doc in data:
        #     print(doc)


    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {url}: {str(e)}")
        
def espn_scraper():
    driver = setup_driver()
    url = "https://espnbet.com/sport/football/organization/united-states/competition/nfl/featured-page"
    try:
        driver.get(url)
        time.sleep(5)  # Wait for the page to load

        soup = BeautifulSoup(driver.page_source, 'lxml')
        games = soup.find_all('article', class_='b-default pt-2 first:pt-0 last:pb-0 first:pt-0')

        data = []

        for game in games:
            teams = game.find_all('button', {'data-testid': 'team-name'})
            if len(teams) == 2:
                away_team = teams[0].text.strip()
                home_team = teams[1].text.strip()
            else:
                continue

            bet_buttons = game.find_all('button', {'data-dd-action-name': 'Add Bet Selections'})
            if len(bet_buttons) >= 6:
                away_spread_line, away_spread_odds = parse_spread(bet_buttons[0].text.strip())
                home_spread_line, home_spread_odds = parse_spread(bet_buttons[3].text.strip())
                over_total_line = parse_total(bet_buttons[1].text.strip())
                # under_total_line = bet_buttons[4].text.strip()
                away_moneyline = bet_buttons[2].text.strip()
                home_moneyline = bet_buttons[5].text.strip()

                game_info = {
                    "Away": away_team,
                    "Home": home_team,
                    "HSPR": {
                        "espnbet": home_spread_line
                    },
                    "HSPRO": {
                        "espnbet": home_spread_odds
                    },
                    "ASPR": {
                        "espnbet": away_spread_line
                    },
                    "ASPRO": {
                        "espnbet": away_spread_odds
                    },
                    "O/U": {
                        "espnbet": over_total_line
                    },
                    "AML": {
                        "espnbet": away_moneyline
                    },
                    "HML": {
                        "espnbet": home_moneyline
                    }
                }

            data.append(game_info)
        
        driver.quit()
        
        df = pd.DataFrame(data)
        print(df)
        # MongoDB Instance
        client = MongoClient("localhost", 27017)
        # Create Database
        db = client['sportsbooks']
        collection = db['espn_nfl_odds']
        
        
        # Clear the collection and insert new data
        collection.delete_many({})
        collection.insert_many(data)
        
        return {
            'statusCode': 200,
            'body': 'ESPN NFL odds Scraping and database update successful'
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {url}: {str(e)}")


if __name__ == "__main__":
    dk_scraper()
    espn_scraper()