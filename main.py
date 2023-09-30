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
        super(ChatbotApp, self).__init__(*args, **kw)
        self.init_ui()

    def init_ui(self):
        pnl = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.text_history = wx.TextCtrl(pnl, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.input_field = wx.TextCtrl(pnl)
        self.send_button = wx.Button(pnl, label='Send')
        self.send_button.Bind(wx.EVT_BUTTON, self.send_message)

        vbox.Add(self.text_history, proportion=1, flag=wx.EXPAND)
        vbox.Add(self.input_field, flag=wx.EXPAND)
        vbox.Add(self.send_button, flag=wx.EXPAND)

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

if __name__ == '__main__':
    app = wx.App()
    frame = ChatbotApp(None)
    frame.Show()
    app.MainLoop()
