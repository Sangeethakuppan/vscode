from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
import time
import pandas as pd
from datetime import datetime, timedelta
import mysql.connector
import pymysql
import streamlit as st
from sqlalchemy import create_engine


def convert_to_datetime(time_str, base_date):
    """Convert a time string to a datetime object."""
    try:
        return datetime.strptime(time_str, '%I:%M %p').replace(year=base_date.year, month=base_date.month, day=base_date.day)
    except ValueError:
        return None

driver = webdriver.Chrome()
driver.maximize_window()

# Open Redbus website
driver.get("https://www.redbus.in")
time.sleep(5)  # Wait for the page to load

# Click 'View All' button in the Government Bus Corporations section
try:
    view_all_button = driver.find_element(By.XPATH, '//*[@id="homeV2-root"]/div[3]/div[1]/div[2]/a')
    view_all_button.click()
    print("View All button clicked successfully.")
except NoSuchElementException:
    print("View All button not found.")
    driver.quit()
    exit()

time.sleep(5)

# Switch to the new tab
driver.switch_to.window(driver.window_handles[1])

# Scroll down to the bottom of the page
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)  # Wait to load the page
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Select a bus corporation
try:
    bus_corp = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="root"]/div/article[2]/div/div/ul[3]/li[3]/a'))
    )
    
    # Scroll the element into view
    driver.execute_script("arguments[0].scrollIntoView(true);", bus_corp)
    time.sleep(2)
    
    # Click the bus corporation link
    bus_corp.click()
    time.sleep(5)
except ElementClickInterceptedException:
    print("Element is not clickable, trying again...")
    bus_corp.click()
    time.sleep(5)
except NoSuchElementException:
    print("Bus corporation link not found.")
    driver.quit()
    exit()

# Initialize list to store routes
routes = []

# Loop to manually click each page and scrape data
while True:
    input("Please click the next page number button manually, wait for the page to load, then press Enter to confirm...")

    # Scrape route names and their links
    route_elements = driver.find_elements(By.CLASS_NAME, 'route')
    for route_element in route_elements:
        route = route_element.text  # Get the route name
        route_link = route_element.get_attribute('href')  # Get the route link
        routes.append((route, route_link))
    
    # Check if there are more pages to click
    more_pages = input("Are there more pages to click? (yes/no): ")
    if more_pages.lower() != 'yes':
        break

# Print the scraped routes to view them
print("Scraped Routes and Links:")
for route, link in routes:
    print(f"Route: {route}, Link: {link}")

# Now use the scraped routes and links to get bus details
bus_details = []

for route, route_link in routes:
    driver.get(route_link)
    time.sleep(5)  # Wait for the page to load

    # Click the 'View Buses' button if present
    try:
        view_buses_button = driver.find_element(By.CLASS_NAME, 'button')
        view_buses_button.click()
        time.sleep(5)
    except NoSuchElementException:
        pass  # No 'View Buses' button present

    # Scroll down to the bottom of the page
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait to load the page
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    try:
        bus_elements = driver.find_elements(By.CSS_SELECTOR, "div.bus-item")
    except NoSuchElementException:
        print("No bus elements found")
        continue

    for bus in bus_elements:
        try:
            busname = bus.find_element(By.CSS_SELECTOR, "div.travels.lh-24.f-bold.d-color").text
        except NoSuchElementException:
            busname = "N/A"

        try:
            bustype = bus.find_element(By.CSS_SELECTOR, "div.bus-type.f-12.m-top-16.l-color.evBus").text
        except NoSuchElementException:
            bustype = "N/A"

        try:
            departing_time = bus.find_element(By.CSS_SELECTOR, "div.dp-time.f-19.d-color.f-bold").text
            departing_time_dt = convert_to_datetime(departing_time, datetime.now())
        except NoSuchElementException:
            departing_time_dt = None

        try:
            duration = bus.find_element(By.CSS_SELECTOR, "div.dur.l-color.lh-24").text
        except NoSuchElementException:
            duration = "N/A"

        try:
            reaching_time = bus.find_element(By.CSS_SELECTOR, "div.bp-time.f-19.d-color.disp-Inline").text
            reaching_time_dt = convert_to_datetime(reaching_time, datetime.now())
            if reaching_time_dt and departing_time_dt and reaching_time_dt < departing_time_dt:
                reaching_time_dt += timedelta(days=1)
        except NoSuchElementException:
            reaching_time_dt = None

        try:
            star_rating = bus.find_element(By.CSS_SELECTOR, "div.rating-sec.lh-24").text
            star_rating = float(star_rating) if star_rating != "N/A" else 0.0
        except NoSuchElementException:
            star_rating = 0.0

        try:
            price = bus.find_element(By.CSS_SELECTOR, "span.f-19.f-bold").text
            price = float(price.replace('₹', '').replace(',', '').strip()) if price != "N/A" else None
        except NoSuchElementException:
            price = None

        try:
            seats_available = bus.find_element(By.CSS_SELECTOR, "div.seat-left.m-top-16").text
            seats_available = int(seats_available.split()[0]) if seats_available != "N/A" else 0
        except NoSuchElementException:
            seats_available = 0

        bus_details.append((route, route_link, busname, bustype, departing_time_dt, duration, reaching_time_dt, star_rating, price, seats_available))

# Print the scraped bus details to view them
print("Scraped Bus Details:")
for detail in bus_details:
    print(detail)

# Connect to the MySQL database
conn = pymysql.connect(
    host='127.0.0.1',
    user='root',
    passwd='Lakshmi@123',
    db='red_bus'  # Make sure the database exists
)
cursor = conn.cursor()

# Create the bus_routes table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS bus_routes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        route_name TEXT,
        route_link TEXT,
        busname TEXT,
        bustype TEXT,
        departing_time TIME,
        duration TEXT,
        reaching_time TIME,
        star_rating FLOAT,
        price DECIMAL(10, 2),
        seats_available INT
    )
''')


# Insert scraped data into the bus_routes table
for detail in bus_details:
	cursor.execute('''
	    INSERT INTO bus_routes (
	        route_name, route_link, busname, bustype, departing_time,
	        duration, reaching_time, star_rating, price, seats_available
	    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
	''', detail)

# Commit the transaction and close the connection
conn.commit()
conn.close()
print("Data has been successfully saved to the database.")
    
# Connect to the MySQL database
conn = pymysql.connect(
    host='127.0.0.1',
    user='root',
    passwd='Lakshmi@123',
    db='red_bus'  # Make sure the database exists
)
cursor = conn.cursor()

# Create the bus_routes table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS bus_routes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        route_name TEXT,
        route_link TEXT,
        busname TEXT,
        bustype TEXT,
        departing_time TIME,
        duration TEXT,
        reaching_time TIME,
        star_rating FLOAT,
        price DECIMAL(10, 2),
        seats_available INT
    )
''')


# Insert scraped data into the bus_routes table
for detail in bus_details:
	cursor.execute('''
	    INSERT INTO bus_routes (
	        route_name, route_link, busname, bustype, departing_time,
	        duration, reaching_time, star_rating, price, seats_available
	    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
	''', detail)

# Commit the transaction and close the connection
conn.commit()
conn.close()
print("Data has been successfully saved to the database.")