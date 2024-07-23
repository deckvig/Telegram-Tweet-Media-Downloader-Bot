import httpx, logging, os

class recievedData:
    def __init__(self, isOk: bool, isErr: bool=False, statusCode: int=-1, content: bytes=bytearray(0), errDetails: str=""):
        self.ok: bool = isOk
        self.isErr: bool = isErr
        self.statusCode: int = statusCode
        self.content: bytes = content
        self.errDetails: str = errDetails

class tMsgSender:
    def __init__(self, token: str):
        self.token = token
        self.tAPIUrl: str = f"https://api.telegram.org/bot{self.token}"

    def generateRequest(self, msgParams: list) -> str:
        logging.debug("Generating request string")

        if len(msgParams) > 3:
            requestString = f"{self.tAPIUrl}/{msgParams[0]}?"
            requestString += '&'.join([f"{msgParams[i]}={msgParams[i+1]}" for i in range(1, len(msgParams) - 1, 2)])
        elif len(msgParams) > 1:
            requestString = f"{self.tAPIUrl}/{msgParams[0]}?{msgParams[1]}={msgParams[2]}"
        else:
            requestString = f"{self.tAPIUrl}/{msgParams[0]}"

        logging.debug(f"Generated request string: {requestString}")
        return requestString

    def sendGetMe(self) -> recievedData:
        return self.sendRequest(["getMe"])
    
    def sendGetUpdates(self, msgOffset: int, pollTimeout: int, updatesToFetch: str) -> recievedData:
        return self.sendRequest(["getUpdates", "offset", msgOffset, "timeout", pollTimeout, "allowed_updates", updatesToFetch])

    def sendMessage(self, text: str, chat_id: str) -> recievedData:
        return self.sendRequest(["sendMessage", "chat_id", chat_id, "text", text, "disable_web_page_preview", True])
    
    def sendSilentMessage(self, text: str, chat_id: str) -> recievedData:
        return self.sendRequest(["sendMessage", "chat_id", chat_id, "text", text, "disable_web_page_preview", True, "disable_notification", True])

    def sendRequest(self, msgParams: list) -> recievedData:
        requestString = self.generateRequest(msgParams)
        proxies = {
            'http://': os.environ.get("HTTP_PROXY"),
            'https://': os.environ.get("HTTPS_PROXY")
        }
        try:
            timeout = httpx.Timeout(connect=60.0, read=60.0, write=60.0, pool=60.0)
            with httpx.Client(proxies=proxies, verify=False,timeout=timeout) as client:
                response = client.get(requestString, timeout=(5, 60))
                return recievedData(response.status_code == 200, statusCode=response.status_code, content=response.content)
        except Exception as e:
            logging.error(f"Error making request {requestString}: {str(e)}")
            return recievedData(isOk=False, isErr=True, errDetails=f"Error making request {requestString}: {str(e)}")
