import time
import asyncio

from requests_html import AsyncHTMLSession
from requests_html import HTMLSession
from datetime import datetime
from dateutil import tz
from tabulate import tabulate

def setup(betfair_url, tab_url, sportsbet_url):
    _, _, id = betfair_url.partition("/market/")

    try:
        id = id.split('?')[0]
    except:
        pass

    betfair_url = 'https://ero.betfair.com.au/www/sports/exchange/readonly/v1/bymarket?_ak=nzIFcwyWhrlwYMrh&alt=json&currencyCode=AUD&locale=en_GB&marketIds=' + id + '&rollupLimit=25&rollupModel=STAKE&types=MARKET_STATE,MARKET_RATES,MARKET_DESCRIPTION,EVENT,RUNNER_DESCRIPTION,RUNNER_STATE,RUNNER_EXCHANGE_PRICES_BEST,RUNNER_METADATA,MARKET_LICENCE,MARKET_LINE_RANGE_INFO'
    
    place_market = id[0:2] + str(int(id[2:]) + 1)
    place_market_alt = id[0:2] + str(int(id[2:]) - 1)
    betfairPlace_url = 'https://ero.betfair.com.au/www/sports/exchange/readonly/v1/bymarket?_ak=nzIFcwyWhrlwYMrh&alt=json&currencyCode=AUD&locale=en_GB&marketIds=' + place_market + '&rollupLimit=25&rollupModel=STAKE&types=MARKET_STATE,MARKET_RATES,MARKET_DESCRIPTION,EVENT,RUNNER_DESCRIPTION,RUNNER_STATE,RUNNER_EXCHANGE_PRICES_BEST,RUNNER_METADATA,MARKET_LICENCE,MARKET_LINE_RANGE_INFO'
    betfairPlace_url_alt = 'https://ero.betfair.com.au/www/sports/exchange/readonly/v1/bymarket?_ak=nzIFcwyWhrlwYMrh&alt=json&currencyCode=AUD&locale=en_GB&marketIds=' + place_market_alt + '&rollupLimit=25&rollupModel=STAKE&types=MARKET_STATE,MARKET_RATES,MARKET_DESCRIPTION,EVENT,RUNNER_DESCRIPTION,RUNNER_STATE,RUNNER_EXCHANGE_PRICES_BEST,RUNNER_METADATA,MARKET_LICENCE,MARKET_LINE_RANGE_INFO'

    tab_split = tab_url.split('/')
    if len(tab_split[-1]) > 2:
        tab_split.pop()
    tab_url = 'https://api.beta.tab.com.au/v1/tab-info-service/racing/dates/' + tab_split[-5] + '/meetings/' + tab_split[-2]+ '/' + tab_split[-3] + '/races/' + tab_split[-1] + '?returnPromo=true&returnOffers=true&jurisdiction=QLD'

    urls = {
        'betfair' : betfair_url,
        'betfairPlace' : betfairPlace_url,
        'betfairPlaceAlt' : betfairPlace_url_alt,
        'tab' : tab_url,
        'sportsbet' : sportsbet_url
    }
    return(urls)
    
def raceinfo(urls):
    session = HTMLSession()
    s_betfair = session.get(urls['betfair'])
    results = s_betfair.json()

    venue = results.get('eventTypes')[0].get('eventNodes')[0].get('event').get('venue')
    race_number = results.get('eventTypes')[0].get('eventNodes')[0].get('marketNodes')[0].get('description').get('marketName')
    race_time = results.get('eventTypes')[0].get('eventNodes')[0].get('marketNodes')[0].get('description').get('marketTime')[11:16]

    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()

    utc = datetime.strptime(race_time, "%H:%M")
    utc = utc.replace(tzinfo = from_zone)
    central = utc.astimezone(to_zone)
    race_time = central.strftime("%H:%M")

    information = {
        'venue' : venue,
        'race_number' : race_number,
        'race_time' : race_time
    }

    return information

async def betfair(session, urls):
    s_betfair = await session.get(urls['betfair'])
    results = s_betfair.json()

    all_runners = {}

    runners = results.get('eventTypes')[0].get('eventNodes')[0].get('marketNodes')[0].get('runners')

    for runner in runners:
        horse = {}
        try:
            number = int(str(runner.get('description').get('runnerName')).split(". ")[0])
            name = str(runner.get('description').get('runnerName')).split(". ")[1]
            try:
                price = float(runner.get('exchange').get('availableToLay')[0].get('price'))
            except:
                continue
            horse['number'] = number
            horse['name'] = name
            horse['price'] = price

            all_runners[number] = horse
        except:
            return("Betfair error occurred.")

    return all_runners

async def betfairplace(session, urls):
    s_betfair = await session.get(urls['betfair'])
    s_betfairplace = await session.get(urls['betfairPlace'])
    s_betfairplacealt = await session.get(urls['betfairPlaceAlt'])

    betfair = s_betfair.json()
    place = s_betfairplace.json()
    altplace = s_betfairplacealt.json()

    try:
        runners = place.get('eventTypes')[0].get('eventNodes')[0].get('marketNodes')[0].get('runners')
        if (str(betfair.get('eventTypes')[0].get('eventNodes')[0].get('marketNodes')[0].get('description').get('raceNumber')) != str(place.get('eventTypes')[0].get('eventNodes')[0].get('marketNodes')[0].get('description').get('raceNumber'))) or (str(betfair.get('eventTypes')[0].get('eventNodes')[0].get('event').get('eventName')) != str(place.get('eventTypes')[0].get('eventNodes')[0].get('event').get('eventName'))) or (str(place.get('eventTypes')[0].get('eventNodes')[0].get('marketNodes')[0].get('description').get('marketType')) != 'PLACE'):
            runners = altplace.get('eventTypes')[0].get('eventNodes')[0].get('marketNodes')[0].get('runners')
    except:
        runners = altplace.get('eventTypes')[0].get('eventNodes')[0].get('marketNodes')[0].get('runners')

    all_runners = {}

    for runner in runners:
        horse = {}
        try:
            number = int(str(runner.get('description').get('runnerName')).split(". ")[0])
            name = str(runner.get('description').get('runnerName')).split(". ")[1]
            try:
                price = float(runner.get('exchange').get('availableToLay')[0].get('price'))
            except:
                continue
            horse['number'] = number
            horse['name'] = name
            horse['price'] = price

            all_runners[number] = horse
        except:
            return("Betfair place error occurred.")

    return all_runners

