import openai
import wx

# Ваш API-ключ (не делитесь им в публичном доступе!)
openai.api_key = "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"

CONVERSATION_FILE = "conversation_history.txt"

def get_previous_conversations():
    try:
        with open(CONVERSATION_FILE, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def save_key_moments(user_msg, bot_msg):
    if is_key_moment(bot_msg):
        with open(CONVERSATION_FILE, "a") as f:
            f.write(f"You: {user_msg}\nChatGPT: {bot_msg}\n")

def is_key_moment(message):
    key_words = ["important", "remember", "key point"]
    for word in key_words:
        if word in message.lower():
            return True
    return False

def ask_gpt(prompt):
    history = get_previous_conversations()
    messages = []

    if history:
        history_split = history.strip().split("\n")
        for i in range(0, len(history_split), 2):
            user_msg = history_split[i].replace("You: ", "")
            bot_msg = history_split[i + 1].replace("ChatGPT: ", "")

            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": bot_msg})

    # Добавим текущий вопрос пользователя
    messages.append({"role": "user", "content": prompt})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        assistant_message = response.choices[0].message['content']
        return assistant_message
    except Exception as e:
        return str(e)

class ChatbotApp(wx.Frame):
    def __init__(self, *args, **kw):
        style = wx.FRAME_SHAPED | wx.SIMPLE_BORDER
        super(ChatbotApp, self).__init__(style=style, *args, **kw)
        
        self.hasShape = False
        self.delta = None

        self.bmp = wx.Bitmap("cat.png", wx.BITMAP_TYPE_PNG)

        self.SetClientSize((self.bmp.GetWidth(), self.bmp.GetHeight()))

        dc = wx.ClientDC(self)
        dc.DrawBitmap(self.bmp, 0, 0, True)
        self.SetWindowShape()

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_WINDOW_CREATE, self.SetWindowShape)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_KEY_UP, self.on_key_up)

        self.init_ui()

    def SetWindowShape(self, evt=None):
    	img = wx.Image('cat.png', wx.BITMAP_TYPE_PNG)
    	r = img.ConvertToRegion()
    	self.hasShape = self.SetShape(r)

    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush("#A1FFA1"))  # Светло-салатовый цвет
        dc.Clear()  # Эта строка очистит текущий фон и применит новый.
        dc.DrawBitmap(self.bmp, 0, 0, True)


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

    def init_ui(self):
        pnl = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        chat_height = int(self.GetSize().GetHeight() * 0.10)

        vbox.Add((-1,200))
        self.text_history = wx.TextCtrl(pnl, size=(-1, chat_height), style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.input_field = wx.TextCtrl(pnl)
        self.send_button = wx.Button(pnl, label='Send')
        self.send_button.Bind(wx.EVT_BUTTON, self.send_message)

        vbox.Add(self.text_history, proportion=0, flag=wx.EXPAND | wx.LEFT, border=20)  # Отступ слева
        vbox.Add(self.input_field, flag=wx.EXPAND | wx.LEFT, border=20)  # Отступ слева
        vbox.Add(self.send_button, flag=wx.EXPAND | wx.LEFT, border=20)  # Отступ слева

        pnl.SetSizer(vbox)

        self.SetTitle('ChatGPT for Kids')
        self.Centre()

    def send_message(self, event):
        user_message = self.input_field.GetValue()
        if user_message:
            self.text_history.AppendText(f"You: {user_message}\n")
            response = ask_gpt(user_message)
            self.text_history.AppendText(f"ChatGPT: {response}\n")
            save_key_moments(user_message, response)
            self.input_field.Clear()

    def on_key_up(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:  # Если нажата клавиша Esc
            self.Close(True)

if __name__ == '__main__':
    app = wx.App()
    frame = ChatbotApp(None)
    frame.Show()
    app.MainLoop()
