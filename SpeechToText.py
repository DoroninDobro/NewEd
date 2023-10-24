import json
import wave
from vosk import Model, KaldiRecognizer


class SpeechToText:
    """
    Класс для распознавания аудио через Vosk и преобразования его в текст.
    Поддерживаются форматы аудио: wav
    """
    # Стандартные настройки
    _config_init = {
        "model_path": r".\model\vosk-model-small-en-us-0.15",
        # По умолчанию английская
        # r".\model\vosk-model-small-ru-0.22"
        "sample_rate": 44100,
        "ffmpeg_path": r".\ffmpeg"
    }

    def __init__(self,
                 model_path=None,
                 sample_rate=None,
                 ffmpeg_path=None
                 ):
        """
        Настройка модели Vosk для распознавания аудио и
        преобразования его в текст.

        :arg model_path: str путь до модели Vosk
        :arg sample_rate: int частота выборки, обычно 16000
                Можно и больше, но будет дольше обрабатываться.
                ТАКЖЕ ВАЖНО ЧТО БЫ СОВПОДАЛ sample_rate ЗАПИСАННОЙ АУДИ И МОДЕЛИ
        :arg ffmpeg_path: str путь к ffmpeg
        """
        self._model_path = model_path if model_path else \
            SpeechToText._config_init[
                "model_path"]
        self._sample_rate = sample_rate if sample_rate else \
            SpeechToText._config_init[
                "sample_rate"]
        self._ffmpeg_path = ffmpeg_path if ffmpeg_path else \
            SpeechToText._config_init[
                "ffmpeg_path"]

        # Инициализация модели
        self._model = Model(self._model_path)
        self.recognizer = KaldiRecognizer(self._model, self._sample_rate)

    def audio_file_to_text(self, audio_file_name=r"temp.wav") -> str:
        """
        Offline-распознавание аудио в текст через Vosk
        :param audio_file_name: str путь и имя аудио файла
        :return: str распознанный текст
        """
        with wave.open(audio_file_name, "rb") as wf:
            # Чтение данных кусками и распознавание через модель
            while True:
                data = wf.readframes(self._sample_rate)
                if len(data) == 0:
                    break
                if self.recognizer.AcceptWaveform(data):
                    pass

        # Возвращаем распознанный текст в виде str
        result_json = self.recognizer.FinalResult()  # это json в виде str
        result_dict = json.loads(result_json)  # это dict
        return result_dict["text"]  # текст в виде str
