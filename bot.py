import os
from slack_sdk import WebClient
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask,request,Response
from slackeventsapi import SlackEventAdapter

# Load env
env_path = Path('.') / '.env'  # ('.')meaning current directory
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

# Stack client


slack_event_adapter = SlackEventAdapter(
    os.getenv('SIGNING_SECRET'),'/slack/events',app)

client=WebClient(token=os.getenv('SLACK_TOKEN')) 
BOT_ID = client.api_call("auth.test")['user_id']

message_counts = {}
welcome_messages ={}

class WelcomeMessage:
    START_TEXT ={
        'type':'section',
        'text':{
            'type':'mrkdwn',
            'text':(
                'Welcome to this awesome channel! \\n\n'
                '*Get started by completing the tasks!*'
            )
        }
    }

    DIVIDER = {'type':'divider'}


    def __init__(self,channel,user):
        self.channel=channel
        self.user =user
        self.icon_emoji=':robot_face:'
        self.timestamp =' '
        self.completed = False

    def get_message(self):
        return {
            'ts': self.timestamp,
            'channel':self.channel,
            'username':'Welcome Robot!',
            'icon_emoji':self.icon_emoji,
            'blocks':[
                self.START_TEXT,
                self.DIVIDER,
                self._get_reaction_task()
            ]


        }
    
    def _get_reaction_task(self):
        checkmark =':white_check_mark:'
        if not self.completed:
            check = ':white_large_square:'
        
        text = f'{checkmark} * React to this message!*'

        return [{'type':'section','text':{'type':'mrkdwn','text':text}}]

def send_welcome_message(channel,user):
    welcome = WelcomeMessage(channel,user)
    message= welcome.get_message()
    response =client.chat_postMessage(**message)
    welcome.timestamp =response['ts']

    if channel not in welcome_messages:
        welcome_messages[channel] = {}
    welcome_messages[channel][user]= welcome


@slack_event_adapter.on('message')
def message(payload):
    # print(payload)
    event = payload.get('event',{})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text=event.get('text')

    if user_id != None and BOT_ID != user_id:
        if user_id in message_counts:
            message_counts[user_id]+=1
        else:
            message_counts[user_id]=1
        
        if text.lower() =='start':
            send_welcome_message(f'@{channel_id}',user_id)
        
             
        # client.chat_postMessage(channel=channel_id ,text=text)

# endpoint commands
@app.route('/message-count',methods=['POST'])

def get_message_count():
    data= request.form
    user_id =data.get('user_id')
    channel_id = data.get('channel_id')
    message_count = message_counts.get(user_id,0) #user_id- if we found the user_id in message counts it returns it else return 0

    client.chat_postMessage(channel=channel_id,text=f"Message:{message_count}")
    return Response(), 200

# Just for testing
@app.route("/", methods=["GET"])
def home():
    return "Slack Bot is Running 🚀"

if __name__=="__main__":
    app.run(debug=True)
