import os
import re
import random
import time
import requests
from io import BytesIO
from slackclient import SlackClient
from subprocess import call
from prometheus_client import start_http_server, Summary


# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
PIC_FETCH = Summary('picture_request_seconds', 'Time spent fetching picture')



# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM

GO = "go"
PIC = "pic"

MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
TIMEOUT= 60
entry_code = random.randint(1000,999999999)
entry_code_generated = time.time()
token = os.environ.get('HTTP_HEADERS')

headers = {"Authorization":(token)}



def parse_bot_commands(slack_events):
    global entry_code_generated
    global entry_code
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """

    if time.time() - entry_code_generated > TIMEOUT:
        random_number = random.randint(1000,999999)
        entry_code = random_number
        entry_code_generated = time.time()


    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

@REQUEST_TIME.time()
def handle_command(command, channel):
    global entry_code
    global entry_code_generated
    global headers
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Code denied. Start opening with 'go'"

    # Finds and executes the given command, filling in response
    response = None

    if command.startswith(GO):
        random_number = random.randint(1000,9999)
        entry_code = random_number
        entry_code_generated = time.time()
        response = "Safe to move the gate? Code is "+str(entry_code)

        img_data = requests.get("http://192.168.1.16:8123/api/camera_proxy/camera.ffmpeg", headers=headers).content
        with open('image_name.jpg', 'wb') as handler:
            handler.write(img_data)

        #with open('snapshot.jpg', 'rb') as file_content:
        slack_client.api_call(
            "files.upload",
             channels=channel,
             file=img_data,
             title="Gate Pic"
             )
    elif command.startswith(PIC):
        print("Received pic request")
        response = "Like what you see?"
        img_data = requests.get("http://192.168.1.16:8123/api/camera_proxy/camera.ffmpeg", headers=headers).content
        with open('image_name.jpg', 'wb') as handler:
            handler.write(img_data)
        slack_client.api_call(
            "files.upload",
             channels=channel,
             file=img_data,
             title="Gate Pic"
             )


    elif command.startswith(str(entry_code)):
        response = "Sending the signal to the gate.... here we go!"
        print("Challenge code accepted")
        # Probably will just call curl to interact with the esp8266 from here. Touch file just to validate I can exect something from cmd line
        call(["./trigger.sh"])

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running! Initial code: " + str(entry_code))
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        start_http_server(8000)
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
