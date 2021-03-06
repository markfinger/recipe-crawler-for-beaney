import requests
from bs4 import BeautifulSoup
import os
import csv

# This is a path to a file that contains the list of urls to check.
# Each url should be on a new line
URL_FILE = os.path.join(os.path.dirname(__file__), 'urls_to_crawl.txt')

# This is the file that we will write the output to
CSV_FILE = os.path.join(os.path.dirname(__file__), 'output.csv')

# We read in the content of URL_FILE
with open(URL_FILE, 'r') as url_file:
    urls_file_contents = url_file.read()

# We split each url by end of the line
urls_to_crawl = urls_file_contents.split('\n')

# We remove any empty lines and whitespace from the url file
urls_to_crawl = [url.strip() for url in urls_to_crawl if url and url.strip()]

# As we check each url, this is where we store the data for each
urls_crawled = []

# Now we output all the data to a CSV file, so you should be able to import it
# into a spreadsheet easily
with open(CSV_FILE, 'r') as csv_file:
    csv_reader = csv.reader(csv_file)
    for i, row in enumerate(csv_reader):
        if i != 0:
            urls_crawled.append({
                'url': row[0],
                'description': row[1],
                'image': row[2],
                'ignored': row[3]
            })

for obj in urls_crawled:
    if obj['url'] in urls_to_crawl:
        urls_to_crawl.remove(obj['url'])

# Now we output all the data to a CSV file, so you should be able to import it
# into a spreadsheet easily
with open(CSV_FILE, 'wb') as csv_file:
    csv_writer = csv.writer(csv_file)

    # We create the column titles
    csv_writer.writerow(['URL', 'DESCRIPTION', 'IMAGE', 'IGNORED'])

    # For every url we checked, write its data to the CSV file
    for data in urls_crawled:
        csv_writer.writerow([data['url'], data['description'], data['image'], data['ignored']])

    for url in urls_to_crawl:
        print('Checking: ' + url)

        data = {
            'url': url,
            'description': '',
            'image': '',
            'ignored': ''
        }

        # Add the data object to the list of urls crawled
        urls_crawled.append(data)

        # This sends a request to get the HTML document for the url
        response = requests.get(url)

        # We get the text for the request - in this case, the raw HTML
        html_text = response.text

        # We parse the HTML, so that we can search it for data
        parsed_html = BeautifulSoup(html_text, 'html.parser')

        # They don't serve the usual 404 code for a missing page, so we need
        # to look for a element that identifies missing pages
        oops_sorry = parsed_html.find('div', {'class': 'oops-sorry'})
        if oops_sorry:
            print('Ignoring: ' + url)
            data['ignored'] = 'ignored'
        else:
            # We look for the description field
            description = parsed_html.find('div', {'class': 'content-item quote-left-right clearfix'})

            # Pull out the text of the description field
            description_text = description.text.strip()

            # Remove any whitespace (empty spaces or new lines) from the description
            description_text = description_text.strip()

            # If there is content in the description, then we update the data object
            if description_text:
                data['description'] = description_text

            # We look for the image in the document
            image = parsed_html.find('img', {'class': 'print-thumb'})

            if image:
                # We pull out the value of its "src" attribute
                image_src = image.get('src')

                # The site has a weird thing were it assumes every recipe has an image, and
                # if it doesn't then it sets it to the placeholder image. So we have to
                # pretend to be a browser, so that we can check if the image exists
                image_response = requests.get(image_src, headers={'referer': url})
                if image_response.ok:
                    data['image'] = image_src
            elif parsed_html.find('div', {'class': 'content-item asset'}).find('div', {'id': 'playerCtn'}):
                data['image'] = 'VIDEO'
            else:
                raise Exception('Cannot resolve image or video')

        # Write its data to the CSV file
        csv_writer.writerow([data['url'], data['description'].encode('utf8'), data['image'], data['ignored']])