async def tab(session, urls):
    s_tab = await session.get(urls['tab'])
    results = s_tab.json()

    all_runners = {}

    runners = results.get('runners')

    for runner in runners:
        horse = {}
        try:
            if runner.get('fixedOdds').get('bettingStatus') == 'Open':
                number = int(runner.get('runnerNumber'))
                name = str(runner.get('runnerName')).replace("'", "").title()
                price = float(runner.get('fixedOdds').get('returnWin'))

                horse['number'] = number
                horse['name'] = name
                horse['price'] = price

                all_runners[number] = horse
        except:
            return("TAB error occurred.")

    return all_runners

async def sportsbet(session, urls):
    s_sportsbet = await session.get(urls['sportsbet'])

    names = s_sportsbet.html.find('div.outcomeName_f18x6kvm')
    prices = s_sportsbet.html.xpath('//div[@data-automation-id="racecard-outcome-0-L-price"]')

    all_runners = {}

    for name, price in zip(names, prices):
        horse = {}
        try:
            number = int(name.text.split(u'\xa0')[0].split('. ')[0])
            name = name.text.split(u'\xa0')[0].split('. ')[1]
            name = name.replace("'", "").title()
            price = float(price.text.split(u'\n')[0])

            horse['number'] = number
            horse['name'] = name
            horse['price'] = price

            all_runners[number] = horse
        except:
            return("Sportsbet error occurred.")

    return all_runners

async def main(urls):
    session = AsyncHTMLSession()

    tasks = (
        betfair(session, urls),
        betfairplace(session, urls),
        tab(session, urls),
        sportsbet(session, urls)
        )

    return await asyncio.gather(*tasks)

def fetch(info, urls):
    results = asyncio.run(main(urls))
    return {
        'info' : info,
        'betfair' : results[0],
        'betfairplace' : results[1],
        'tab' : results[2],
        'sportsbet' : results[3]
    }

def transform(info):
    results = []

    race_time = info['info']['race_time']
    start_time = datetime.strptime(info['info']['race_time'] + ":00", "%H:%M:%S")
    current_time = datetime.strptime(datetime.now().strftime("%H:%M:%S"), "%H:%M:%S")

    delta = start_time - current_time
    countdown = str(delta)

    race_name = info['info']['venue'] + " " + info['info']['race_number']

    try:
        for i in info['betfair'].values():
            for j in info['tab'].values():
                for k in info['sportsbet'].values():
                    for l in info['betfairplace'].values():
                        if i['number'] == j['number'] == k['number'] == l['number']:                            
                            if j['price'] >= k['price']:
                                bookie = 'Tab'
                                best_price = j['price']
                                xr = (50 * (j['price'] - 1) * (1 / i['price'])) + (-50 * (1 - (1 / i['price'])) + (50 * 0.8 * ((1 / l['price']) - (1 / i['price']))))
                                br = (best_price - 1) / i['price'] * 100
                            else:
                                bookie = 'Sportsbet'
                                best_price = k['price']
                                xr = (50 * (k['price'] - 1) * (1 / i['price'])) + (-50 * (1 - (1 / i['price'])) + (50 * 0.8 * ((1 / l['price']) - (1 / i['price']))))
                                br = (best_price - 1) / i['price'] * 100

                            results.append([
                                i['number'], 
                                i['name'],
                                best_price,
                                i['price'],
                                bookie,
                                xr,
                                br
                                ])
    except:
        return("Error transforming data.")

    results.sort(key = lambda x: x[2], reverse = False)
    
    if len(results) == 0:
        print('-' * 55)
        print("Betting for this race has now ended.")
        print("Please load the next races.")
        print('-' * 55)
        quit()

    return {
        'race_name' : race_name,
        'race_time' : race_time,
        'countdown' : countdown,
        'delta' : delta,
        'results' : results
    }

if __name__ == "__main__":
    betfair_url = input("Enter Betfair URL: ")
    tab_url = input("Enter TAB URL: ")
    sportsbet_url = input("Enter Sportsbet URL: ")
    
    try:
        urls = setup(betfair_url, tab_url, sportsbet_url)
        info = raceinfo(urls)
        data = fetch(info, urls)

        print("Success!")
    except:
        print("Error running program.")
        quit()

    while True:
        data = fetch(info, urls)
        all_data = transform(data)

        race_name = all_data['race_name']
        race_time = all_data['race_time']
        countdown = all_data['countdown']
        delta = all_data['delta']
        results = all_data['results']

        print('-' * 80)
        print(f'{race_name} @{race_time}')
        print(f'Race starts in: {countdown}')
        print('-' * 80)
        print(tabulate(results, headers = ['#', 'Name', 'Back', 'Lay', 'Bookie', 'EV', 'Bonus bet %'], floatfmt = ".2f"))

        time.sleep(1)
