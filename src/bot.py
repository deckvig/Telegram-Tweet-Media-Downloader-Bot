import time, sys, httpx, random, json, logging, subprocess, os
from tMsgSender import tMsgSender
from tMsgFetcher import tMsgFetcher, messageInfo
from tMsgText import tMsgText
from config import Config

class bot:
    def __init__(self):
        self.msgOffset = 0
        self.pollTimeout = 50
        logging.info(f"Using max long polling timeout of {self.pollTimeout} seconds")

    def getHelp(self):
        logging.info("\nList of options:\n\n(t)oken to use for telegram bot API [token]\n")
        sys.exit(0)

    def handleMessage(self, msg):
        logging.info("Handling message(s)")
        tMsgText(msg['message'], self.sender, conf).process()
        self.msgOffset = msg['update_id'] + 1
        logging.info(f"Message offset updated to {self.msgOffset}")

    def verifyAPIToken(self):
        logging.info("Using proxies from environment variables")  # Log information about used proxies
        proxies = {
            'http': os.environ.get("HTTP_PROXY"),
            'https': os.environ.get("HTTPS_PROXY"),
        }
        logging.info("Attempting to verify Telegram API token")
        try:
            with httpx.Client(proxies=proxies, verify=False) as client:
                testResponse = client.get(f"https://api.telegram.org/bot{conf.tToken}/getMe")
                if testResponse.status_code == 200:
                    self.bottoken = conf.tToken
                    logging.info("Telegram API token OK")
                else:
                    logging.error("Telegram API check failed")
                    self.getHelp()
        except Exception as ex:
            logging.error("Telegram API token verification failed", exc_info=ex)
            self.getHelp()

    def createSenderFetcher(self):
        self.sender = tMsgSender(self.bottoken)
        self.fetcher = tMsgFetcher(self.bottoken, self.pollTimeout)

    def getBotInfo(self):
        logging.info("Getting Bot info from Telegram")
        response = self.sender.sendGetMe()
        if not response.content:
            logging.error("Empty response received from Telegram")
            return
        self.botInfo = json.loads(response.content)['result']
        self.bot_id = self.botInfo['id']
        self.bot_username = self.botInfo['username']
        logging.info(f"Got bot info - ID: {self.bot_id}, username: {self.bot_username}")

    def run(self):
        self.createSenderFetcher()
        self.getBotInfo()
        while True:
            logging.info("Sending off to wait for new data")
            response = self.fetcher.fetchMessages(self.msgOffset)
            logging.info("Received new Telegram data")
            if response.tResponseOk:
                logging.info("Telegram response was OK")
                list(map(self.handleMessage, response.tResult))
            else:
                logging.warning(f"Telegram response indicated error! {response.errCode} - {response.errDesc}")
                sleepTime = random.randint(self.pollTimeout, self.pollTimeout * 2)
                logging.info(f"Sleeping for {sleepTime} seconds")
                time.sleep(sleepTime)

if __name__ == '__main__':
    print("Loading configuration")
    conf = Config()
    logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s', level=conf.logLevel)
    conf.loadEnvVars()
    galleryDlVersion = subprocess.run(["gallery-dl", "--version"], capture_output=True)
    logging.info(f"Using gallery-dl version: {galleryDlVersion.stdout.decode().strip()}")

    tBot = bot()
    tBot.verifyAPIToken()
    tBot.run()