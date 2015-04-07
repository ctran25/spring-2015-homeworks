#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import logging
import requests
from BeautifulSoup import BeautifulSoup


log = logging.getLogger(__name__)
log.setLevel(logging.ERROR)
loghandler = logging.StreamHandler(sys.stderr)
loghandler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
log.addHandler(loghandler)

base_url = "http://www.tripadvisor.com/"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36"

hotelURLs = []
hotelNames = []
excellent = []

def parse_hotel_page(hotelURL):
    hotelDictionary = {}
    for url in hotelURL:
        thisURL = base_url + url
        headers = {'User-Agent': user_agent}
        response = requests.get(thisURL, headers=headers)
        html = response.text.encode('utf-8')
        soup = BeautifulSoup(html)
        hotel = soup.find("h1", {"id" : "HEADING"}).text
        hotelDictionary[hotel] = {}

        ratingForm = soup.find("form", {"id" : "REVIEW_FILTER_FORM"})

        ''' TRAVEL RATINGS ==================================================='''
        travelRating = ratingForm.find("div", {"class" : "col2of2 composite"})
        ratingTitle = ratingForm.find("div", {"class" : "colTitle"}).text
        ratingRows = travelRating.findAll("div", {"class": "wrap row"})
        for row in ratingRows:
            rowTitle = row.find("span", {"class" : "rdoSet"}).text
            numRatings = row.find("span", {"class" : "compositeCount"}).text
            hotelDictionary[hotel][rowTitle] = int(numRatings.replace(',', ''))

        ''' SEE REVIEWS FOR =================================================='''
        tripTypes = ratingForm.find("div", {"class" : "trip_type"})
        reviewsFor = tripTypes.find("div", {"class" : "colTitle"}).text
        # hotelDictionary[hotel][reviewsFor] = {}

        familyRow = tripTypes.find("div", {"class" : "segment segment1"})
        family = tripTypes.find("div", {"class" : "sprite-tt-family-active-refresh filter_selection taLnk hvrIE6 ulBlueLinks"}).text
        familyCount = familyRow.find("div", {"class" : "value"}).text
        hotelDictionary[hotel][family] = int(familyCount.replace(',', ''))

        couplesRow = tripTypes.find("div", {"class" : "segment segment2"})
        couple = tripTypes.find("div", {"class" : "sprite-tt-couples-active-refresh filter_selection taLnk hvrIE6 ulBlueLinks"}).text
        coupleCount = couplesRow.find("div", {"class" : "value"}).text
        hotelDictionary[hotel][couple] = int(coupleCount.replace(',', ''))

        soloRow = tripTypes.find("div", {"class" : "segment segment3"})
        solo = tripTypes.find("div", {"class" : "sprite-tt-solo-active-refresh filter_selection taLnk hvrIE6 ulBlueLinks"}).text
        soloCount = soloRow.find("div", {"class" : "value"}).text
        hotelDictionary[hotel][solo] = int(soloCount.replace(',', ''))

        businessRow = tripTypes.find("div", {"class" : "segment segment4"})
        business = tripTypes.find("div", {"class" : "sprite-tt-business-active-refresh filter_selection taLnk hvrIE6 ulBlueLinks"}).text
        businessCount = businessRow.find("div", {"class" : "value"}).text
        hotelDictionary[hotel][business] = int(businessCount.replace(',', ''))

        ''' RATING SUMMARY ===================================================='''
        summary = ratingForm.find("div", {"id" : "SUMMARYBOX"})
        ratingSummaryTitle = summary.find("span", {"class" : "conceptsHeading"}).text
        # print ratingSummaryTitle
        locationRow = summary.findAll("li")
        for row in locationRow:
            rowTitle = row.find("div", {"class" : "name"}).text
            sRating = row.find("img", {"src" : "http://e2.tacdn.com/img2/x.gif"})
            hotelDictionary[hotel][rowTitle] = float(sRating['alt'].split()[0])
    return hotelDictionary


def get_city_page(city, state, datadir):
    """ Returns the URL of the list of the hotels in a city. Corresponds to
    STEP 1 & 2 of the slides.

    Parameters
    ----------
    city : str

    state : str

    datadir : str


    Returns
    -------
    url : str
        The relative link to the website with the hotels list.

    """
    # Build the request URL
    url = base_url + "city=" + city + "&state=" + state
    # Request the HTML page
    headers = {'User-Agent': user_agent}
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    with open(os.path.join(datadir, city + '-tourism-page.html'), "w") as h:
        h.write(html)

    # Use BeautifulSoup to extract the url for the list of hotels in
    # the city and state we are interested in.

    # For example in this case we need to get the following href
    # <li class="hotels twoLines">
    # <a href="/Hotels-g60745-Boston_Massachusetts-Hotels.html" data-trk="hotels_nav">...</a>
    soup = BeautifulSoup(html)
    li = soup.find("li", {"class": "hotels twoLines"})
    city_url = li.find('a', href=True)
    return city_url['href']


