# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _

from sms_service import sms24x7

def send_sms(phone_number, text, email_error_text=''):
    """
    Отправить СМС с текстом text на номер phone_number (Decimal or string!)
    
    *   email_error_text - текст сообщения в службу поддержки, если передача СМС не получилась.
        К нему добавляется сообщение СМС-сервиса
    *   функцию вызывать, если not settings.DEBUG!
    
    *   Возвращает кортеж:
            sent,   True, если успешно
            message, сообщение: пустое, если успешно, иначе причину отказа в отправке
    """
    phone_number = str(phone_number)
    default_serv = your_serv = None
    message = ''
    for serv in settings.SMS_SERVICE:
        if serv['country_code'] == 'default':
            default_serv = serv
        if phone_number.startswith(serv['country_code']):
            your_serv = serv
    if not your_serv:
        if default_serv:
            your_serv = default_serv
        else:
            message = _(u"Оператора телефона нет в настройках PohoronnoeDeloRu")
    if not message:
        try:
            smsapi = sms24x7.smsapi(your_serv['user'], your_serv['password'])
            smsapi.push_msg(
                text,
                phone_number,
                # 11 chars max
                sender_name=u'PohoronnoeD',
                nologin = True
            )
        # Некоторые ошибки идут с нормальной расшифровкой, но иные только
        # с цифровыми кодами, приходится перечислять
        except sms24x7.smsapi_nogate_exception:
            message = _(u"Ошибка СМС-сервиса: оператор телефона не обслуживается")
        except sms24x7.smsapi_auth_exception as excpt:
            message = _(u"Ошибка СМС-сервиса: аутентификация, код: %s") % excpt
        except sms24x7.smsapi_spam_exception as excpt:
            message = _(u"Ошибка СМС-сервиса: спам, код: %s") % excpt
        except sms24x7.smsapi_encoding_exception as excpt:
            message = _(u"Ошибка СМС-сервиса: кодировка, код: %s") % excpt
        except sms24x7.smsapi_other_exception as excpt:
            message = _(u"Ошибка СМС-сервиса: иная, код: %s") % excpt
        # Все остальные идут с нормальной тестовой расшифрровкой
        except sms24x7.smsapi_exception as excpt:
            message = _(u"Ошибка СМС-сервиса, %s") % excpt
    if message:
        email_error_text += u"\n%s\n%s" % \
                            (message, _(u"Справка по числовому коду: https://outbox.sms24x7.ru/api_manual/errors.html"), )
        email_from = settings.DEFAULT_FROM_EMAIL
        email_to = (settings.DEFAULT_FROM_EMAIL, )
        email_subject = _(u'Ошибка СМС-сервиса при отправке на %s') % phone_number
        email_text = email_error_text
        EmailMessage(email_subject, email_text, email_from, email_to, ).send()
    return bool(not message), message
