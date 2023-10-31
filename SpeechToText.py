import json
import sys
import queue
import wave
from vosk import Model, KaldiRecognizer  # pip3 install vosk
import sounddevice as sd


class SpeechToText:
    """
    Класс для распознавания аудио через Vosk и преобразования его в текст.
    Поддерживаются форматы аудио: wav
    """
    # _device_info = sd.query_devices("input")  # Все input устройства
    # # Частота дискретизации устройства по умолчанию.
    # sample_rate = int(_device_info["default_samplerate"])

    def __init__(self,
                 model_path=r".\model\vosk-model-small-en-us-0.15",
                 ffmpeg_path=r".\ffmpeg",
                 sample_rate=None,
                 device=1
                 ):
        """
        Настройка модели Vosk для распознавания аудио и
        преобразования его в текст.

        :arg model_path: str путь до модели Vosk
        :arg sample_rate: int Частота дискретизации
        :arg ffmpeg_path: str путь к ffmpeg
        """
        self._model_path = model_path
        # По умолчанию английская
        # r".\model\vosk-model-small-ru-0.22"
        self._ffmpeg_path = ffmpeg_path
        self._device = device
        self.sample_rate = sample_rate

        self.q = queue.Queue()

        # Инициализация модели Vosk
        self._model = Model(self._model_path)
        # В распознаватель Kaldi мы передаем модель Vosk
        self._recognizer = KaldiRecognizer(self._model, self.sample_rate)

    def audioFileToText(self, audio_file_name=r"temp.wav") -> str:
        """
        Offline-распознавание аудио файла в текст через Vosk

        :arg audio_file_name: str путь и имя аудио файла
        :return: str распознанный текст
        """
        with wave.open(audio_file_name, "rb") as wf:
            # Чтение данных кусками и распознавание через модель
            while True:
                data = wf.readframes(self.sample_rate)
                if len(data) == 0:
                    break
                # Загружаем данные! И возвращает 1 если законченная фраза
                if self._recognizer.AcceptWaveform(data):
                    pass

        # Возвращаем распознанный текст в виде str
        result_json = self._recognizer.FinalResult()  # это json в виде str
        result_dict = json.loads(result_json)  # это dict
        return result_dict["text"]  # текст в виде str

    def backgroundWiretapping(
            self, handler=None,
            break_: bool = False,
            return_: bool = False
    ) -> None or str:
        """
        Эта функция прослушивает микрофон фоном,
        а также загружает данные в модель и распознает текст.

        Есть 3 режима работы:

        1.
        Она передает распознанный текст на дальнейшую
        обработку в функцию handler

        Важно если выход не включен, то дальнейшее взаимодействие с кодом
        возможно только через  handler. Эта функция в бесконечном цикле.

        2.
        break_ - как первый режим только после фразы, функция прекращает работу

        3.
        return_ - Возвратит распознаю фразу

        :arg handler: function которая обрабатывает то что распознала модель
        :arg break_: bool Прекращать работу функции после фразы
        :arg return_: bool функция возвращает текст
        :return: None or str:
        """

        def _qCallback(indata, frames, time, status):
            """Это вызывается (из отдельного потока) для каждого аудио блока."""
            if status:
                print(status, file=sys.stderr)
            self.q.put(bytes(indata))

        # Запись микрофона в режиме Stream
        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000,
                               device=self._device, dtype='int16',
                               channels=1, callback=_qCallback):
            print("Запись")
            while True:
                data = self.q.get()  # берем пакет записи с микрофона
                # Загружаем данные! И возвращает 1 если законченная фраза
                if self._recognizer.AcceptWaveform(data):
                    # действие после по окончанию фразы
                    if not return_:
                        # Передаем текст на обработку
                        handler(json.loads(self._recognizer.Result())["text"])
                    else:
                        # Возвращаем текст
                        return json.loads(self._recognizer.Result())["text"]
                    if break_:
                        # Выход после фразы
                        break
