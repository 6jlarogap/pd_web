import os, time
from django.conf import settings
from pd.views import get_front_end_url
from pd.utils import host_country_code

from users.models import Org

def context_processor(request):

    def get_static_updated_time():
        """
        UTC modified timestamp папки settings.STATIC_ROOT

        Во избежание лишнего кэширования в браузере клиента
        статических файлов: javascript- сценариев.

        Все наши сценарии определяются в шаблонах как:

        <script src="{% static 'js/<сценарий>.js' %}?updated_=<timestamp>">
        </script>

        где <timestamp> - UTC время в секундах изменения папки
        settings.STATIC_ROOT. Это время автоматически обновляется
        процедурой установки нового кода в проекте.
        В этой процедуре, после ./manage.py collectstatic,
        если произошли изменения в папке settings.STATIC_ROOT,
        производится обновление modified timestamp этой
        папки, и этот обновленный <timestamp> приписывается
        в src сценариев. URL сценария меняется, браузер
        должен его перегружать.
        """

        try:
            result = os.stat(settings.STATIC_ROOT).st_mtime
        except (OSError, AttributeError, ):
            # Невероятно, но!
            # Вдруг STATIC_ROOT не определено или ОС доступ
            # закроет к параметрам папки.
            result = time.time()
        return int(result)

    return {
            'global_context_PRODUCTION_SITE': settings.PRODUCTION_SITE,
            'global_context_FRONT_END_URL': get_front_end_url(request),
            'global_context_DEADMAN_IDENT_NUMBER_ALLOW': settings.DEADMAN_IDENT_NUMBER_ALLOW,
            'global_context_CREATE_CABINET_ALLOW': settings.CREATE_CABINET_ALLOW,
            'global_context_REDIRECT_LOGIN_TO_FRONT_END': settings.REDIRECT_LOGIN_TO_FRONT_END,
            'global_context_DEATH_CERTIFICATE_REQUIRED': settings.DEATH_CERTIFICATE_REQUIRED,
            'global_context_HOST_COUNTRY_CODE': host_country_code(request) or 'ru',
            'global_context_MOBILEKEEPER_URL': request.build_absolute_uri(
                os.path.join(
                    settings.MEDIA_URL,
                    settings.MOBILEKEEPER_MEDIA_PATH,
             )),
            'global_context_STATIC_UPDATED_TIME': get_static_updated_time(),

            'global_context_ARE_LORUS_IN_SYSTEM': Org.objects.filter(type=Org.PROFILE_LORU).exists(),
            'global_context_UHOD_MOGIL_URL': settings.UHOD_MOGIL_URL,
            'global_context_HRAM_PREDKOV_URL': settings.HRAM_PREDKOV_URL,
            'global_context_YEAR_OVER_DAYS': settings.YEAR_OVER_DAYS,
            'global_context_SHOW_OPER_STATS': settings.SHOW_OPER_STATS,
           }
