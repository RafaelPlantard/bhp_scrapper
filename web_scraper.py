from bs4 import BeautifulSoup
import requests
import json
import time
import datetime
import os

host = "www.revivalandreformation.org"
url = f"bhp/en/bible/1co/4"
payload = {}
go_to_next_page_automatically = True
headers = {
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Encoding': 'deflate',
  'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
  'Cookie': 'TAsessionID=77770798-71a1-4acd-ae2b-8bc8fb65608d|EXISTING; _ga_2VBYH6KEBQ=GS1.1.1735410945.6.1.1735410951.0.0.372092959; notice_behavior=implied|sa; _ga=GA1.1.1690987295.1734208656; _gid=GA1.2.1068337915.1735395223; cf_clearance=J5vU5pqH1UmaqkOlfPEX3s.27hDzMqk54hJzFVrrSxY-1735410946-1.2.1.1-JPJ14oyzUY3c1XXMJL.iyrcJTu4IpYKgrWwlecyxbmxn7NL7NVN887m_de2pJkowkeX2nBraERRIoD3cPXjZrnpyMgFa2YOdt52Y0NJmd7L6cVJQFjKabPhtlul2lkJOBMVk4xyBRJbGXDAXQWtljs.nhJtjGVQxb25Amd.6wOe4SlC0HY.vy676HsXzdDniLyQUQdSWOw7SE10fL28u7t5VifVSfyjAFOS3ksdt7WqDN3V20z0c1TtQPAbrgxYaXTRSGM2pZXPDCVCN37YA29GcbDqm9nJNPtP.jCOeiywqMBZSo4edejjTPAKSFUwhARiShNRc3Zz23tPefqgNZLuFMTpVwTm1.1s6whP0vTYg1GsNcmWDFLiip2reNv714VGka0Jv01ueyBA6KiAm6g; cmapi_cookie_privacy=permit_1|2|3|4|5_; cmapi_gtm_bl=; notice_gdpr_prefs=0|1|2|3|4:; notice_preferences=4:',
  'Priority': 'u=0, i',
  'Referer': url,
  'Sec-Fetch-Dest': 'document',
  'Sec-Fetch-Mode': 'navigate',
  'Sec-Fetch-Site': 'same-origin',
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15',
}

def extract_commentary(html_content):
    """
    Extract commentary from HTML content.
    
    Args:
        html_content (str): HTML content as string
        
    Returns:
        dict: Dictionary containing commentary text and author information
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the Commentary section
    commentary_header = soup.find('h3', string='Commentary')

    if not commentary_header:
        return None
    
    # Initialize variables
    commentary_text = []
    author_info = {}
    pagination = {}
    passage = {}
    date = {}

    # Find the previous and next chapter buttons
    pagination['previous'] = soup.find('a', {'class': 'btn', 'title': 'Previous Chapter'}).get('href', 'Not found')

    # Find the current chapter
    base_page = soup.find('meta', {'property': 'og:image'}).get('content', 'Not found')
    pagination['current'] = soup.find('meta', {'property': 'og:url'}).get('content', 'Not found').replace(base_page, '')
    pagination['url'] = soup.find('meta', {'property': 'og:url'}).get('content', 'Not found')

    # Find the next chapter
    pagination['next'] = soup.find('a', {'class': 'btn', 'title': 'Next Chapter'}).get('href', 'Not found')

    # Find the passage
    passage['verse'] = soup.find('h2', {'class': 'bible-header'}).get_text().strip()
    passage['chapter'] = soup.find('h2', {'class': 'font--secondary--xl theme--secondary-text-color', 'style': 'text-align:center;font-size:2.4rem;'}).get_text().strip()

    # Find the date
    date['original'] = soup.find('p', {'class': 'hide-mobile', 'style': 'text-align:center;'}).get_text().strip()

    # Format the date in the desired format (YYYY-MM-DD)
    # From December 15, 2024 to 20241215
    date['formatted'] = datetime.datetime.strptime(date['original'], '%B %d, %Y').strftime('%Y%m%d')

    # Get all paragraphs after the Commentary header until we find the author
    current_element = commentary_header.find_next('p')

    # Check if inside current_element there is a strong element
    if current_element.find('strong'):
        text = '\n'.join(current_element.stripped_strings)

        author_info['name'] = current_element.find_next('strong').get_text().strip()
        author_name_index = text.find(author_info['name'])
        author_info['position'] = text[author_name_index + len(author_info['name']) + 1:].split('\n')[0].strip()

    else:
        while current_element:
            if current_element.name == 'p':
                # Clean up the text and add to commentary
                text = ' '.join(current_element.stripped_strings)

                # remove newlines and tabs
                text = text.replace('\n', ' ').replace('\t', ' ')

                # remove extra spaces inside the text
                text = ' '.join(text.split())

                if text:
                    commentary_text.append(text + '\n')

            current_element = current_element.find_next()

            if current_element and current_element.name == 'strong':
                # Author info found, break the loop
                break

        # Extract author information if available
        if current_element:
            author_name = current_element
            if author_name:
                author_info['name'] = author_name.get_text().strip()
                # Get the position/title (it's in the next br tag's tail)
                position = current_element.get_text().replace(author_info['name'], '').strip()
                author_info['position'] = position
    
    return {
        'commentary': ''.join(commentary_text),
        'author': author_info,
        'pagination': {
            'previous': pagination['previous'],
            'next': pagination['next'],
            'current': pagination['current']
        },
        'date': {
            'original': date['original'],
            'formatted': date['formatted']
        },
        'bible_passage': {
            'verse': passage['verse'],
            'chapter': passage['chapter']
        }
    }

def go_to_next_page(path):
    if not go_to_next_page_automatically:
        return

    with open(path, 'r') as f:
        data = json.load(f)

    # Get the next chapter url from the pagination data
    next_chapter_url = data['pagination']['next']

    if next_chapter_url != 'Not found':
        download_page(next_chapter_url)

def get_path(url):
    parts = url.split('/')
    chapter = parts[-2] + '_' + parts[-1]
    path = f'commentary/{chapter}.json'

    return path

def download_page(url):
    url_complete = f"https://{host}/{url}"
    path = get_path(url_complete)

    # Download the page if it doesn't exist
    if os.path.exists(path):
        print(f'{path} already exists')

        return go_to_next_page(path)

    try:
        # try request until it succeeds increasing the delay value
        attemps = range(999)
        size = len(attemps)

        for i in attemps:
            try:
                # increase delay between requests
                if i > 0:
                    time.sleep(i)

                import http.client
                connection = http.client.HTTPSConnection(host)
                connection.request("GET", f"/{url}", headers=headers)
                response = connection.getresponse()
                if response.status != 200:
                    raise Exception(f"HTTP Error: {response.status} {response.reason}")
                response_data = response.read().decode("utf-8")
                connection.close()
                break
            except Exception as e:
                print(f"Retry attempt {i}: {e}")
                if i == size - 1:
                    raise

        # if the request fails after 10 attempts, raise an exception
        result = extract_commentary(response_data)

        if result:
            # save result to file
            with open(path, 'w') as f:
                # save json formatted pretty
                f.write(json.dumps(result, indent=2))

            print(f"Commentary extracted and saved to {path}")

            download_page(result['pagination']['next'])
        else:
            raise Exception("No commentary section found in the HTML content.")
            
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    # Create folder if it doesn't exist
    if not os.path.exists('commentary'):
        os.makedirs('commentary')

    download_page(url)

if __name__ == "__main__":
    main()
