import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import spacy
import time
from names_dataset import NameDataset, NameWrapper
from transliterate import translit, get_available_language_codes
from geopy.geocoders import Nominatim
from countryinfo import CountryInfo

start_time = time.time()

input_file = "authors_urls_3.csv"
df = pd.read_csv(input_file)

nd = NameDataset()
nlp = spacy.load("uk_core_news_lg")
geolocator = Nominatim(user_agent = "my_app")


def get_text(element):
    if element:
        return element.get_text(separator=' ', strip=True)
    return None

def perform_ner(text):
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities.append({"text": ent.text, "label": ent.label_})
    return entities


def extract_name(soup):
    header = soup.find(class_="mw-page-title-main")
    return get_text(header)

def get_full_loc(loc):
    def extract_before_keyword(text_list, keyword):
        for item in text_list:
            if keyword in item:
                match = re.search(rf"(.*?)(?=\s*{keyword})", item)
                if match:
                    return match.group(1).strip()
        return ''

    location = geolocator.geocode(loc, language='uk')
    if location:
        full_loc = location.raw.get('display_name', '').split(", ")
        if not full_loc:
            return '', '', ''
        
        city = full_loc[0]
        district = full_loc[1] if len(full_loc) > 2 else ''
        region = full_loc[-1]

        if region == 'Україна':
            region = extract_before_keyword(full_loc, 'область') or region
            district = extract_before_keyword(full_loc, 'район') or district

        return city, district, region
    return '', '', ''

def extract_birth_info(soup):
    possible_headers = ["Народився", "Дата народження", "Народження", "Народилася", " Народження:"]

    def extract_location(data_text, entities):
        """Extract city, district, and region using NER or fallback tokens."""
        city, district, region = '', '', ''
        
        if entities:
            city, district, region = get_full_loc(entities[0]["text"])
        
        if not (city or district or region):
            text_tokens = re.findall(r"\b[A-ZА-ЯІЇЄҐ][a-zа-яіїєґ]*[a-zа-яіїєґ'-]*\b", data_text)
            if text_tokens:
                city, district, region = get_full_loc(text_tokens[0])
        
        return city, district, region

    for header in possible_headers:
        row = soup.find("th", string=re.compile(fr"^\s*{header}\s*$"))
        if row:
            data = row.find_next_sibling("td")
            if data:
                data_text = get_text(data)
                birth_year_match = re.search(r"\b(\d{4})\b", data_text)
                birth_year = birth_year_match.group(1) if birth_year_match else None

                text_after_year = data_text.split(birth_year, 1)[1].strip() if birth_year else data_text

                entities = perform_ner(text_after_year)
                city, district, region = extract_location(text_after_year, entities)

                if not (city or region):
                    if entities and len(entities) > 0:
                        city = entities[0]["text"]
                        region = entities[-1]["text"] if len(entities) > 1 else city
                    else:
                        text_tokens = re.findall(r"\b[A-ZА-ЯІЇЄҐ][a-zа-яіїєґ]*[a-zа-яіїєґ'-]*\b", data_text)
                        if text_tokens:
                            city = text_tokens[0]
                            region = text_tokens[-1] if len(text_tokens) > 1 else city

                return {
                    "text": data_text,
                    "year": birth_year,
                    "city": city,
                    "district": district,
                    "region": region,
                }

    return None


def extract_death_info(soup):
    possible_headers = ["Помер", "Смерть:", "Дата смерті", "Померла", "Смерть:"]

    for header in possible_headers:
        row = soup.find("th", string=re.compile(fr"^\s*{header}\s*$"))
        if row:
            data = row.find_next_sibling("td")
            if data:
                data_text = get_text(data)
                
                death_year_match = re.search(r"\b(\d{4})\b", data_text)
                death_year = death_year_match.group(1) if death_year_match else None
                return {"text": data_text, "year": death_year}
    return None

def get_sex(name):
    first_name = name.split()[0]
    full_sex = NameWrapper(nd.search(first_name)).gender
    if (full_sex and full_sex != ''):
        return full_sex[0]
    else:
        tr_name = re.sub('\'', '', translit('Гельмут', 'uk', reversed=True))
        full_sex = NameWrapper(nd.search(tr_name)).gender
        
    if (full_sex and full_sex != ''):
        return full_sex[0]
    else:
        return None
    
