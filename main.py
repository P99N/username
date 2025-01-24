import requests
import argparse
import concurrent.futures
from collections import OrderedDict
from colorama import init, Fore
import time
import random
from threading import Lock

# Initialize Colorama
init()

# Ordered dict of websites to check
WEBSITES = OrderedDict([
    ("Instagram", "https://www.instagram.com/{}"),
    ("Facebook", "https://www.facebook.com/{}"),
    ("YouTube", "https://www.youtube.com/user/{}"),
    ("Reddit", "https://www.reddit.com/user/{}"),
    ("GitHub", "https://github.com/{}"),
    ("Twitch", "https://www.twitch.tv/{}"),
    ("Pinterest", "https://www.pinterest.com/{}/"),
    ("TikTok", "https://www.tiktok.com/@{}"),
    ("Flickr", "https://www.flickr.com/photos/{}"),
    ("Snapchat", "https://www.snapchat.com/add/{}"),
    ("Twitter", "https://twitter.com/{}"),
    ("Discord", "https://discord.com/users/{}"),
    ("Spotify", "https://open.spotify.com/user/{}"),
    ("SoundCloud", "https://soundcloud.com/{}"),
    ("Netflix", "https://www.netflix.com/profile/{}"),
    ("LinkedIn", "https://www.linkedin.com/in/{}"),
    ("Tumblr", "https://www.tumblr.com/{}"),
    ("Steam", "https://steamcommunity.com/id/{}"),
    ("Vimeo", "https://vimeo.com/{}"),
    ("Quora", "https://www.quora.com/profile/{}"),


])

# custom dict check
SITE_CHECKS = {
    "Instagram": "page isn't available",
    "TikTok": "Couldn't find this account",
    "Reddit": "page not found",
    "YouTube": "this channel isn't available",
    "Facebook": "content isn't available right now",
    "GitHub": "find a user",
    "Twitch": "doesn't exist",
    "Pinterest": "couldn't find that page",
    "Flickr": "nobody seems to be here",
    "Twitter": "Sorry, that page doesn’t exist!",
    "LinkedIn": "This page doesn’t exist",
    "Tumblr": "There's nothing here",
    "Steam": "The specified profile could not be found",
    "Vimeo": "Sorry, we couldn’t find that page",

}


# Constants
REQUEST_DELAY = 2
MAX_RETRIES = 3

# Thread-safe data structures
last_request_times = {}
lock = Lock()

def check_username(website_name, website, username):
    """
    Check if the given username exists on the specified website.
    """
    url = website.format(username)
    retries = 0

    while retries < MAX_RETRIES:
        try:
            # Rate limiting with thread safety
            with lock:
                current_time = time.time()
                if website in last_request_times and current_time - last_request_times[website] < REQUEST_DELAY:
                    delay = REQUEST_DELAY - (current_time - last_request_times[website])
                    time.sleep(delay)
            
            # Make the HTTP request
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            response = requests.get(url, headers=headers, timeout=10)
            
            # Update the last request time
            with lock:
                last_request_times[website] = time.time()

            # Check response status
            if response.status_code == 200:
                if website_name in SITE_CHECKS:
                    not_found_phrase = SITE_CHECKS[website_name]
                    if not_found_phrase in response.text.lower():
                        return False
                return url 
            elif response.status_code == 404:
                return False
            else:
                retries += 1
                time.sleep(random.uniform(1, 3))  # Retry delay
        except requests.exceptions.RequestException:
            retries += 1
            time.sleep(random.uniform(1, 3))

    return False

def main():
    # Argument parser setup
    parser = argparse.ArgumentParser(description="Check if a username exists on various websites.")
    parser.add_argument('username', help='The username to check.')
    parser.add_argument('-o', '--output', help="Path to save the results to.")
    args = parser.parse_args()

    username = args.username
    output_file = args.output

    print(f"[+] Checking for username: {username}")

    results = OrderedDict()

    # Thread pool for concurrent checking
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(check_username, website_name, website_url, username): website_name for website_name, website_url in WEBSITES.items()}
        for future in concurrent.futures.as_completed(futures):
            website_name = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                print(f"{website_name} generated an exception: {exc}")
                result = False
            finally:
                results[website_name] = result
    
    # Display results
    print("\nResults:")
    for website, result in results.items():
        if result:
            print(f" {Fore.GREEN}{website}: Found ({result})")
        else:
            print(f" {Fore.RED}{website}: Not Found")

    # Save results to a file if specified
    if output_file:
        with open(output_file, "w") as f:
            for website, result in results.items():
                if result:
                    f.write(f"{website}: Found ({result})\n")
                else:
                    f.write(f"{website}: Not Found\n")
        print(f"[+] {Fore.GREEN}\nResults saved to {output_file}")

if __name__ == "__main__":
    main()
