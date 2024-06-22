from tMsgSender import tMsgSender
from config import Config
import os, re, logging

class tMsgText:
    def __init__(self, message: dict, sender: tMsgSender, conf: Config):
        self.message: dict = message
        self.getInfo()
        self.sender: tMsgSender = sender
        self.conf: Config = conf
        self.urlRegex: str = r'http[s]?://(?:[a-zA-Z]|[0-9]|[^?\s])+'


    def getInfo(self):
        # extract always included message data
        self.message_id = self.message['message_id']
        self.date = self.message['date']
        self.chat = self.message['chat']
        self.isfrom = self.message['from']


    def checkCanReply(self, id) -> bool:
        logging.debug(f"Checking if allowed to reply to userID: {id}")
        match id in self.conf.allowedIds:
            case True: 
                logging.info(f"Allowed to reply to userID: {id}")
                return True
            case _:
                logging.info(f"Not allowed to process things from userID: {id}")
                return False


    def process(self):
        # Check for userID who sent the msg. Only do stuff if they're allowed to send stuff
        if self.checkCanReply(self.isfrom['id']) == False:
            logging.info(f"Sending not on allow list message for userID: {self.isfrom['id']}")
            self.sender.sendSilentMessage("Sorry, you're not on my allow list! Zzzz...", self.chat['id'])
            return
        
        match self.message:
            case _ if 'text' in self.message and self.message['text'] == "/start":
                # what to say when a new person talks to the bot
                logging.info(f"Received /start message from userID {self.isfrom['id']}, replying with info text")
                self.sender.sendSilentMessage("Hi! Please send a URL to get started!", self.chat['id'])
            case msg if 'text' in self.message and self.message['text'] != "/start":
                logging.info(f"Received text message from userID {self.isfrom['id']}")
                self.downloadAndRespond(msg['text'])
            case msg if 'caption' in self.message:
                logging.info(f"Received media message with caption text from userID {self.isfrom['id']}")
                self.downloadAndRespond(msg['caption'])
            case _:
                logging.warning(f"Received incompatible message from userID {self.isfrom['id']}")
                self.sender.sendSilentMessage("Incompatible message!", self.chat['id'])
        

    def downloadAndRespond(self, text):
        urls: list[str] = self.parseRegex(text)
        if len(urls) > 0:
            logging.debug(f"Mapping URLs to download and respond to")
            # Map() returns an iterator, and won't process any elements until told to.
            # Use the list() to force all elements to be processed
            list(map(lambda x: self.handleDownloadOutcome(self.downloadUrl(x)), urls))
        else:
            logging.info(f"Replying couldn't find URL to userID {self.isfrom['id']}")
            self.reply([False, "Couldn't find a valid URL to use"])
    def convert_twitter_url(url: str) -> str:
        # Only convert URLs that match Twitter's pattern
        if re.match(r'http[s]?://(vx|fx|[a-z]*?)twitter\.com', url):
            return re.sub(r'(http[s]?://)(vx|fx|[a-z]*?)(twitter\.com)', r'\1twitter\3', url)
        elif re.match(r'http[s]?://x\.com', url):
            return re.sub(r'(http[s]?://)x(\.com)', r'\1twitter\2', url)
        else:
            return url

    def parseRegex(self, toParse: str) -> list[str]:
        logging.debug("Parsing text against regex")
        
        # Find all URLs matching the regex pattern
        urls: list[str] = re.findall(self.urlRegex, toParse)
        logging.debug(f"Found {len(urls)} matches: {urls}")

        # Convert URLs if they match the specific Twitter patterns
        convertedUrls: list[str] = [self.convert_twitter_url(url) for url in urls]
        logging.debug(f"Converted {len(convertedUrls)} matches into twitter.com format URLs: {convertedUrls}")
        
        return convertedUrls


    def downloadUrl(self, url: str) -> tuple[str, int]:
        logging.info(f"Attempting to gallery-dl download content from: {url}")
        return (url, os.system(f"gallery-dl \"{url}\""))
    

    def handleDownloadOutcome(self, downloadResult: tuple[str, int]) -> None:
        match downloadResult[1]:
            case 0: 
                logging.info(f"Replying success for {downloadResult[0]} to userID {self.isfrom['id']}")
                self.reply([True, downloadResult[0]])
            case _: 
                logging.info(f"Replying failed download for {downloadResult[0]} to userID {self.isfrom['id']}")
                self.reply([False, f"Encountered an error whilst downloading content for {downloadResult[0]}"])


    def reply(self, data):
        if data[0] == True:
            logging.debug(f"Sending sendMessage request to chat_id {self.chat['id']} with text 'Done for URL {data[1]}'")
            self.sender.sendSilentMessage(f"Done for URL {data[1]}", self.chat['id'])
        else:
            logging.debug(f"Sending sendMessage request to chat_id {self.chat['id']} with text 'Failed! {data[1]}'")
            self.sender.sendSilentMessage(f"Failed! {data[1]}", self.chat['id'])