def get_birth_country(soup):
    possible_headers = ["Місце народження", "Країна", "Країна:"]

    def extract_location(data_text, entities):
        city, district, region = '', '', ''
        
        if entities:
            city, district, region = get_full_loc(entities[0]["text"])
        
        if not (city or district or region):
            text_tokens = re.findall(r"\b[A-ZА-ЯІЇЄҐ][a-zа-яіїєґ]*[a-zа-яіїєґ'-]*\b", data_text)
            if text_tokens:
                city, district, region = get_full_loc(text_tokens[0])
        
        return city, district, region

    for header in possible_headers:
        row = soup.find("th", string=re.compile(fr"^\s*{header}\s*$"))
        if row:
            data = row.find_next_sibling("td")
            if data:
                data_text = get_text(data)

                entities = perform_ner(data_text)
                city, district, region = extract_location(data_text, entities)

                if not (city or region):
                    if entities and len(entities) > 0:
                        city = entities[0]["text"]
                        region = entities[-1]["text"] if len(entities) > 1 else city
                    else:
                        text_tokens = re.findall(r"\b[A-ZА-ЯІЇЄҐ][a-zа-яіїєґ]*[a-zа-яіїєґ'-]*\b", data_text)
                        if text_tokens:
                            city = text_tokens[0]
                            region = text_tokens[-1] if len(text_tokens) > 1 else city

                return {
                    "text": data_text,
                    "city": city,
                    "district": district,
                    "region": region,
                }

    return {
        "text": '',
        "city": '',
        "district": '',
        "region": '',
    }
    
def get_mother_language(name):
    location = geolocator.geocode(name, language='en')
    if (location):
        full_loc = location.raw['display_name'].split(", ")[-1]
        country = CountryInfo(full_loc)
        if (country):
            return country.languages()[0]
        else:
            return ''
    else:
        return ''

def fetch_wikipedia_article(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except Exception as e:
        print(f"Помилка завантаження {url}: {e}")
        return ""

def parse_article_content(soup, url, name):
    try:
        full_name = extract_name(soup)
        birth_info = extract_birth_info(soup)
        death_info = extract_death_info(soup)
        mother_lang = ''
        sex = ''
        birth_year = ''
        death_year = ''

        if (birth_info["city"] == '' and birth_info["district"] == '' and birth_info["region"] == ''):
            birth_country_info = get_birth_country(soup)
            city = birth_country_info["city"]
            district = birth_country_info["district"]
            region = birth_country_info["region"]
        else:
            city = birth_info["city"]
            district = birth_info["district"]
            region = birth_info["region"]

        if full_name:
            sex = get_sex(full_name)
        
        if city:
            mother_lang = get_mother_language(city).upper()
            
        if (birth_info and birth_info["year"]):
            birth_year = birth_info["year"]
            
        if (death_info and death_info["year"]):
            death_year = death_info["year"]
            
            
            
        return {
            'Автор': name,
            'Повне ім\'я': full_name,
            'Рік народження': birth_year,
            'Рік смерті': death_year,
            'Місце народження': city,
            'Район': district,
            'Регіон': region,
            'URL': url,
            'Рідна мова': mother_lang,
            'Стать': sex
        }
    except Exception as e:
        print(f"Error parsing article content for URL: {url}")
        print(f"Error details: {e}")
        return None

results = []
save_frequency = 5  # Як часто зберігати DataFrame
output_file = 'parsed_data_3.csv'

for idx, row in enumerate(df[['Name', 'URL']].itertuples(index=False), start=1):
    name, url = row
    if url:
        try:
            article_content = fetch_wikipedia_article(url)
            parsed_data = parse_article_content(article_content, url, name)
            
            if parsed_data:
                results.append(parsed_data)
            
            # Зберігати кожні 5 рядків
            if idx % save_frequency == 0 or idx == len(df):
                temp_df = pd.DataFrame(results)
                if idx == save_frequency:  # Якщо перше збереження
                    temp_df.to_csv(output_file, index=False)
                else:
                    temp_df.to_csv(output_file, mode='a', header=False, index=False)
                print(f"Data saved to {output_file} at row {idx}")
                results.clear()  # Очистити список після збереження
        except Exception as e:
            print(f"Error fetching or processing URL: {url}")
            print(f"Error details: {e}")
            
            
end_time = time.time()
execution_time = end_time - start_time
print(f"\nЧас виконання програми: {execution_time:.6f} секунд")