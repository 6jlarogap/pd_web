# -*- coding: utf-8 -*-

import re, urllib2, json

from django.conf import settings

class Youtube(object):
    """
    Функции с youtube api
    """
    RE_YOUTUBE_URL = r'^.*(?:youtu.be\/|v\/|e\/|u\/\w+\/|embed\/|v=)([^#\&\? ]{11,})[\?\/\&]*.*?$'
    
    GET_PARMS_TEMPLATE = 'https://www.googleapis.com/youtube/v3/videos?id=%(id)s&key=%(key)s&part=snippet'
    
    _id = None
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
            print self._id, len(self._id)
            if len(self._id) != 11:
                raise self.ExcptId
        elif not re.search(r'^[^#\&\? ]{11,11}$', youtube_id):
            raise self.ExcptId
        else:
            self._id = youtube_id

    def get_id(self):
        return self._id

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
            r = urllib2.urlopen(url)
            raw_data = r.read().decode(r.info().getparam('charset') or 'utf-8')
            data = json.loads(raw_data)
        except (urllib2.HTTPError, urllib2.URLError, ValueError):
            raise ExcptHttp
        result = dict(title='', title_photo_url='', audio_lang='ru')
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