def get_hotellist_page(city_url, page_count, city, datadir='data/'):
    """ Returns the hotel list HTML. The URL of the list is the result of
    get_city_page(). Also, saves a copy of the HTML to the disk. Corresponds to
    STEP 3 of the slides.

    Parameters
    ----------
    city_url : str
        The relative URL of the hotels in the city we are interested in.
    page_count : int
        The page that we want to fetch. Used for keeping track of our progress.
    city : str
        The name of the city that we are interested in.
    datadir : str, default is 'data/'
        The directory in which to save the downloaded html.

    Returns
    -------
    html : str
        The HTML of the page with the list of the hotels.
    """
    url = base_url + city_url
    # Sleep 2 sec before starting a new http request
    time.sleep(2)
    # Request page
    headers = { 'User-Agent' : user_agent }
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    # Save the webpage
    with open(os.path.join(datadir, city + '-hotelist-' + str(page_count) + '.html'), "w") as h:
        h.write(html)
    return html

def parse_hotellist_page(html):
    """Parses the website with the hotel list and prints the hotel name, the
    number of stars and the number of reviews it has. If there is a next page
    in the hotel list, it returns a list to that page. Otherwise, it exits the
    script. Corresponds to STEP 4 of the slides.

    Parameters
    ----------
    html : str
        The HTML of the website with the hotel list.

    Returns
    -------
    URL : str
        If there is a next page, return a relative link to this page.
        Otherwise, exit the script.
    """
    soup = BeautifulSoup(html)
    # Extract hotel name, star rating and number of reviews
    hotel_boxes = soup.findAll('div', {'class' :'listing wrap reasoning_v5_wrap jfy_listing p13n_imperfect'})
    if not hotel_boxes:
        log.info("#################################### Option 2 ######################################")
        hotel_boxes = soup.findAll('div', {'class' :'listing_info jfy'})
    if not hotel_boxes:
        log.info("#################################### Option 3 ######################################")
        hotel_boxes = soup.findAll('div', {'class' :'listing easyClear  p13n_imperfect'})

    for hotel_box in hotel_boxes:
        hotel_address = hotel_box.find("a", {"class" : "property_title"})['href']
        hotelURLs.append(hotel_address)

        hotel_name = hotel_box.find("a", {"target" : "_blank"}).find(text=True)
        hotelNames.append(hotel_name.strip())
        log.info("Hotel name: %s" % hotel_name.strip())

        stars = hotel_box.find("img", {"class" : "sprite-ratings"})
        if stars:
            log.info("Stars: %s" % stars['alt'].split()[0])

        num_reviews = hotel_box.find("span", {'class': "more"}).findAll(text=True)
        if num_reviews:
            log.info("Number of reviews: %s " % [x for x in num_reviews if "review" in x][0].strip())

    # Get next URL page if exists, otherwise exit
    div = soup.find("div", {"class" : "pagination paginationfillbtm"})
    # check if this is the last page
    if div.find('span', {'class' : 'guiArw pageEndNext'}):
        log.info("We reached last page")
        sys.exit()
    # If not, return the url to the next page
    hrefs = div.findAll('a')
    for href in hrefs:
        cclass = href['class'].strip()
        if cclass == 'guiArw sprite-pageNext':
            return href['href']

def returnDictionary():
    hotelDictionary = dict.fromkeys(hotelNames)
    return hotelDictionary

def scrape_hotels(city, state, datadir='data/'):
    """Runs the main scraper code

    Parameters
    ----------
    city : str
        The name of the city for which to scrape hotels.

    state : str
        The state in which the city is located.

    datadir : str, default is 'data/'
        The directory under which to save the downloaded html.
    """

    # Get current directory
    current_dir = os.getcwd()
    # Create datadir if does not exist
    if not os.path.exists(os.path.join(current_dir, datadir)):
        os.makedirs(os.path.join(current_dir, datadir))

    # Get URL to obtaint the list of hotels in a specific city
    city_url = get_city_page(city, state, datadir)
    c = 0
    while(True):
        c += 1
        html = get_hotellist_page(city_url, c, city, datadir)
        city_url = parse_hotellist_page(html)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape tripadvisor')
    parser.add_argument('-datadir', type=str,
                        help='Directory to store raw html files',
                        default="data/")
    parser.add_argument('-state', type=str,
                        help='State for which the hotel data is required.',
                        required=True)
    parser.add_argument('-city', type=str,
                        help='City for which the hotel data is required.',
                        required=True)

    args = parser.parse_args()
    scrape_hotels(args.city, args.state, args.datadir)