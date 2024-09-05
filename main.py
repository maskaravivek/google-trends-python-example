from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup
import time
import csv

import pandas as pd
import matplotlib.pyplot as plt

def get_driver():
    # update the path to the location of your Chrome binary
    CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    options = Options()
    options.add_argument("--headless=new")
    options.binary_location = CHROME_PATH

    driver = webdriver.Chrome(options=options)

    return driver


def get_raw_trends_data(
    driver: webdriver.Chrome, date_range: str, geo: str, query: str
) -> str:
    url = f"https://trends.google.com/trends/explore?date={date_range}&geo={geo}&q={query}"

    print(f"Getting data from {url}")

    driver.get(url)
    # workaround to get the page source after initial 429 error
    driver.get(url)
    driver.maximize_window()

    # Wait for the page to load
    time.sleep(5)

    return driver.page_source

def extract_interest_by_sub_region(content: str) -> dict:
    soup = BeautifulSoup(content, "html.parser")

    interest_by_subregion = soup.find(
        "div", class_="geo-widget-wrapper geo-resolution-subregion"
    )

    related_queries = interest_by_subregion.find_all(
        "div", class_="fe-atoms-generic-content-container"
    )

    # Dictionary to store the extracted data
    interest_data = {}

    # Extract the region name and interest percentage
    for query in related_queries:
        items = query.find_all("div", class_="item")
        for item in items:
            region = item.find("div", class_="label-text").text.strip()
            interest = item.find("div", class_="progress-value").text.strip()
            interest_data[region] = interest

    return interest_data


def extract_interest_by_sub_region(content: str) -> dict:
    soup = BeautifulSoup(content, "html.parser")

    interest_by_subregion = soup.find(
        "div", class_="geo-widget-wrapper geo-resolution-subregion"
    )

    related_queries = interest_by_subregion.find_all(
        "div", class_="fe-atoms-generic-content-container"
    )

    # Dictionary to store the extracted data
    interest_data = {}

    for query in related_queries:
        items = query.find_all("div", class_="item")
        for item in items:
            region = item.find("div", class_="label-text").text.strip()
            interest = item.find("div", class_="progress-value").text.strip()
            interest_data[region] = interest

    return interest_data

def save_interest_by_sub_region(interest_data: dict):
    interest_data = [{"Region": region, "Interest": interest} for region, interest in interest_data.items()]

    csv_file = "interest_by_region.csv"

    # Open the CSV file for writing
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["Region", "Interest"])
        writer.writeheader()  # Write the header
        writer.writerows(interest_data)  # Write the data

    print(f"Data saved to {csv_file}")
    
    return csv_file

def plot_sub_region_data(csv_file_path, output_file_path):
    # Load the data from the CSV file
    df = pd.read_csv(csv_file_path)

    # Create a bar chart for comparison by region
    plt.figure(figsize=(30, 12))
    
    plt.bar(df["Region"], df["Interest"], color="skyblue")
    
    # Add titles and labels
    plt.title('Interest by Region')
    plt.xlabel('Region')
    plt.ylabel('Interest')

    # Rotate the x-axis labels if needed
    plt.xticks(rotation=45)

    # Show the plot
    plt.savefig(output_file_path)

# Parameters
date_range = "now 7-d"
geo = "US"
query = "coffee"
all_data = {}

# Get the raw data
driver = get_driver()

raw_data = get_raw_trends_data(driver, "now 7-d", "US", "coffee")

# Extract the interest by region
interest_data = extract_interest_by_sub_region(raw_data)
all_data.update(interest_data)

# Get paginated interest data
while True:
    # Click the md-button to load more data if available
    try:
        geo_widget = driver.find_element(
            By.CSS_SELECTOR, "div.geo-widget-wrapper.geo-resolution-subregion"
        )
        
        # Find the load more button with class name "md-button" and aria-label "Next"
        load_more_button = geo_widget.find_element(
            By.CSS_SELECTOR, "button.md-button[aria-label='Next']"
        )
        
        icon = load_more_button.find_element(By.CSS_SELECTOR, ".material-icons")
        
        # Check if the button is disabled by checking class-name includes arrow-right-disabled
        if "arrow-right-disabled" in icon.get_attribute("class"):
            print("No more data to load")
            break
        
        load_more_button.click()
        time.sleep(2)
        
        extracted_data = extract_interest_by_sub_region(driver.page_source)
        all_data.update(extracted_data)
    except Exception as e:
        print("No more data to load", e)
        break

driver.quit()

csv_file_path = save_interest_by_sub_region(all_data)

output_file_path = "interest_by_region.png"
plot_sub_region_data(csv_file_path, output_file_path)