from flask import Flask, request, render_template
import requests
import difflib
import json
from bs4 import BeautifulSoup
from nltk.util import ngrams
from rapidfuzz import process, fuzz
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
import nltk

# nltk.download('punkt')
# nltk.download('wordnet')

app = Flask(__name__)

main_urls = ["https://nacev2.com/en/activity/agriculture-forestry-and-fishing",
            "https://nacev2.com/en/activity/mining-and-quarrying",
            "https://nacev2.com/en/activity/manufacturing",
            "https://nacev2.com/en/activity/electricity-gas-steam-and-air-conditioning-supply",
            "https://nacev2.com/en/activity/water-supply-sewerage-waste-management-and-remediation-activities",
            "https://nacev2.com/en/activity/construction",
            "https://nacev2.com/en/activity/wholesale-and-retail-trade-repair-of-motor-vehicles-and-motorcycles",
            "https://nacev2.com/en/activity/transportation-and-storage",
            "https://nacev2.com/en/activity/accommodation-and-food-service-activities",
            "https://nacev2.com/en/activity/information-and-communication",
            "https://nacev2.com/en/activity/financial-and-insurance-activities",
            "https://nacev2.com/en/activity/real-estate-activities",
            "https://nacev2.com/en/activity/professional-scientific-and-technical-activities",
            "https://nacev2.com/en/activity/administrative-and-support-service-activities",
            "https://nacev2.com/en/activity/public-administration-and-defence-compulsory-social-security",
            "https://nacev2.com/en/activity/education",
            "https://nacev2.com/en/activity/human-health-and-social-work-activities",
            "https://nacev2.com/en/activity/arts-entertainment-and-recreation",
            "https://nacev2.com/en/activity/other-service-activities",
            "https://nacev2.com/en/activity/activities-of-households-as-employers-undifferentiated-goods-and-services-producing-activities-of-households-for-own-use",
            "https://nacev2.com/en/activity/activities-of-extraterritorial-organisations-and-bodies"           
            ]
data_file = 'nace_data.json'

def generate_ngrams(words):
    one_grams = words
    two_grams = [' '.join(gram) for gram in ngrams(words, 2)]
    three_grams = [' '.join(gram) for gram in ngrams(words, 3)]
    return one_grams + two_grams + three_grams

def scrape_data(urls):
    nace_keywords = {}
    nace_codes = {}

    for main_url in urls:
        response = requests.get(main_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        items = soup.find_all('a', {'class': 'list__grid--item'})

        for item in items:
            code_name = item.get_text()
            url = "https://nacev2.com" + item['href']

            code, name = code_name.split(' - ', 1)
            nace_codes[code] = name

            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            description = soup.find(class_='item--description').text
            keywords = generate_ngrams(description.split())

            for keyword in keywords:
                nace_keywords.setdefault(keyword, []).append(code)

    with open(data_file, 'w') as f:
        json.dump({'nace_keywords': nace_keywords, 'nace_codes': nace_codes}, f)

def load_data():
    with open(data_file, 'r') as f:
        data = json.load(f)
    return data['nace_keywords'], data['nace_codes']

def find_best_matches(word, possibilities):
    return process.extract(word, possibilities, scorer=fuzz.WRatio, score_cutoff=90, limit=7)

def get_synonyms(word):
    synonyms = set()
    for synset in wordnet.synsets(word):
        for lemma in synset.lemmas():
            synonyms.add(lemma.name())
    return list(synonyms)

def search_nace_with_synonyms(user_input, nace_keywords, nace_codes):
    words = word_tokenize(user_input)

    primary_results = search_nace(user_input, nace_keywords, nace_codes)

    synonyms = [get_synonyms(word) for word in words]
    synonyms = [syn for syn_list in synonyms for syn in syn_list]
    synonyms = list(set(synonyms))

    additional_results = []
    for syn in synonyms:
        syn_results = search_nace(syn, nace_keywords, nace_codes)
        additional_results += [result for result in syn_results if "NACE code" in result]

    primary_results = list({v['NACE code']:v for v in primary_results}.values())
    additional_results = list({v['NACE code']:v for v in additional_results}.values())


    primary_codes = {result['NACE code'] for result in primary_results}
    additional_results = [result for result in additional_results if result['NACE code'] not in primary_codes]

    primary_results.sort(key=lambda x: x['score'], reverse=True)
    additional_results.sort(key=lambda x: x['score'], reverse=True)

    return primary_results, additional_results, synonyms





def search_nace(user_input, nace_keywords, nace_codes):
    if user_input in nace_codes:
        return [{"NACE code": user_input, "title": nace_codes[user_input], "score": 100}]
    else:
        best_matches = find_best_matches(user_input, nace_keywords.keys())
        matching_codes_with_titles = []
        for match, score, _ in best_matches:
            if len(match) < 3:
                continue
            for code in nace_keywords.get(match, []):
                matching_codes_with_titles.append({"NACE code": code, "title": nace_codes[code], "score": score})
        if matching_codes_with_titles:
            matching_codes_with_titles = list({v['NACE code']:v for v in matching_codes_with_titles}.values())
            matching_codes_with_titles.sort(key=lambda x: x['score'], reverse=True)
            return matching_codes_with_titles
        else:
            return [{"message": "No matching NACE code found."}]


try:
    nace_keywords, nace_codes = load_data()
except FileNotFoundError:
    scrape_data(main_urls)
    nace_keywords, nace_codes = load_data()
    
@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    if request.method == 'POST':
        user_input = request.form.get('search')
        primary_results, additional_results, synonyms = search_nace_with_synonyms(user_input, nace_keywords, nace_codes)
        results = {
            'primary_results': primary_results,
            'additional_results': additional_results,
            'synonyms': synonyms
        }
    return render_template('search_with_synonyms.html', results=results)



if __name__ == '__main__':
    app.run(debug=True)