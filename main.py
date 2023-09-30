import openai
import wx

# Ваш секретный API-ключ от OpenAI (важно не публиковать его и не делиться)
openai.api_key = "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"

# Название файла, в котором будет храниться история разговора
CONVERSATION_FILE = "conversation_history.txt"

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

# Класс главного окна чатбота
class ChatbotApp(wx.Frame):
    def __init__(self, *args, **kw):
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
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_KEY_UP, self.on_key_up)

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

    # Обработчики для возможности перетаскивать окно
    def OnLeftDown(self, evt):
        self.CaptureMouse()
        pos = self.ClientToScreen(evt.GetPosition())
        origin = self.GetPosition()
        self.delta = wx.Point(pos.x - origin.x, pos.y - origin.y)

    def OnMouseMove(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            pos = self.ClientToScreen(evt.GetPosition())
            newPos = (pos.x - self.delta.x, pos.y - self.delta.y)
            self.Move(newPos)

    def OnLeftUp(self, evt):
        if self.HasCapture():
            self.ReleaseMouse()

    def OnRightUp(self, evt):
        self.Close()

    # Инициализация пользовательского интерфейса
    def init_ui(self):
        # Создание панели на основном окне
        pnl = wx.Panel(self)
        
        # Создание вертикального контейнера для управления компоновкой элементов
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Вычисление высоты области чата как 10% от высоты главного окна
        chat_height = int(self.GetSize().GetHeight() * 0.28)
        chat_width = int(self.GetSize().GetWidth() * 0.4)

        # Добавление пустого пространства высотой 200 пикселей в верхней части интерфейса
        vbox.Add((chat_width,353))
        
        # Создание многострочного текстового поля для истории чата с атрибутом READONLY (только для чтения)
        self.text_history = wx.TextCtrl(pnl, size=(chat_width, chat_height), style=wx.TE_MULTILINE | wx.TE_READONLY)
        
        # Создание однострочного текстового поля для ввода сообщений
        self.input_field = wx.TextCtrl(pnl, size=(chat_width, -1))

        self.text_history.SetBackgroundColour("#E2ACAB")  
        self.input_field.SetBackgroundColour("#E2A9AF")  

        
        # Создание кнопки "Send"
        self.send_button = wx.Button(pnl, label='Send', size=(chat_width, -1))
        
        # Привязка события нажатия на кнопку к функции send_message
        self.send_button.Bind(wx.EVT_BUTTON, self.send_message)

        # Добавление поля истории чата, поля ввода и кнопки "Send" к вертикальному контейнеру

        vbox.Add(self.text_history)
        vbox.Add(self.input_field)
        vbox.Add(self.send_button)

        hbox_outer = wx.BoxSizer(wx.HORIZONTAL)

        hbox_outer.Add((175, 0), proportion=1)  # Пустое пространство слева
        hbox_outer.Add(vbox, proportion=2, flag=wx.EXPAND)
        hbox_outer.Add((chat_width, 0), proportion=1)  # Пустое пространство справа


        # Установка вертикального контейнера как основного менеджера компоновки для панели
        pnl.SetSizer(hbox_outer)

        # Установка заголовка для главного окна
        self.SetTitle('ChatGPT for Kids')
        
        # Центрирование окна на экране
        self.Centre()



    # Отправка сообщения и получение ответа от бота
    def send_message(self, event):
        user_message = self.input_field.GetValue()
        bot_response = ask_gpt(user_message)
        # Убираем префикс "ChatGPT:" из ответа бота
        bot_response = bot_response.replace("ChatGPT: ", "")
        self.text_history.AppendText(f"You: {user_message}\n")
        self.text_history.AppendText(f"LisKas: {bot_response}\n")
        self.input_field.Clear()

    # Отправка сообщения при нажатии на клавишу Enter
    def on_key_up(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER:
            self.send_message(None)

# Запуск приложения
if __name__ == '__main__':
    app = wx.App()
    frm = ChatbotApp(None)
    frm.Show()
    app.MainLoop()
