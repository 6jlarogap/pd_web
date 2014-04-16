# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _

from sms_service import sms24x7

def send_sms(phone_number, text, email_error_text=''):
    """
    Отправить СМС с текстом text на номер phone_number (Decimal or string!)
    
    *   email_text - текст сообщения в службу поддержки, если передача СМС не получилась
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
            message = _(u"Оператор телефона не обслуживается")
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
        except sms24x7.smsapi_nogate_exception:
            message = _(u"Оператор телефона не обслуживается")
        except sms24x7.smsapi_exception:
            message = _(u"Произошла ошибка. Мы известим Вас о восстановлении сервиса")
            email_from = settings.DEFAULT_FROM_EMAIL
            email_to = (settings.DEFAULT_FROM_EMAIL, )
            email_subject = _(u'Ошибка СМС сервиса')
            email_text = email_error_text
            EmailMessage(email_subject, email_text, email_from, email_to, ).send()
    return bool(not message), message
