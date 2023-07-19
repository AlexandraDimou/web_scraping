# Importing the necessary libraries
from playwright.sync_api import sync_playwright
import random
import time
from pymongo import MongoClient

### This scraper extracts data from this site:
site = 'https://podcastcharts.byspotify.com/'

# User agents and proxy
user_agents_old = [
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246',
  'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9',
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36',
  'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
]

proxy = {
    "server": "#####",
    "username": "#####",
    "password": "######",
}



# Save in MongoDatabase
client = MongoClient(
        "mongodb+srv://doadmin:###########"
    )
# For podcasts
def savePodcastsInMongo(PodcastRank,PodcastTitle,PodcastAuthor,PodcastArrow,):
    itemToSave = {
        "ranking": PodcastRank,
        "podcast_title": PodcastTitle,
        "author": PodcastAuthor,
        "arrow": PodcastArrow,
        "date": round(time.time()),
        }
    
    client["meta"]["podcast_rankings"].insert_one(itemToSave)

# For episodes  
def saveEpisodesInMongo(EpisodeRank,EpisodeTitle,EpisodeAuthor,EpisodeArrow,):
    itemToSave = {
        "ranking": EpisodeRank,
        "episode_title": EpisodeTitle,
        "author": EpisodeAuthor,
        "arrow": EpisodeArrow,
        "date": round(time.time()),
        }
    
    client["meta"]["podcast_episode_rankings"].insert_one(itemToSave)

# Scrapers
def podcasts_scraper(podcasts_link):    
    with sync_playwright() as p:
        
        browser = p.firefox.launch(headless = True,proxy={"server": "per-context"},)
        
        context = browser.new_context(viewport={'width':1600,'height':900},ignore_https_errors=True, user_agent=random.choice(user_agents_old),
                                        default_browser_type='chrome',
                                        proxy= proxy,
                                        )
        page = context.new_page()
         
        page.goto(podcasts_link, timeout=0, wait_until='load')
        
        page.wait_for_timeout(3000)
        
        #For cookies (accept cookies)
        try:
            page.get_by_role("button", name="Accept Cookies").click()
        except:
            pass
        
        # Select the country
        country_selection = page.query_selector('div[class="pl-2 md:pl-0 flex justify-center items-center text-accent0 hover:text-white transition-color duration-500 leading-none pt-2 md:pt-0 pointer-events-auto"]')
        country_selection.query_selector('div[class="transform mr-2 rotate-0 translate-y-0 w-auto transition duration-500 text-right origin-center absolute right-3 font-mono"]').click()
        page.wait_for_timeout(5000)
        country_container = country_selection.query_selector('div[class="absolute origin-top-left w-full transform transition-all ease-in-out duration-500 z-0 mr-0 md:mr-32 pointer-events-auto opacity-100 translate-y-0 z-30 "]')
        country_list = country_container.query_selector('ul[class="jsx-7b679aec34536d50 overflow-x-hidden overflow-y-auto"]')
        countries = country_list.query_selector_all('li')
        for country in countries:
            if country.query_selector('span[class="jsx-7b679aec34536d50 false"]').inner_text() == 'Denmark':
                country.click()
        
        page.wait_for_timeout(3000)
        
        # Scrolling
        try:
            page.evaluate(
                """
                var intervalID = setInterval(function () {
                    var scrollingElement = (document.scrollingElement || document.body);
                    scrollingElement.scrollTop += 200;}, 200);
                """
                )
            prev_height = None
            while True:
                
                curr_height = page.evaluate('(window.innerHeight + window.scrollY)')
                
                if not prev_height:
                    prev_height = curr_height
                    time.sleep(5)
                elif prev_height == curr_height:
                    page.evaluate('clearInterval(intervalID)')
                    break
                else:
                    prev_height = curr_height
                    time.sleep(5)
        except Exception as e:
            print(e)
            print('problem with scrolling')
        
        
        # Scrape info for each podcast
        podcasts_container = page.query_selector('div[class="List_list__0oF1W List_list__default__cJtSV overflow-hidden"]')
        pods = podcasts_container.query_selector_all('div[class="Show_show__jq9gl Show_show__default__2x1b_ "]')   
        for pd in pods:
            pd.hover()
            info = pd.query_selector('div[class="flex-grow"]')
            rank = pd.query_selector('div[class="flex pl-6 w-10 md:w-20 h-20 items-center justify-center  text-accent0 text-center"]').query_selector('div[class="Rank_rank__75HTS Rank_rank__default__YGig9 text-lg md:text-3xl"]').inner_text()
            title = info.query_selector('div[class="mt-1 md:mt-0 w-full lg:w-3/4 text-left text-sm md:text-xl md:pt-1 leading-tight md:leading-none text-accent0"]').query_selector('span[width="800"]').inner_text()
            author = info.query_selector('div[class="w-full md:w-1/2 text-white uppercase text-left font-light tracking-wide pt-1 text-2xs md:text-sm"]').query_selector('span[width="800"]').inner_text()
            try:
                arrow = pd.query_selector('div[class="relative"]').query_selector('img').get_attribute('alt')
            except:
                arrow = 'same'
            savePodcastsInMongo(rank, title, author, arrow)
        page.wait_for_timeout(3000)
        
        page.close()
        browser.close()
        

