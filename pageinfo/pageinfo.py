import requests
from bs4 import BeautifulSoup
from HTMLParser import HTMLParseError
import json
import re
from urlparse import urlparse, urljoin

#get title, description, favicon, twitter card, facebook open graph data
def get_meta(url=None, raw_html=None):
    domain = None
    if url:
        response = requests.get(url, timeout=3)
        if not response.status_code == 200:
            return json.dumps({"canonical": url, "error":"URL returned status"+str(response.status_code)})
        raw_html = response.text

        parsed_uri = urlparse( url )
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    
    data = {}
    data["raw_html"] = raw_html
    data["title"] = ""
    data["canonical"] = None
    data["description"] = None
    data["favicon"] = None
    data["facebook"] = {}
    data["twitter"] = {}

    try:
        soup = BeautifulSoup(raw_html)

        #get title
        if soup.title.string:
            data["title"] = soup.title.string
        #get canonical
        canonical = soup.find("link", rel="canonical")
        if canonical and domain:
            data["canonical"] = urljoin( domain, canonical["href"] )
        elif canonical:
            data["canonical"] = canonical["href"]
            parsed_uri = urlparse(data["canonical"])
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        #get favicon
        if soup.find("link", rel="shortcut icon"):
            icon_rel = soup.find("link", rel="shortcut icon")["href"]
            icon_abs = urljoin( url, icon_rel ) if url else icon_rel
            data["favicon"] = icon_abs
        elif domain:
            data["favicon"] = domain + 'favicon.ico'

        #get description
        if soup.find('meta', attrs={'name':'description'}):
            data["description"] = soup.find('meta', attrs={'name':'description'})["content"]

        #get facebook open graph data
        for attr in ('name', 'property'):
            tags = soup.findAll('meta', attrs={attr:re.compile("^og")})
            for tag in tags:
                tag_type = tag[attr]
                content_attr = tag.get('content') or tag.get('value')
                if content_attr:
                    data["facebook"][tag_type] = tag[content_attr]
                    if tag_type == "og:description" and data["description"] is None:
                        data["description"] = tag[content_attr]

        #get twitter card data
        for attr in ('name', 'property'):
            tags = soup.findAll('meta', attrs={attr:re.compile("^twitter")})
            for tag in tags:
                tag_type = tag[attr]
                content_attr = tag.get('content') or tag.get('value')
                if content_attr:
                    data["twitter"][tag_type] = tag[content_attr]
                    if tag_type == "twitter:description" and data["description"] is None:
                        data["description"] = tag[content_attr]
        # make sure canonical exists, use og as backup
        if not data['canonical'] or len(data['canonical']) == 0:
            if data['facebook'].has_key('og:url'):
                data['canonical'] = data['facebook']['og:url']
        if not data['canonical'] or len(data['canonical']) == 0:
            data['canonical'] = url

        return json.dumps(data)
    except HTMLParseError:
        return json.dumps({"canonical":url,"error":"Error parsing page data"})
