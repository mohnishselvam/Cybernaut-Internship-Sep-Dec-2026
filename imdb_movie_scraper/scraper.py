from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import time

# ============================================================
# IMDb Top 250 Movie Scraper
# Step 2: Data Cleaning & Validation
# ============================================================

# ------------------------------------------------------------
# Chrome settings
# ------------------------------------------------------------

options = webdriver.ChromeOptions()

options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")

# Start Chrome
driver = webdriver.Chrome(options=options)

print("========================================")
print("IMDb Movie Rating Scraper")
print("Step 2: Data Cleaning & Validation")
print("========================================")

print("\nChrome started")

# ------------------------------------------------------------
# Open IMDb Top 250
# ------------------------------------------------------------

url = "https://www.imdb.com/chart/top/"

print("Opening IMDb Top 250...")

driver.get(url)

# Wait for IMDb page to load
print("Waiting for IMDb page to load...")

time.sleep(10)

print("IMDb request completed")

# ------------------------------------------------------------
# Check page
# ------------------------------------------------------------

print("\nPage title:")
print(driver.title)

print("\nCurrent URL:")
print(driver.current_url)

# ------------------------------------------------------------
# Find all movies
# ------------------------------------------------------------

movies = driver.find_elements(
    By.CSS_SELECTOR,
    "li.ipc-metadata-list-summary-item"
)

print("\nMovies found:", len(movies))

# ------------------------------------------------------------
# Store movie data
# ------------------------------------------------------------

movie_data = []

# ------------------------------------------------------------
# Extract movie details
# ------------------------------------------------------------

print("\nExtracting movie information...")
print("----------------------------------------")

for movie in movies:

    try:

        # Extract rank
        rank = movie.find_element(
            By.CSS_SELECTOR,
            '[data-testid="title-list-item-ranking"]'
        ).text

        # Extract title
        title = movie.find_element(
            By.CSS_SELECTOR,
            "h4.ipc-title__text"
        ).text

        # Extract year
        year = movie.find_element(
            By.CSS_SELECTOR,
            "div.cli-title-metadata li"
        ).text

        # Extract rating
        rating = movie.find_element(
            By.CSS_SELECTOR,
            '[data-testid="ratingGroup--imdb-rating"] .ipc-rating-star--rating'
        ).text

        # Add raw data to list
        movie_data.append({
            "Rank": rank,
            "Title": title,
            "Year": year,
            "Rating": rating
        })

    except Exception as e:

        print("Error extracting movie:", e)

# ------------------------------------------------------------
# Close Chrome
# ------------------------------------------------------------

driver.quit()

print("\nChrome closed")

# ============================================================
# DATA CLEANING
# ============================================================

print("\n========================================")
print("DATA CLEANING")
print("========================================")

# Create DataFrame
df = pd.DataFrame(movie_data)

print("\nRaw records:", len(df))

# ------------------------------------------------------------
# Clean Rank
# ------------------------------------------------------------

# Remove # symbol
df["Rank"] = (
    df["Rank"]
    .astype(str)
    .str.replace("#", "", regex=False)
    .str.strip()
)

# Convert Rank to numeric
df["Rank"] = pd.to_numeric(
    df["Rank"],
    errors="coerce"
)

# ------------------------------------------------------------
# Clean Title
# ------------------------------------------------------------

df["Title"] = (
    df["Title"]
    .astype(str)
    .str.strip()
)

# ------------------------------------------------------------
# Clean Year
# ------------------------------------------------------------

df["Year"] = (
    df["Year"]
    .astype(str)
    .str.strip()
)

df["Year"] = pd.to_numeric(
    df["Year"],
    errors="coerce"
)

# ------------------------------------------------------------
# Clean Rating
# ------------------------------------------------------------

df["Rating"] = (
    df["Rating"]
    .astype(str)
    .str.strip()
)

df["Rating"] = pd.to_numeric(
    df["Rating"],
    errors="coerce"
)

# ------------------------------------------------------------
# Remove incomplete records
# ------------------------------------------------------------

before_cleaning = len(df)

df = df.dropna(
    subset=["Rank", "Title", "Year", "Rating"]
)

after_cleaning = len(df)

removed_records = before_cleaning - after_cleaning

print("\nIncomplete records removed:", removed_records)

# ------------------------------------------------------------
# Remove duplicate ranks
# ------------------------------------------------------------

before_duplicates = len(df)

df = df.drop_duplicates(
    subset=["Rank"],
    keep="first"
)

duplicate_records = before_duplicates - len(df)

print("Duplicate records removed:", duplicate_records)

# ------------------------------------------------------------
# Sort by rank
# ------------------------------------------------------------

df = df.sort_values(
    by="Rank"
)

# Reset DataFrame index
df = df.reset_index(drop=True)

# ============================================================
# VALIDATION
# ============================================================

print("\n========================================")
print("DATA VALIDATION")
print("========================================")

print("\nFinal records:", len(df))

print("Missing values:")
print(df.isnull().sum())

print("\nDuplicate ranks:", df["Rank"].duplicated().sum())

# ------------------------------------------------------------
# Check rating range
# ------------------------------------------------------------

invalid_ratings = df[
    (df["Rating"] < 0) |
    (df["Rating"] > 10)
]

print("Invalid ratings:", len(invalid_ratings))

# ============================================================
# SAVE CLEAN DATASET
# ============================================================

df.to_csv(
    "imdb_top_250.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n========================================")
print("CSV FILE CREATED SUCCESSFULLY")
print("========================================")

print("\nFile:")
print("imdb_top_250.csv")

# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\nFirst 10 Movies")
print("==============================")

print(
    df.head(10).to_string(index=False)
)

print("\n========================================")
print("SCRAPING COMPLETED")
print("========================================")

print("Total movies saved:", len(df))

print("\nData types:")
print(df.dtypes)

print("\n========================================")
print("Program finished successfully")
print("========================================")