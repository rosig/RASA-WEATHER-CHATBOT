# RASA-WEATHER-CHATBOT

To execute this project, you need to install python3, rasa, spaCy and ngrok (With telegram)

Then, to run, type on your terminal in two windows:

rasa train; rasa run actions (window 1)

rasa shell (window 2)

If you want to know how your input are being acknowledged by model trained, use the command in another terminal:

rasa shell nlu

To run in a telegram bot, you need to create a bot with the @botfather channel in telegram, the botfather will create a bot with a name, and acess token to you. And then, using ngrok in your machine, with another terminal in the folder that contains ngrok executable and unziped, 

./ngrok http 5005 

this command with generate a http forwarding, so put it, in creadentials.yml, 

telegram:
  access_token: "HashTokenCreatedByTelegramHere"
  verify: "[YouChatNameBotInTelegram]"
  webhook_url: "https://[your hash created].ngrok.io/webhooks/telegram/webhook"
[case MacOS, other S.O, look at the ngrok documantation instructions]

Can you use also, a venv, virtual environment, if you want. In this case, so,
create a venv, before all of it, and then, run:

source ./venv/bin/activate
