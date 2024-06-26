from celery import Celery, group
import os
import requests
import time
import json
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from config import API_URL, GEMINI_URL, API_KEY, HEADERS

# Directory to store data
DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# Initialize logging
logging.basicConfig(level=logging.INFO)


# Celery configuration
app = Celery('tasks',
             broker=os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@localhost:5672//'),
             backend=os.getenv('CELERY_RESULT_BACKEND', 'rpc://'))


@app.task
def fetch_corporate_details(corporate_id):
    """
    Fetches details for a specific corporate by ID.
    """
    query = f"""
    query {{
        corporate(id: "{corporate_id}") {{
                name
                description
                logo_url
                hq_city
                hq_country
                website_url
                linkedin_url
                twitter_url
                startup_partners_count
                startup_partners {{
                    company_name
                    logo
                    city
                    website
                    country
                    theme_gd
                }}
                startup_themes
        }}
    }}
    """
    response = requests.post(API_URL, json={'query': query}, headers=HEADERS)
    if response.status_code == 200:
        return response.json()['data']['corporate']
    else:
        raise Exception(f"Failed to fetch details for corporate ID {corporate_id}")

@app.task
def fetch_all_corporates():
    """
    Fetches all corporate IDs.
    """
    logging.info("Fetching all corporates")
    query = """
    query Corporates($filters: CorporateFilters, $page: Int, $sortBy: String) {
    corporates(filters: $filters, page: $page, sortBy: $sortBy) {
        rows {
        id
        }
    }
    }
    """
    all_ids = []
    page = 1
    while True:
        variables = {
            "filters": {
                "hq_city": [],
                "industry": []
            },
            "page": page,
            "sortBy": None
        }
        response = requests.post(API_URL, json={'query': query, 'variables': variables}, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
        else:
            logging.error("Failed to fetch data: %s %s", response.status_code, response.text)
            break

        page_ids = [item['id'] for item in data['data']['corporates']['rows']]
        if not page_ids:
            break

        page += 1
        all_ids.extend(page_ids)
    logging.info("Total IDs fetched: %d", len(all_ids))
    return all_ids

@app.task
def process_results(results):
    """
    Processes the fetched corporate details and performs analysis.
    """
    file_path = os.path.join(DATA_FOLDER, "all_corporates.json")
    with open(file_path, 'w') as f:
        json.dump(results, f, indent=4)
    logging.info("Data saved.")
    return perform_analysis(results)

@app.task(bind=True)
def perform_complete_analysis(self, user_id):
    corporate_ids = fetch_all_corporates()
    
    # Dispatch tasks as a group
    group_result = group(fetch_corporate_details.s(cid) for cid in corporate_ids)()
    
    # Collect results using the group result
    results = group_result.get(disable_sync_subtasks=False)
    
    process_results(results)
    return "Finished"

@app.task
def perform_analysis(corporates):
    """
    Analyzes the corporate data by clustering descriptions.
    """
    logging.info("Starting analysis: Clustering the corporate data based on their descriptions using K-means.")
    descriptions = [corp['description'] for corp in corporates if 'description' in corp]
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(descriptions)

    k = 10
    kmeans = KMeans(n_clusters=k, random_state=42)
    clusters = kmeans.fit_predict(X)

    for i, corp in enumerate(corporates):
        if 'description' in corp:
            corp['cluster'] = int(clusters[i])
        else:
            corp['cluster'] = None

    key_phrases = extract_key_phrases(corporates, clusters, k)
    cluster_info = generate_cluster_info(corporates, key_phrases, clusters, k)

    file_path = os.path.join(DATA_FOLDER, "cluster_descriptions.json")
    with open(file_path, 'w') as f:
        json.dump(cluster_info, f, indent=4)
    logging.info("Cluster descriptions saved.")

    file_path = os.path.join(DATA_FOLDER, "corporates_with_clusters.json")
    with open(file_path, 'w') as f:
        json.dump(corporates, f, indent=4)
    logging.info("Corporates with clusters saved.")

    return corporates

def extract_key_phrases(corporates, clusters, k):
    """
    Extracts key phrases from corporate descriptions for each cluster.
    """
    key_phrases = []
    for i in range(k):
        cluster_descriptions = [corporates[j]['description'] for j in range(len(corporates)) if 'description' in corporates[j] and clusters[j] == i]
        if cluster_descriptions:
            text = ' '.join(cluster_descriptions)
            tfidf = TfidfVectorizer(stop_words='english', max_features=3)
            X = tfidf.fit_transform([text])
            keywords = tfidf.get_feature_names_out()
            key_phrases.append(keywords)
    return key_phrases

def generate_cluster_info(corporates, key_phrases, clusters, k):
    """
    Generates cluster information including titles and descriptions.
    """
    cluster_info = []
    for idx, phrases in enumerate(key_phrases):
        title_prompt = f"Generate a concise title for a corporate cluster focused on: {', '.join(phrases)}"
        title = generate_text(title_prompt)
        description_prompt = f"Write a short paragraph describing a company cluster based on these keywords: {', '.join(phrases)}"
        description = generate_text(description_prompt)
        cluster_info.append({
            "Cluster ID": idx + 1,
            "Title": title if title else "Untitled Cluster",
            "Description": description if description else "No description available"
        })
    return cluster_info

def generate_text(prompt):
    """
    Generates text using the GEMINI API.
    """
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    response = requests.post(f"{GEMINI_URL}?key={API_KEY}", headers=HEADERS, data=json.dumps(data))
    if response.status_code == 200:
        response_json = response.json()
        if 'candidates' in response_json and response_json['candidates']:
            return response_json['candidates'][0]['content']['parts'][0]['text']
    logging.error("Failed to generate text: %s %s", response.status_code, response.text)
    return None
