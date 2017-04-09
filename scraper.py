import lxml.html
import os
import requests
from sqlalchemy.exc import OperationalError

# hack to override sqlite database filename
# see: https://help.morph.io/t/using-python-3-with-morph-scraperwiki-fork/148
os.environ['SCRAPERWIKI_DATABASE_NAME'] = 'sqlite:///data.sqlite'
import scraperwiki

SLACK_WEBHOOK_URL = os.environ['MORPH_SLACK_WEBHOOK_URL']

def post_slack_message(message):
    r = requests.post(SLACK_WEBHOOK_URL, json={ "text": message })

html = scraperwiki.scrape("https://www.ordnancesurvey.co.uk/business-and-government/help-and-support/products/addressbase-release-notes.html")
root = lxml.html.fromstring(html)

h3_tags = root.cssselect('h3')
for h3 in h3_tags:
    text = str(h3.text)
    if 'Epoch' in text:
        release = text
        try:
            exists = scraperwiki.sql.select(
                "* FROM 'data' WHERE release=?", release)
            if len(exists) == 0:
                print(release)
                slack_message = "New AddressBase release %s available" % (release)
                post_slack_message(slack_message)
        except OperationalError:
            # The first time we run the scraper it will throw
            # because the table doesn't exist yet
            pass

        scraperwiki.sqlite.save(
            unique_keys=['release'], data={'release': release}, table_name='data')
        scraperwiki.sqlite.commit_transactions()
