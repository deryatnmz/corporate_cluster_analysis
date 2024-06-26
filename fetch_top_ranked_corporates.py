import requests
import json
import os

from config import API_URL

# Directory to store data
DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# Function to fetch top-ranked corporates
def fetch_top_ranked_corporates():
    """
    Fetches the IDs of the top-ranked corporates from the GraphQL API.

    Returns:
        list: A list of corporate IDs.
    """
    query = """
    query TopRankedCorporates {
        topRankedCorporates {
            id
        }
    }
    """
    response = requests.post(API_URL, json={'query': query})
    
    if response.status_code != 200:
        print(f"Failed to fetch top-ranked corporates. Status code: {response.status_code}")
        return []

    try:
        data = response.json()
        return [item['id'] for item in data['data']['topRankedCorporates']]
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing response: {e}")
        return []

# Function to fetch details for a specific corporate
def fetch_corporate_details(corporate_id):
    """
    Fetches details for a specific corporate by ID from the GraphQL API.

    Args:
        corporate_id (str): The ID of the corporate.

    Returns:
        dict: A dictionary containing corporate details, or None if the request fails.
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
    response = requests.post(API_URL, json={'query': query})
    
    if response.status_code != 200:
        print(f"Failed to fetch details for corporate ID {corporate_id}. Status code: {response.status_code}")
        return None

    try:
        return response.json()['data']['corporate']
    except KeyError as e:
        print(f"Key error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return None

# Main function to orchestrate the crawling
def main():
    """
    Main function to orchestrate the fetching of top-ranked corporates and their details.
    Saves the results to a JSON file.
    """
    corporates_ids = fetch_top_ranked_corporates()
    results = []

    for cid in corporates_ids:
        details = fetch_corporate_details(cid)
        if details:
            results.append(details)

    # Save results to a JSON file under the data folder
    file_path = os.path.join(DATA_FOLDER, "top_ranked_corporates.json")
    with open(file_path, 'w') as f:
        json.dump(results, f, indent=4)

    print("Data has been successfully saved to 'top_ranked_corporates.json'.")

if __name__ == '__main__':
    main()
