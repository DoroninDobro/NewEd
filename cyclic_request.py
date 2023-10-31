import time

import openai

import SpeechToText
import TextToSpeech

CONVERSATION_FILE = "conversation_history.txt"
openai.api_key = "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"

# Заранее инициализируем модель vosk. Английский
speechToText = SpeechToText.SpeechToText(sample_rate=44100)
print("The model is loaded SpeechToText")

# Модель синтеза речи. Английский
textToSpeech = TextToSpeech.TextToSpeech(
    model_id='v3_en',
    sample_rate=8000,
    language="en")
print("The model is loaded TextToSpeech")


def get_previous_conversations():
    try:
        with open(CONVERSATION_FILE, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def ask_gpt(prompt: str) -> str:
    # Получаем историю предыдущих бесед
    history = get_previous_conversations()
    messages = []

    # Если в истории есть сообщения, добавляем их в список сообщений
    if history:
        history_split = history.strip().split("\n")
        for i in range(0, len(history_split), 2):
            user_msg = history_split[i].replace("You: ", "")
            bot_msg = history_split[i + 1].replace("LisKas: ", "")

            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": bot_msg})

    # Добавляем текущий запрос от пользователя
    messages.append({"role": "user", "content": prompt})

    # Отправляем запрос к GPT-3 и возвращаем полученный ответ
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        assistant_message = response.choices[0].message['content']
        return assistant_message
    except Exception as e:
        return str(e)


def handler_request(text: str):
    """
    Получение ответа от GPT, синтез и воспроизведение речи.
    :arg text: str
    """
    # Распознавание текста(Тут же запись голоса)
    st = time.time()  # ТАЙМЕР после фраза

    print(f"I: {text}")
    answer = None
    if text:
        # Получение ответа от вашей функции
        answer = ask_gpt(text)

    print(f"GPT: {answer}")
    if answer:
        # Генерируем аудио
        audio = textToSpeech.audioGeneration(answer)

        # Воспроизводим аудио
        textToSpeech.readAudio(audio)


def main():
    # Запуск петли фоновой прослушки микрофона. И распознавание речи.
    speechToText.backgroundWiretapping(handler=handler_request)


if __name__ == "__main__":
    main()