def episodes_scraper(podcasts_link):
        
    with sync_playwright() as p:
        
        browser = p.firefox.launch(headless = True,proxy={"server": "per-context"},)
        
        context = browser.new_context(viewport={'width':1600,'height':900},ignore_https_errors=True, user_agent=random.choice(user_agents_old),
                                        default_browser_type='chrome',
                                        proxy= proxy,
                                        )
        page = context.new_page()
         
        page.goto(podcasts_link, timeout=0, wait_until='load')
        
        page.wait_for_timeout(3000)
        #For cookies
        try:
            page.get_by_role("button", name="Accept Cookies").click()
        except:
            pass
        
        # Country selection
        country_selection = page.query_selector('div[class="pl-2 md:pl-0 flex justify-center items-center text-accent0 hover:text-white transition-color duration-500 leading-none pt-2 md:pt-0 pointer-events-auto"]')
        country_selection.query_selector('div[class="transform mr-2 rotate-0 translate-y-0 w-auto transition duration-500 text-right origin-center absolute right-3 font-mono"]').click()
        page.wait_for_timeout(5000)
        country_container = country_selection.query_selector('div[class="absolute origin-top-left w-full transform transition-all ease-in-out duration-500 z-0 mr-0 md:mr-32 pointer-events-auto opacity-100 translate-y-0 z-30 "]')
        country_list = country_container.query_selector('ul[class="jsx-7b679aec34536d50 overflow-x-hidden overflow-y-auto"]')
        countries = country_list.query_selector_all('li')
        for country in countries:
            if country.query_selector('span[class="jsx-7b679aec34536d50 false"]').inner_text() == 'Denmark':
                country.click()
        
        page.wait_for_timeout(5000)
        
        # Category selection
        category_selection = page.query_selector('div[class="CategoryTitle_category_title__qmyUe CategoryTitle_category_title__default__txDqR bg-blue-1e text-center cursor-pointer z-10"]')
        category_selection.query_selector('div[class="transform mr-2 rotate-0 translate-y-0 w-auto transition duration-500 text-right origin-center absolute right-3 font-mono"]').click()
        page.wait_for_timeout(4000)
        category_container = category_selection.query_selector('div[class="jsx-7b679aec34536d50 Categories_categories__DOcrI Categories_categories__default__XJQc6 overflow-x-hidden w-full overflow-y-auto h-235 md:h-full"]')
        category_list = category_container.query_selector('ul[class="jsx-7b679aec34536d50 categories-ul overflow-x-hidden overflow-y-auto grid grid-cols-1"]')
        categories = category_list.query_selector_all('li')
        for category in categories:
            if category.inner_text() == 'Top Episodes':
                category.click()
           
                
        page.wait_for_timeout(5000)
        
        # Scrolling
        try:
            page.evaluate(
                """
                var intervalID = setInterval(function () {
                    var scrollingElement = (document.scrollingElement || document.body);
                    scrollingElement.scrollTop += 200;}, 200);
                """
                )
            prev_height = None
            while True:
                
                curr_height = page.evaluate('(window.innerHeight + window.scrollY)')
                if not prev_height:
                    prev_height = curr_height
                    time.sleep(5)
                elif prev_height == curr_height:
                    page.evaluate('clearInterval(intervalID)')
                    break
                else:
                    prev_height = curr_height
                    time.sleep(5)
        except Exception as e:
            print(e)
            print('problem with scrolling')
        
        # Scrape info for each episode
        episodes_container = page.query_selector('div[class="List_list__0oF1W List_list__default__cJtSV overflow-hidden"]')
        eps = episodes_container.query_selector_all('div[class="Show_show__jq9gl Show_show__default__2x1b_ "]')   
        for ep in eps:
            ep.hover()
            info = ep.query_selector('div[class="flex-grow"]')
            rank = ep.query_selector('div[class="flex pl-6 w-10 md:w-20 h-20 items-center justify-center  text-accent0 text-center"]').query_selector('div[class="Rank_rank__75HTS Rank_rank__default__YGig9 text-lg md:text-3xl"]').inner_text()
            title = info.query_selector('div[class="mt-1 md:mt-0 w-full lg:w-3/4 text-left text-sm md:text-xl md:pt-1 leading-tight md:leading-none text-accent0"]').query_selector('span[width="800"]').inner_text()
            author = info.query_selector('div[class="w-full md:w-1/2 text-white uppercase text-left font-light tracking-wide pt-1 text-2xs md:text-sm"]').query_selector('span[width="800"]').inner_text()
            try:
                arrow = ep.query_selector('div[class="relative"]').query_selector('img').get_attribute('alt')
            except:
                arrow = 'same'
            saveEpisodesInMongo(rank, title, author, arrow)
        page.wait_for_timeout(3000)
        
        page.close()
        browser.close()




# Scraping
podcasts_scraper(site)

time.sleep(5)

episodes_scraper(site)
