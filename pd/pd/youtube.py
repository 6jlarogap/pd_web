# -*- coding: utf-8 -*-

import re, urllib.request, urllib.error, urllib.parse, json
from decimal import Decimal

from django.conf import settings

class Youtube(object):
    """
    Функции с youtube api
    """
    RE_YOUTUBE_URL = r'^.*(?:youtu.be\/|v\/|e\/|u\/\w+\/|embed\/|v=)([^#\&\? ]{11,})[\?\/\&]*.*?$'
    GET_PARMS_TEMPLATE = 'https://www.googleapis.com/youtube/v3/videos?id=%(id)s&key=%(key)s&part=snippet'
    GET_CAPTIONS_TEMPLATE = 'http://video.google.com/timedtext?lang=%(lang)s&v=%(id)s'
    YOUTUBE_URL_TEMPLATE = 'https://www.youtube.com/watch?v=%(id)s'
    
    _id = None
    _url = None
    _audio_lang = None

    class Excpt(Exception):
        """
        Базовое исключение
        """
        pass

    class ExcptId(Excpt):
        """
        Ошибка получения youtube id из URI или из переданного youtube id
        """
        pass

    class ExcptNoGoogleKey(Excpt):
        """
        Не задан ключ приложения Google
        """
        pass

    class ExcptHttp(Excpt):
        """
        Ошибка интернет- доступа к youtube api
        """
        pass

    def __init__(self, youtube_id, *args, **kwargs):
        super(Youtube, self).__init__(*args, **kwargs)
        if re.search(r'^https?://', youtube_id, flags=re.I):
            m = re.search(self.RE_YOUTUBE_URL, youtube_id, flags=re.I)
            if not m:
                raise self.ExcptId
            self._id = m.group(1)
            self._url = youtube_id
            if len(self._id) != 11:
                raise self.ExcptId
        elif not re.search(r'^[^#\&\? ]{11,11}$', youtube_id):
            raise self.ExcptId
        else:
            self._id = youtube_id
            self._url = self.YOUTUBE_URL_TEMPLATE % dict(id=youtube_id)

    def get_id(self):
        return self._id

    def get_url(self):
        return self._url

    def get_parms(self):
        """
        Получить параметры видео
        """
        if not settings.GOOGLE_SERVER_API_KEY:
            raise self.ExcptNoGoogleKey
        url = self.GET_PARMS_TEMPLATE % dict(
            id=self._id,
            key=settings.GOOGLE_SERVER_API_KEY
        )
        try:
            r = urllib.request.urlopen(url)
            raw_data = r.read().decode(r.info().getparam('charset') or 'utf-8')
            data = json.loads(raw_data)
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
            raise ExcptHttp
        result = dict(
            yid=self._id,
            url=self._url,
            title='',
            title_photo_url='',
            audio_lang='ru',
        )
        try:
            snippet = data['items'][0]['snippet']
        except (KeyError, IndexError):
            pass
        else:
            try:
                result['title'] = snippet['title']
            except KeyError:
                pass
            try:
                result['title_photo_url'] = snippet['thumbnails']['default']['url']
            except KeyError:
                pass
            try:
                result['audio_lang'] = snippet['defaultAudioLanguage']
            except KeyError:
                pass
        self._audio_lang = result['audio_lang']
        return result

    def get_captions(self):
        """
        Получить субтитры видео
        """
        # inspired by
        # http://code.activestate.com/recipes/577459-convert-a-youtube-transcript-in-srt-subtitle/

        pattern = re.compile(r'<?text start="(\d+\.?\d*)" dur="(\d+\.?\d*)">(.*)</text>?')

        def parseLine(text):
            """Parse a subtitle."""
            m = re.match(pattern, text)
            result = None
            if m:
                try:
                    start = Decimal(m.group(1))
                    stop = start + Decimal(m.group(2))
                    result = dict(
                        start=float(start),
                        stop=float(stop),
                        text=m.group(3),
                    )
                except ValueError:
                    pass
            return result

        result = []
        if not self._audio_lang:
            try:
                parms = self.get_parms()
                lang = parms['audio_lang']
            except self.Excpt:
                lang = 'ru'
        else:
            lang = self._audio_lang

        url = self.GET_CAPTIONS_TEMPLATE % dict(
            id=self._id,
            lang=lang,
        )
        try:
            r = urllib.request.urlopen(url)
        except (urllib.error.HTTPError, urllib.error.URLError,):
            return result
        buf = r.read().decode(r.info().getparam('charset') or 'utf-8')
        for text in buf.replace('\n', '').split('><'):
            parsed = parseLine(text)
            if parsed:
                result.append(parsed)
        return result
