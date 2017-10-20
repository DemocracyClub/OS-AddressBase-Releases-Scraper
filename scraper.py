import lxml.html
import os
from polling_bot.brain import SlackClient, GitHubClient
from sqlalchemy.exc import OperationalError

# hack to override sqlite database filename
# see: https://help.morph.io/t/using-python-3-with-morph-scraperwiki-fork/148
os.environ['SCRAPERWIKI_DATABASE_NAME'] = 'sqlite:///data.sqlite'
import scraperwiki

try:
    SLACK_WEBHOOK_URL = os.environ['MORPH_POLLING_BOT_SLACK_WEBHOOK_URL']
except KeyError:
    SLACK_WEBHOOK_URL = None

try:
    GITHUB_API_KEY = os.environ['MORPH_GITHUB_ISSUE_ONLY_API_KEY']
except KeyError:
    GITHUB_API_KEY = None


def post_slack_message(release):
    message = "New AddressBase release %s available" % (release)
    slack = SlackClient(SLACK_WEBHOOK_URL)
    slack.post_message(message)


def raise_github_issue(release):
    owner = 'DemocracyClub'
    repo = 'polling_deploy'
    title = 'Import new AddressBase'
    body = "@chris48s - New AddressBase release %s available" % (release)
    github = GitHubClient(GITHUB_API_KEY)
    github.raise_issue(owner, repo, title, body)


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
                if SLACK_WEBHOOK_URL:
                    post_slack_message(release)
                if GITHUB_API_KEY:
                    raise_github_issue(release)
        except OperationalError:
            # The first time we run the scraper it will throw
            # because the table doesn't exist yet
            pass

        scraperwiki.sqlite.save(
            unique_keys=['release'], data={'release': release}, table_name='data')
        scraperwiki.sqlite.commit_transactions()
