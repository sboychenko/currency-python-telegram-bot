import telegram

BOT_TOKEN = "token"


def main():
    bot = telegram.Bot(token=BOT_TOKEN)
    updates = bot.get_updates()
    for update in updates:
        try:
            chat_id = update.message.chat_id
            bot.send_message(chat_id=chat_id, text='Your chat ID is: {}'.format(chat_id))
        except:
            print("error")


# Bot for get chat_id
if __name__ == '__main__':
    main()
