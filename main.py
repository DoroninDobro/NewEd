import openai
import wx
from wx.lib.buttons import GenButton, GenBitmapTextButton
import speech_recognition as sr
# import os
# from google.cloud import speech_v1p1beta1 as speech
# from google.cloud import texttospeech
import pyaudio
import wave
# from google.cloud import speech
from google.cloud import speech_v1p1beta1 as speech
# from google.cloud.speech import types
from google.cloud import texttospeech
import os
import io
import SpeechToText

# Настройки записи
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 44100
# Ваш секретный API-ключ от OpenAI (важно не публиковать его и не делиться)
openai.api_key = "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"

# client = texttospeech.TextToSpeechClient()
# voices = client.list_voices()
# for voice in voices.voices:
#     print(f"Name: {voice.name}")
#     print(f"Gender: {voice.ssml_gender}")
#     print(f"Language Codes: {voice.language_codes}\n")

# Название файла, в котором будет храниться история разговора
CONVERSATION_FILE = "conversation_history.txt"

# Для использования вашего API-ключа, вы должны установить его в переменную окружения:
os.environ[
    "GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/vladimirdoronin/NewEd/NewEd.json"


def play_audio(filename):
    """
    Воспроизведение аудиофайла.
    """
    os.system(f"afplay {filename}")


def synthesize_speech(text, output_filename='output.mp3'):
    # Инициализация клиента
    client = texttospeech.TextToSpeechClient()

    # Настройка запроса
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Запрос к API для получения аудио
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )

    # Сохранение аудио в файл
    with open(output_filename, "wb") as out:
        out.write(response.audio_content)


