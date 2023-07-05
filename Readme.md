# NACE Code Search

Nace code suggestions based on internal contents and descriptions of the codes.

## Dependencies

To install the dependencies:

pip install -r requirements.txt


## Usage

1. Run the application:

    python3 app.py (for the standard verison)
    python3 appV2.py (for the version with synonyms)

2. Open your web browser and go to `http://localhost:5000`.

3. Enter a search term in the provided input field and click the "Search" button or hit enter.

4. The application will display matching NACE codes.

## Data Source

The application relies on pre-scraped data for NACE codes and their descriptions source: https://nacev2.com/en

## Data Scraping

The entirety of the descriptions were used generate the JSON file, hence there is room for pre-processing for a more efficient search.