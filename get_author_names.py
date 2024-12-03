from bs4 import BeautifulSoup
import wikipediaapi
import pandas as pd 

with open("file.html", "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

rows = soup.find_all("tr")

names = []

for row in rows[15001:]:
    columns = row.find_all("td")
    if columns:
      
        name = BeautifulSoup(columns[0].get_text(strip=True), "html.parser").text
        
        names.append(name)

def split_and_process_names(names_list):
    processed_names = []
    for name in names_list:
        # Розділяємо імена, якщо є символ '&'
        separated_names = [n.strip() for n in name.split("&")]
        processed_names.extend(separated_names)
    return processed_names


names = split_and_process_names(names)

wiki_wiki = wikipediaapi.Wikipedia('application_for_practice', 'uk')

def find_wikipedia_articles(names):
    results = {}
    for name in names:
        print(name)
        page = wiki_wiki.page(name)
        if page.exists():
            results[name] = {
                "title": page.title,
                "url": page.fullurl
            }
        else:
            results[name] = None
    return results

articles = find_wikipedia_articles(names)

# Convert articles dictionary to a DataFrame
def create_dataframe(articles):
    data = []
    for name, info in articles.items():
        if info:
            data.append({"Name": name, "URL": info["url"]})
        else:
            data.append({"Name": name, "URL": None})
    return pd.DataFrame(data)

# Create DataFrame from results
df = create_dataframe(articles)

# Display the DataFrame
print(df)

df.to_csv("wikipedia_results_15001_26728.csv", index=False)