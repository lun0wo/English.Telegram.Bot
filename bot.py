import telebot
from telebot import types
import questions # importing the task file for the quiz

TOKEN = "" # YOUR TOKEN

bot = telebot.TeleBot(TOKEN)

user_data = {} # storing user states

# returns the list of commands for selecting a theme
def get_topic_commands():
    return [
        "/tenses", "/simple", "/continuous", "/perfect", "/perfectcontinuous",
        "/present", "/future", "/past", "/presentsimple", "/presentcontinuous",
        "/presentperfect", "/presentperfectcontinuous", "/futuresimple",
        "/futurecontinuous", "/futureperfect", "/futureperfectcontinuous",
        "/pastsimple", "/pastcontinuous", "/pastperfect", "/pastperfectcontinuous",
        "/modalverbs"
    ]

# begins a quiz on a selected topic
def start_quiz(message, topic):
    if topic not in questions.QUESTIONS:
        bot.send_message(message.chat.id, "Theme is not found.")
        return
      
    # recording of the quiz data for each user
    user_id = message.from_user.id
    user_data[user_id] = {
        "topic": topic,
        "questions": questions.QUESTIONS[topic],
        "current_index": 0,
        "score": 0
    }
    # sending subsequent quiz tasks
    send_next_question(message.chat.id, user_id)

# a function for sending quiz tasks
def send_next_question(chat_id, user_id):
    data = user_data[user_id]
    if data["current_index"] >= len(data["questions"]):
        # returns this message if the quiz is finished.
        bot.send_message(
            chat_id,
            f"The quiz is completed! Total: {data['score']} to {len(data['questions'])}.\n"
            "Choose a new theme:\n" + "\n".join(get_topic_commands())
        )
        user_data.pop(user_id, None)
        return

    question = data["questions"][data["current_index"]]
    markup = types.InlineKeyboardMarkup()
    for option in question["options"]:
        markup.add(types.InlineKeyboardButton(
            text=option,
            callback_data=f"answer_{option}"
        ))

    bot.send_message(chat_id, question["question"], reply_markup=markup)

# sending a hint if the answer is incorrect and resending the task
def show_hint(chat_id, user_id):
    data = user_data[user_id]
    question = data["questions"][data["current_index"]]
    
    bot.send_message(chat_id, f"Hint: {question['help']}")

    markup = types.InlineKeyboardMarkup()
    for option in question["options"]:
        markup.add(types.InlineKeyboardButton(
            text=option,
            callback_data=f"answer_{option}"
        ))
    bot.send_message(chat_id, question["question"], reply_markup=markup)

# the command to start the bot
@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "Hi! I'm a bot for practicing English grammar!\n"
        "Choose a topic for the quiz and start practicing as soon as possible!\n" +
        "\n".join(get_topic_commands()) + "\n"
        "To stop the quiz, send a command /stop_quiz"
    )
    bot.send_message(message.chat.id, welcome_text)

# the command to stop the bot
@bot.message_handler(commands=['stop_quiz'])
def stop_quiz(message):
    user_id = message.from_user.id
    if user_id in user_data:
        data = user_data[user_id]
        bot.send_message(
            message.chat.id,
            f"The quiz is stopped. Total: {data['score']} to {data['current_index']}.\n"
            "Choose a new theme:\n" + "\n".join(get_topic_commands())
        )
        user_data.pop(user_id, None)
    else:
        bot.send_message(message.chat.id, "There is no active quiz.")

@bot.message_handler(func=lambda message: message.text.startswith('/'))
def handle_topic_command(message):
    command = message.text[1:]
    if command in [cmd[1:] for cmd in get_topic_commands()]:
        start_quiz(message, command)
    else:
        bot.send_message(message.chat.id, "Unknown command.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('answer_'))
def handle_answer(call):
    user_id = call.from_user.id
    if user_id not in user_data:
        bot.answer_callback_query(call.id, "The quiz is not active.")
        return

    data = user_data[user_id]
    question = data["questions"][data["current_index"]]
    selected_answer = call.data[7:] 

    if selected_answer == question["correct"]:
        bot.answer_callback_query(call.id, "Right! ✅")
        data["score"] += 1
        data["current_index"] += 1
        send_next_question(call.message.chat.id, user_id)
    else:
        bot.answer_callback_query(call.id, "Wrong. Try again.")
        # Добавляем кнопку "подсказка"
        markup = types.InlineKeyboardMarkup()
        for option in question["options"]:
            markup.add(types.InlineKeyboardButton(
                text=option,
                callback_data=f"answer_{option}"
            ))
        markup.add(types.InlineKeyboardButton(
            text="Hint 💡",
            callback_data="help"
        ))
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "help")
def handle_hint(call):
    user_id = call.from_user.id
    if user_id in user_data:
        show_hint(call.message.chat.id, user_id)
        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id, "The quiz is not active")

# launching the bot
if __name__ == '__main__':
    print("The bot has started working...")
    bot.polling(none_stop=True, interval=0)
