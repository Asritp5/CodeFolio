import requests
from bs4 import BeautifulSoup
import time
def get_leetcode_real_name(username):
    url = "https://leetcode.com/graphql/"
    payload = {
        "operationName": "getUserProfile",
        "variables": {"username": username},
        "query": """
        query getUserProfile($username: String!) {
            matchedUser(username: $username) {
                profile {
                    realName
                }
            }
        }
        """
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    data = response.json()
    try:
        return data['data']['matchedUser']['profile']['realName']
    except Exception:
        return None

def get_gfg_full_name(username):
    """
    Scrapes the public GeeksforGeeks profile page for the full name.
    If the name is separated by a hyphen (e.g., 'John Doe-MyCollege'), returns only the name part.
    """
    url = f"https://auth.geeksforgeeks.org/user/{username}/?t={int(time.time())}"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        # Try extracting from the <title> tag
        title_tag = soup.find("title")
        if title_tag and "|" in title_tag.text:
            full_name = title_tag.text.split("|")[0].strip()
            # If the name is separated by a hyphen, take only the first part
            if "-" in full_name:
                full_name = full_name.split("-")[0].strip()
            return full_name
        return None
    except Exception:
        return None

def get_codeforces_first_name(username):
    """
    Returns the first name from Codeforces API.
    Note: Codeforces API may not reflect profile updates instantly due to caching.
    """
    url = f"https://codeforces.com/api/user.info?handles={username}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("status") == "OK":
            user = data["result"][0]
            return user.get("firstName")
        return None
    except Exception:
        return None