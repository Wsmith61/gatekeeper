import os
import re
import random
import time
from io import BytesIO
from slackclient import SlackClient
from subprocess import call
from prometheus_client import start_http_server, Summary


# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
PIC_FETCH = Summary('picture_request_seconds', 'Time spent fetching picture')



# instantiate Slack client
#slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
GO = "go"
PIC = "pic"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
entry_code = random.randint(1000,999999999)

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
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
        print("Received initial request")
        response = "Safe to move the gate? Code is "+str(entry_code)

        # Going to need to chuck some code in here to fetch the image locally before uploading
        #@PIC_FETCH.time()
        call(["/usr/bin/wget", "http://192.168.1.16:8844/snapshot.jpg", "-O","snapshot.jpg"])

        with open('snapshot.jpg', 'rb') as file_content:
           slack_client.api_call(
             "files.upload",
             #channels="tmptest",
             channels=channel,
             file=file_content.read(),
             title="Gate Pic"
    )
    elif command.startswith(PIC):
        print("Received pic request")
        response = ""

        # Going to need to chuck some code in here to fetch the image locally before uploading
        call(["/usr/bin/wget", "http://192.168.1.16:8844/snapshot.jpg", "-O","snapshot.jpg"])

        with open('snapshot.jpg', 'rb') as file_content:
           slack_client.api_call(
             "files.upload",
             #channels="tmptest",
             channels=channel,
             file=file_content.read(),
             title="Status pic"
    )

    elif command.startswith(str(entry_code)):
        response = "Sending the signal to the gate.... here we go!"
        print("Challenge code accepted")
        # Probably will just call curl to interact with the esp8266 from here. Touch file just to validate I can exect something from cmd line
        call(["./trigger.sh"])
        # Change the code back to something we dont know
        #entry_code = random.randint(1000,999999999)
        # Going to need to chuck some code in here to fetch the image locally before uploading
        #with open('brand.jpg', 'rb') as file_content:
        #   slack_client.api_call(
        #     "files.upload",
        #     channels="tmptest",
        #     file=file_content.read(),
        #     title="Result"
        #     )

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
