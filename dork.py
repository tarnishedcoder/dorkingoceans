# import requests
# from bs4 import BeautifulSoup
# import time
# import re

# def google_dork_and_save_links(website_url, filetype, output_filename="dorked_links.txt"):
#     """
#     Performs a Google dork search for a specified filetype on a given website
#     and saves the extracted links to a text file.
#     """
#     if website_url.startswith("http://") or website_url.startswith("https://"):
#         print("Error: Please provide the website URL without 'http://' or 'https://'.")
#         print("Example: 'www.envolvevision.com'")
#         return

#     dork_query = f"site:{website_url} filetype:{filetype}"
#     google_search_url = f"https://www.google.com/search?q={dork_query}"
#     found_links = set()  # Use a set to store unique links

#     print(f"Starting Google dork for: {dork_query}")
#     print(f"Results will be saved to: {output_filename}")

#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
#     }

#     try:
#         response = requests.get(google_search_url, headers=headers, timeout=10)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.text, 'html.parser')
#         url_pattern = re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)')

#         for a_tag in soup.find_all('a', href=True):
#             href = a_tag['href']
#             if f".{filetype}" in href.lower():
#                 if website_url in href:
#                     found_links.add(href)
#                 elif "url?q=" in href and "webcache.googleusercontent.com" not in href:
#                     clean_url = href.split("url?q=")[1].split("&sa=U")[0]
#                     if website_url in clean_url and f".{filetype}" in clean_url.lower():
#                         found_links.add(clean_url)
#     except requests.exceptions.RequestException as e:
#         print(f"Error making request to Google: {e}")
#         return

#     if found_links:
#         with open(output_filename, 'w') as f:
#             for link in sorted(list(found_links)):
#                 f.write(link + '\n')
#         print(f"\nSuccessfully found {len(found_links)} unique links and saved them to {output_filename}")
#     else:
#         print("\nNo links found for the given criteria.")

# if __name__ == "__main__":
#     target_website = input("Enter the target website (e.g., www.example.com, NO http/https): ")
#     target_filetype = input("Enter the filetype to search for (e.g., pdf, docx, xls) or type 'all' for any filetype: ")

#     if not target_website:
#         print("Website is required.")
#     else:
#         time.sleep(2)
#         output_path = r"C:\Users\PC\Desktop\bounties\results\dorked_links.txt"
#         # Pass None if user wants all filetypes
#         if target_filetype.strip().lower() == "all" or not target_filetype.strip():
#             google_dork_and_save_links(target_website, None, output_filename=output_path)
#         else:
#             google_dork_and_save_links(target_website, target_filetype, output_filename=output_path)


import requests
from bs4 import BeautifulSoup
import time
import re

def google_dork_and_save_links(website_url, filetype, output_filename="dorked_links.txt"):
    """
    Performs a Google dork search for a specified filetype on a given website
    and saves the extracted links to a text file.
    """
    if website_url.startswith("http://") or website_url.startswith("https://"):
        print("Error: Please provide the website URL without 'http://' or 'https://'.")
        print("Example: 'www.envolvevision.com'")
        return

    # Construct the dork query. If filetype is None, it means "all" and we don't add filetype to the query.
    if filetype:
        dork_query = f"site:{website_url} filetype:{filetype}"
    else:
        dork_query = f"site:{website_url}" # For "all" filetypes, just search the site

    google_search_url = f"https://www.google.com/search?q={dork_query}"
    found_links = set()  # Use a set to store unique links

    print(f"Starting Google dork for: {dork_query}")
    print(f"Results will be saved to: {output_filename}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(google_search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # This pattern is more for general URLs. The filetype check will filter.
        # url_pattern = re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)')

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # Only consider links relevant to the website and filetype, or any if filetype is None
            if website_url in href or "url?q=" in href:
                clean_url = href
                if "url?q=" in href:
                    clean_url = href.split("url?q=")[1].split("&sa=U")[0]
                
                # Ensure the link belongs to the target website and optionally matches the filetype
                if website_url in clean_url:
                    if filetype: # If a specific filetype is requested
                        if f".{filetype}" in clean_url.lower():
                            found_links.add(clean_url)
                    else :
                        found_links.add(clean_url)

    except requests.exceptions.RequestException as e:
        print(f"Error making request to Google: {e}")
        return

    if found_links:
        with open(output_filename, 'w') as f:
            for link in sorted(list(found_links)):
                f.write(link + '\n')
        print(f"\nSuccessfully found {len(found_links)} unique links and saved them to {output_filename}")
    else:
        print(f"\nNo links found for the given criteria (filetype: {filetype if filetype else 'all'}).")

if __name__ == "__main__":
    target_website = input("Enter the target website (e.g., www.example.com, NO http/https): ")
    target_filetype = input(
        "Enter the filetype to search for (e.g., pdf, docx, xls),\n"
        "or type 'all' to check common filetypes one by one,\n"
        "or 'any' for a broad search: "
    )

    if not target_website:
        print("Website is required.")
    else:
        output_base_path = r"C:\Users\PC\Desktop\bounties\results"
        common_filetypes = [
            "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv", "xml",
            "json", "sql", "zip", "rar", "7z", "tar", "gz", "log", "bak", "conf",
            "ini", "env", "php", "asp", "aspx", "jsp", "py", "sh", "bat", "ps1",
            "js", "css", "htm", "html", "yaml", "yml", "svg", "png", "jpg", "jpeg", "gif"
        ]

        if target_filetype.strip().lower() == "all":
            for ft in common_filetypes:
                output_path = fr"{output_base_path}\dorked_links_{ft}.txt"
                print(f"\n--- Searching for filetype: {ft} ---")
                google_dork_and_save_links(target_website, ft, output_filename=output_path)
        elif target_filetype.strip().lower() == "any" or not target_filetype.strip():
            output_path = fr"{output_base_path}\dorked_links_any.txt"
            google_dork_and_save_links(target_website, None, output_filename=output_path)
        else:
            output_path = fr"{output_base_path}\dorked_links_{target_filetype}.txt"
            google_dork_and_save_links(target_website, target_filetype, output_filename=output_path)