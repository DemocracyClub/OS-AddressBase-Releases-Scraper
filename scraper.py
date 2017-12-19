import lxml.html
import os
from polling_bot.brain import SlackClient, GitHubClient


# hack to override sqlite database filename
# see: https://help.morph.io/t/using-python-3-with-morph-scraperwiki-fork/148
os.environ['SCRAPERWIKI_DATABASE_NAME'] = 'sqlite:///data.sqlite'
import scraperwiki


SEND_NOTIFICATIONS = True

try:
    SLACK_WEBHOOK_URL = os.environ['MORPH_POLLING_BOT_SLACK_WEBHOOK_URL']
except KeyError:
    SLACK_WEBHOOK_URL = None

try:
    GITHUB_API_KEY = os.environ['MORPH_GITHUB_ISSUE_ONLY_API_KEY']
except KeyError:
    GITHUB_API_KEY = None


def post_slack_message(release):
    message = "New AddressBase release %s available. @chris48s - Order it from https://www.ordnancesurvey.co.uk/psma/ now!" % (release)
    slack = SlackClient(SLACK_WEBHOOK_URL)
    slack.post_message(message)


def raise_github_issue(release):
    owner = 'DemocracyClub'
    repo = 'polling_deploy'
    title = 'Import new AddressBase'
    body = "@chris48s - New AddressBase release %s available" % (release)
    github = GitHubClient(GITHUB_API_KEY)
    github.raise_issue(owner, repo, title, body)


def init():
    scraperwiki.sql.execute("CREATE TABLE IF NOT EXISTS data (release TEXT);")
    scraperwiki.sql.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        data_release_unique ON data (release);""")


init()
html = scraperwiki.scrape("https://www.ordnancesurvey.co.uk/business-and-government/help-and-support/products/addressbase-release-notes.html")
root = lxml.html.fromstring(html)

h3_tags = root.cssselect('h3')
for h3 in h3_tags:
    text = str(h3.text)
    if 'Epoch' in text:
        release = text
        exists = scraperwiki.sql.select(
            "* FROM 'data' WHERE release=?", release)
        if len(exists) == 0:
            print(release)
            if SLACK_WEBHOOK_URL and SEND_NOTIFICATIONS:
                post_slack_message(release)
            if GITHUB_API_KEY and SEND_NOTIFICATIONS:
                raise_github_issue(release)

        scraperwiki.sqlite.save(
            unique_keys=['release'], data={'release': release}, table_name='data')
        scraperwiki.sqlite.commit_transactions()
