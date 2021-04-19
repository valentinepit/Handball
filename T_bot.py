import requests


def telegram_bot_send_text(bot_message):
    bot_token = '1718324595:AAHMYHS2Qsr72qQbn_-LEaWobIwqQVdf_UI'
    #bot_chatID = '1303537207'
    url = 'https://api.telegram.org/bot'
    channel_id = "-1001418183016"
    send_text = url + bot_token + '/sendMessage?chat_id=' + channel_id + '&parse_mode=Markdown&text=' + bot_message
    try:
        response = requests.get(send_text)
    except Exception as e:
        return (e)
    return response.json()


'''
import requests
BOT_TOKEN = '1718324595:AAHMYHS2Qsr72qQbn_-LEaWobIwqQVdf_UI'

MethodGetUpdates = 'https://api.telegram.org/bot{token}/getUpdates'.format(token=BOT_TOKEN)


while True:
    response = requests.post(MethodGetUpdates)
    result = response.json()
    print(result)

#test = telegram_bot_sendtext("Testing Telegram bot")
'''

# @arsentiy_tennis
# id = https://api.telegram.org/bot1718324595:AAHMYHS2Qsr72qQbn_-LEaWobIwqQVdf_UI/getUpdates
# A_handball_bot
# 1718324595:AAHMYHS2Qsr72qQbn_-LEaWobIwqQVdf_UI
# api_id = 3835472
# api_hash = b9e2c64f8d807efdcb0a57a9ec2f757a
