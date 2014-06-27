import requests
from bs4 import BeautifulSoup
from HTMLParser import HTMLParseError
import json
import re
from urlparse import urlparse
from urlparse import urljoin

def validate_url(input_str):
    parsed_uri = urlparse( input_str )
    if parsed_uri.scheme and parsed_uri.netloc:
        return True
    return False

def get_html(url_or_html):
    if validate_url(url_or_html):
        response = requests.get(url_or_html, timeout=3)
        if not response.status_code == 200:
            return None
        html = response.text
    else:
        html = url_or_html
    return html

def get_pageinfo(url_or_html):
    html = get_html(url_or_html)
    return json.dumps(get_meta(html))

#get title, description, favicon, twitter card, facebook open graph data
def get_meta(html):
    
    data = {}
    data["title"] = ""
    data["canonical"] = None
    data["description"] = None
    data["favicon"] = None
    data["facebook"] = {}
    data["twitter"] = {}

    try:
        soup = BeautifulSoup(html)

        #get title
        if soup.title.string:
            data["title"] = soup.title.string
        #get canonical
        canonical = soup.find("link", rel="canonical")
        if canonical:
            data["canonical"] = canonical['href']
        #get favicon
        parsed_uri = urlparse( url )
        if soup.find("link", rel="shortcut icon"):
            icon_rel = soup.find("link", rel="shortcut icon")["href"]
            icon_abs = urljoin( url, icon_rel )
            data["favicon"] = icon_abs
        else:
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
            data["favicon"] = domain + 'favicon.ico'

        #get description
        if soup.find('meta', attrs={'name':'description'}):
            data["description"] = soup.find('meta', attrs={'name':'description'})["content"]

        #get facebook open graph data
        if soup.findAll('meta', {"property":re.compile("^og")}):
            for tag in soup.findAll('meta', {"property":re.compile("^og")}):
                tag_type = tag['property']
                data["facebook"][tag_type] = tag['content']
                if tag_type == "og:description" and data["description"] is None:
                    data["description"] = tag["content"]

        #get twitter card data
        if soup.findAll('meta', attrs={'name':re.compile("^twitter")}):
            for tag in soup.findAll('meta', attrs={'name':re.compile("^twitter")}):
                tag_type = tag['name']
                if 'content' in tag.attrs:
                    data["twitter"][tag_type] = tag['content']
                    if tag_type == "twitter:description" and data["description"] is None:
                        data["description"] = tag["content"]
        # make sure canonical exists, use og as backup
        if not data['canonical'] or len(data['canonical']) == 0:
            if data['facebook'].has_key('og:url'):
                data['canonical'] = data['facebook']['og:url']
        if not data['canonical'] or len(data['canonical']) == 0:
            data['canonical'] = url

        return data
    except HTMLParseError:
        return {"canonical":url,"error":"Error parsing page data"}
