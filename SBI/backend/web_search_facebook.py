from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import quote_plus
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from pydantic import BaseModel,Field
from typing import List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import json
from typing import Optional
from langchain_openai import ChatOpenAI

###########################################################################################################
def fetch_all_bing_pages(query, driver, delay=5, max_pages=5):
    encoded_query = quote_plus(query)
    base_url = f"https://www.bing.com/search?q={encoded_query}"
    driver.get(base_url)
    time.sleep(delay)

    all_html = []
    current_page = 1

    while current_page <= max_pages:
        print(f" Capturing page {current_page}")

        # Scroll down to trigger lazy loads
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        html = driver.page_source
        all_html.append(html)

        try:
            # Wait for the next button to become clickable
            wait = WebDriverWait(driver, 5)
            next_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[@title='Next page']"))
            )
            
            try:
                # Try to scroll and click normally
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(0.5)
                next_button.click()
            except ElementClickInterceptedException:
                print(" Click intercepted. Using JS click.")
                driver.execute_script("arguments[0].click();", next_button)
            
            time.sleep(delay)
            current_page += 1

        except (NoSuchElementException, TimeoutException):
            print(" No more pages found or next button not available.")
            break

    return all_html


###########################################################################################################

def fetch_facebook_urls(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    links = soup.find_all('a')

    urls = []
    for link in links:
        href = link.get('href')
        if href and "facebook.com" in href:
            urls.append(href)

    return urls


###########################################################################################################

def filter_usernames(urls):

    usernames = []
    seen = set()

    for url in urls:
        path = urlparse(url).path.strip("/")
        parts = path.split("/")

        if parts[0] in ("reel", "p"):
            continue

        username = parts[0]
        if username and username not in seen:
            usernames.append(username)
            seen.add(username)

    usernames = usernames[:5]    
    return usernames

########################################################################################


def get_basic_info(user_id,driver):

    url = f"https://www.facebook.com/{user_id}/"
    driver.get(url)

    time.sleep(30)

    intro_html = driver.page_source
    
    # with open(os.path.join(output_dir,f'{user_id}_fb_intro.html'),'w',encoding='utf-8') as f:
    #     f.write(intro_html)


    soup = BeautifulSoup(intro_html, "html.parser")

    h1_tag = soup.findAll("h1")
    
    name = h1_tag[1]

    target_class = [
    "x193iq5w", "xeuugli", "x13faqbe", "x1vvkbs", "x1xmvt09", "x1lliihq",
    "x1s928wv", "xhkezso", "x1gmr53x", "x1cpjm7i", "x1fgarty", "x1943h6x",
    "xudqn12", "x3x7a5m", "x6prxxf", "xvq8zen", "xo1l8bm", "xzsf02u", "x1yc453h"
    ]

    # Helper to match exact class
    def match_exact_class(tag):
        return tag.name == "span" and sorted(tag.get("class", [])) == sorted(target_class)

    profile_container = soup.find("div", class_="x9f619 x1ja2u2z x78zum5 x2lah0s x1n2onr6 x1qughib x1qjc9v5 xozqiw3 x1q0g3np xv54qhq xf7dkkf xyamay9 x1ws5yxj xw01apr x4cne27 xifccgj")  # update this to your actual container

    # Step 2: Find all matching spans *only inside that div*
    profile_info=[]
    if profile_container:
        scoped_spans = profile_container.find_all(match_exact_class)
        for span in scoped_spans:
            profile_info.append(span.get_text(strip=True))
    else:
        print("Container div not found.")

    output={}
    output['name'] = name
    output['basic_info'] = profile_info
    output['html'] = intro_html

    return output

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
########################################################################################

def initialize_driver(username,password):
    # service = Service(executable_path="C:\\Users\\ASUS\\Downloads\\chromedriver-win32\\chromedriver.exe")
    # driver = webdriver.Chrome(service=service)

   

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    # Open Facebook login page
    driver.get("https://www.facebook.com/")

    # Wait for the page to load
    wait = WebDriverWait(driver, 10)

    # Enter username/email
    username_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    username_input.send_keys(username)

    # Enter password
    password_input = driver.find_element(By.ID, "pass")
    password_input.send_keys(password)

    # Click on login button
    login_button = driver.find_element(By.NAME, "login")
    login_button.click()

    # Optional: wait and print page title
    time.sleep(120)
    
    return driver

########################################################################################

def facebook_searcher(query, initial_metadata_user):

    load_dotenv()
    username = os.getenv('EMAIL_FB')
    password = os.getenv('PASSWORD_FB')
    driver = initialize_driver(username, password)

    all_html = fetch_all_bing_pages(query, driver)

    urls = []
    for html in all_html:
        urls.extend(fetch_facebook_urls(html))

    usernames = filter_usernames(urls)

    extracted_data = []
    for search_id in usernames:
        try:
            user_info = get_basic_info(search_id, driver)
            to_store_data = {
                'name': user_info['name'].text,
                'bio': user_info['basic_info'],
                'user_id': search_id
            }
            extracted_data.append(to_store_data)
            time.sleep(30)
        except Exception as e:
            print(f'Could not fetch for {search_id} due to error: {e}')
            continue

    # Setup LLM
    llm = ChatOpenAI(api_key=os.environ['OPEN_AI_API_KEY'], model='gpt-4.1')

    class llm_output_FB(BaseModel):
        user_id: Optional[str] = Field(description='The most suitable ID out of the entire list')
        reasoning: str = Field(description='Reason to select the account or reject all the accounts')

    sys_message = SystemMessage(content=(
        'Provided a Dictionary, which contains Facebook Bio, Location and Name of various users. '
        'Extract the most suitable ID which matches best with the initial metadata provided in the HumanMessage. '
        'Return only the ID in response — no additional data. If no ID matches to a significant extent, return "None".'
    ))

    human_message = HumanMessage(
        content=(
            f"Initial Metadata:\n"
            f"- Name: {initial_metadata_user['Actual_name']}\n"
            f"- Location: {initial_metadata_user['last_known_location']}\n"
            f"- Last Known Job: {initial_metadata_user['last_known_work']}\n"
            f"- Additional Data: {initial_metadata_user['extra_meta_data']}\n\n"
            f"Facebook Profiles:\n" +
            "\n".join([
                f"ID: {user['user_id']}\nName: {user['name']}\nBio: {user['bio']}\n"
                for user in extracted_data
            ])
        )
    )

    # Invoke the LLM
    response = llm.with_structured_output(llm_output_FB).invoke([sys_message, human_message])

    # Save full extracted info to JSON
    output_data = {
        "query": query,
        "initial_metadata": initial_metadata_user,
        "candidates": extracted_data,
        "llm_selected_id": response.user_id
    }

    # Create directory if needed
    os.makedirs("fb_extractions", exist_ok=True)
    file_name = query.replace(" ", "_")[:50] + ".json"
    file_path = os.path.join("fb_extractions", file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    print(f" Stored results to {file_path}")
    return response.user_id

def main():
    query='Lohit Pattnaik IITG Facebook'
    initial_metadata_user={}
    initial_metadata_user['Actual_name']='Lohit Pattnaik'
    initial_metadata_user['last_known_location']='Guwahati'
    initial_metadata_user['last_known_work']='DS at Nation with Namo'
    initial_metadata_user['extra_meta_data']='Studied at Visakhapatnam, presently at Goa'
    facebook_searcher(query,initial_metadata_user)


if __name__ == "__main__":
    main()   