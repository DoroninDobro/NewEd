import time
import torch
import sounddevice as sd
from omegaconf import OmegaConf


class TextToSpeech:
    """
    Класс для синтеза речи через модель silero
    Для ru и en
    """

    _device_info = sd.query_devices('output')  # Все output устройства
    sample_rate = int(_device_info["default_samplerate"])
    # Модель может работать только при таких значениях
    for i in [8000, 24000, 48000]:
        if sample_rate >= i:
            sample_rate = i

    def __init__(self,
                 speaker: str = None,
                 language: str = 'ru',
                 model_id: str = None,
                 sample_rate: int = sample_rate,
                 cpu_or_gpu: str = "cpu"
                 ):
        """

        :arg speaker: str Какой голос у модели
            Возможны следующие варианты:
                Ru:
                    -aidar"
                    "baya"
                    "kseniya"
                    "xenia"
                    "random"

        :arg language: str "ru"
        :arg model_id: str версия модели
        :arg sample_rate: int Частота дискретизации [8000, 24000, 48000]
        :arg cpu_or_gpu: str на чем будет обрабатываться cpu, cuda, ipu, xpu,
        mkldnn, opengl, opencl, ideep, hip, ve, fpga, ort, xla, lazy, vulkan, mps, meta, hpu, mtia,
        """

        self._cpu_or_gpu = cpu_or_gpu
        self._language = language
        self._model_id = model_id if model_id else TextToSpeech.getLatestVersionForLanguage(
            self._language)
        self._device = torch.device(self._cpu_or_gpu)
        self.sample_rate = sample_rate

        # Указываем, где располагаются модели
        _model_path = r".\model\silero-model"
        torch.hub.set_dir(_model_path)

        # Проверяем на обновление / скачиваем / инициализируем(Если уже скачено)
        self._model, *_ = torch.hub.load(
            repo_or_dir='snakers4/silero-models',
            model='silero_tts',
            language=self._language,
            speaker=self._model_id)

        # Говорим моделе на чем производить вычисления
        self._model.to(self._device)

        self.speaker = speaker if speaker else self.getSpeakers()[0]

        # Порогрузка модели. Если этого не сделать, то модель будет генерировать аудио очень долго.
        if self._language == "ru":
            self.audioGeneration("Текст для генерации")
            self.audioGeneration("Просто нужно для погрузки модели")
        elif self._language == "en":
            self.audioGeneration("Text to generate. And additional words.")
            self.audioGeneration("Just need to load the model. And these are other additional words.")

    def audioGeneration(self, text: str):
        """
        Генерация аудио из текста при помощи silero

        :arg text: str то что будет произнесено в аудио
        :return: audio
        """
        st = time.time()
        audio = self._model.apply_tts(text=text,
                                      speaker=self.speaker,
                                      sample_rate=self.sample_rate
                                      )
        print(time.time() - st)
        return audio

    def readAudio(self, audio) -> None:
        """
        Воспроизводит аудио.
        Во время этого выполнение программы останавливается

        :arg audio:  audio
        """
        sd.play(audio, self.sample_rate)
        time.sleep((
                           len(audio) / self.sample_rate) + 0.1)  # 0.1 что бы была пауза и для форс-мажора
        sd.stop()

    def getSpeakers(self) -> list[str]:
        """
        :return: list[str] список  для выбранной модели
        """
        return self._model.speakers

    @staticmethod
    def listModels():
        """
        Выводит в консоль возможные версии моделей для всех языков/
        Staticmethod
        """
        models = OmegaConf.load('latest_silero_models.yml')
        available_languages = list(models.tts_models.keys())
        print(f'Available languages {available_languages}')

        for lang in available_languages:
            _models = list(models.tts_models.get(lang).keys())
            print(f'Available models for {lang}: {_models}')

    @staticmethod
    def getLatestVersionForLanguage(language: str) -> str:
        """
        Возвращает последнею версию для определенного языка

        :arg language: str Язык для которого возвращаться последняя версия
        :return: Последня версия языковой модели
        """
        models = OmegaConf.load('latest_silero_models.yml')
        return list(models.tts_models.get(language).keys())[0]