# Функция для чтения предыдущих бесед из файла
def get_previous_conversations():
    try:
        with open(CONVERSATION_FILE, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""


# Функция для сохранения ключевых моментов разговора
def save_key_moments(user_msg, bot_msg):
    # Если сообщение является ключевым, сохраняем его в файл
    if is_key_moment(bot_msg):
        with open(CONVERSATION_FILE, "a") as f:
            f.write(f"You: {user_msg}\nLisKas: {bot_msg}\n")


# Функция для определения, является ли сообщение ключевым моментом
def is_key_moment(message):
    # Список ключевых слов, которые определяют важность сообщения
    key_words = ["important", "remember", "key point"]
    for word in key_words:
        if word in message.lower():
            return True
    return False


# Функция для взаимодействия с GPT-3 и получения ответа на вопрос
def ask_gpt(prompt):
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


def record_audio(filename="temp.wav", duration=5, rate=SAMPLE_RATE):
    """Запись аудио с микрофона."""

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=rate,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Начинаю запись...")

    frames = []

    for _ in range(0, int(rate / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Запись завершена.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))


def text_to_speech(text, language="en-US", filename="output.mp3"):
    """Преобразует текст в аудио с помощью Google Text-to-Speech."""

    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=language,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(filename, 'wb') as out:
        out.write(response.audio_content)


# Класс главного окна чатбота
class ChatbotApp(wx.Frame):
    def __init__(self, *args, **kw):
        # Заранее инициализируем модель vosk так как она подгружается ~ 2 секунды.
        self.speechToText = SpeechToText.SpeechToText()

        # Задаем стили для окна
        style = wx.FRAME_SHAPED | wx.SIMPLE_BORDER
        super(ChatbotApp, self).__init__(style=style, *args, **kw)

        self.hasShape = False
        self.delta = None

        # Загрузка фонового изображения для окна
        self.bmp = wx.Bitmap("cat.png", wx.BITMAP_TYPE_PNG)

        self.SetClientSize((self.bmp.GetWidth(), self.bmp.GetHeight()))

        dc = wx.ClientDC(self)
        dc.DrawBitmap(self.bmp, 0, 0, True)
        self.SetWindowShape()

        # Привязка обработчиков событий к методам
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_WINDOW_CREATE, self.SetWindowShape)

        self.init_ui()

        # Получите размеры экрана
        screen_width, screen_height = wx.DisplaySize()
        # Получите размеры вашего окна
        window_width, window_height = self.GetSize()

        # Позиционируйте окно в левом нижнем углу
        self.SetPosition((0, screen_height - window_height))

    # Устанавливаем форму окна в соответствии с изображением
    def SetWindowShape(self, evt=None):
        img = wx.Image('cat.png', wx.BITMAP_TYPE_PNG)
        r = img.ConvertToRegion()
        self.hasShape = self.SetShape(r)

    # Функция рисования фонового изображения
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush("#A1FFA1"))  # Светло-салатовый цвет
        dc.Clear()
        dc.DrawBitmap(self.bmp, 0, 0, True)

    def init_ui(self):
        # Создание панели на основном окне
        pnl = wx.Panel(self)

        # Создание вертикального контейнера для управления компоновкой элементов
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Вычисление высоты области чата как 10% от высоты главного окна
        chat_height = int(self.GetSize().GetHeight() * 0.28)
        chat_width = int(self.GetSize().GetWidth() * 0.4)

        # Добавление пустого пространства высотой 200 пикселей в верхней части интерфейса
        vbox.Add((chat_width, 353))

        # Создание многострочного текстового поля для истории чата с атрибутом READONLY (только для чтения)
        self.text_history = wx.TextCtrl(pnl, size=(chat_width, chat_height),
                                        style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_SUNKEN)
        self.text_history.SetBackgroundColour("#E2ACAB")

        # Создание однострочного текстового поля для ввода сообщений
        self.input_field = wx.TextCtrl(pnl, size=(chat_width, -1),
                                       style=wx.BORDER_SUNKEN)
        self.input_field.SetBackgroundColour("#E2A9AF")

        # Создание кнопки "Send"
        self.send_button = wx.Button(pnl, label='Send', size=(chat_width, -1))
        # New voice input button
        self.voice_button = wx.Button(pnl, label='Voice Input',
                                      size=(chat_width, -1))
        # Привязка событий кнопки к функциям записи голоса
        # Привязка события нажатия на кнопку к функции send_message
        self.send_button.Bind(wx.EVT_BUTTON, self.send_message)
        self.voice_button.Bind(wx.EVT_BUTTON, self.start_voice_input)

        # Добавление поля истории чата, поля ввода и кнопки "Send" к вертикальному контейнеру
        vbox.Add(self.text_history)
        vbox.Add(self.input_field)
        vbox.Add(self.send_button)
        vbox.Add(self.voice_button)

        hbox_outer = wx.BoxSizer(wx.HORIZONTAL)

        hbox_outer.Add((175, 0), proportion=1)  # Пустое пространство слева
        hbox_outer.Add(vbox, proportion=2, flag=wx.EXPAND)
        hbox_outer.Add((chat_width, 0),
                       proportion=1)  # Пустое пространство справа

        # Установка вертикального контейнера как основного менеджера компоновки для панели
        pnl.SetSizer(hbox_outer)

        # Установка заголовка для главного окна
        self.SetTitle('ChatGPT for Kids')

        # Центрирование окна на экране
        self.Centre()

        self.recording = False  # Добавляем атрибут для проверки активности записи

    def start_voice_input(self, event):

        # Распознавание текста
        text = self.speechToText.backgroundWiretapping(return_=True)

        if text:
            # Получение ответа от вашей функции
            answer = ask_gpt(text)

            # Преобразование текста в аудио
            text_to_speech(answer)

            # Воспроизведение аудио (может потребоваться дополнительная настройка)
            play_audio("output.mp3")

    #     global is_recording, stream, frames
    #     is_recording = True
    #     frames = []  # Очищаем предыдущие данные

    #     stream = p.open(format=FORMAT,
    #                     channels=CHANNELS,
    #                     rate=RATE,
    #                     input=True,
    #                     frames_per_buffer=CHUNK)
    #     print("* recording")
    #     a = 1
    #     while is_recording:
    #         data = stream.read(CHUNK)
    #         frames.append(data)

    # def stop_voice_input(self, event=None):
    #     global is_recording, stream
    #     is_recording = False
    #     print("* done recording")

    #     stream.stop_stream()
    #     stream.close()

    #     with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
    #         wf.setnchannels(CHANNELS)
    #         wf.setsampwidth(p.get_sample_size(FORMAT))
    #         wf.setframerate(RATE)
    #         wf.writeframes(b''.join(frames))

    # Продолжаем ваш процесс распознавания и ответа
    # recognized_text = transcribe_audio()
    # response_text = ask_gpt(recognized_text)  # Предполагая, что у вас уже есть этот метод
    # output_filename = "response.mp3"
    # text_to_audio(response_text, output_filename)
    # play_audio('response.mp3')

    def send_message(self, event):
        print('You press send')
        user_message = self.input_field.GetValue()
        # Проверяем, что поле ввода не пустое перед обработкой сообщения
        if not user_message.strip():
            return
        bot_response = ask_gpt(user_message)
        # Убираем префикс "ChatGPT:" из ответа бота
        bot_response = bot_response.replace("ChatGPT: ", "")
        self.text_history.AppendText(f"You: {user_message}\n")
        self.text_history.AppendText(f"LisKas: {bot_response}\n")
        self.input_field.Clear()


# Запуск приложения
if __name__ == '__main__':
    app = wx.App()
    frm = ChatbotApp(None)
    frm.Show()
    app.MainLoop()
