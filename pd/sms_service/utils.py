from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from users.models import Org, Profile

from sms_service import sms24x7

from pd.utils import EmailMessage

def send_sms(
        phone_number,
        text,
        email_error_text='',
        user=None,
        sender_name=None,
        error_email=True,
    ):
    """
    Отправить СМС с текстом text на номер phone_number (Decimal or string!)
    
    *   email_error_text - текст сообщения в службу поддержки, если передача СМС не получилась.
        К нему добавляется сообщение СМС-сервиса
    *   user - инициатор отправки сообщения. Если пользователь не смог получить СМС
        по причине "сотовый оператор не подключен", то информация об user и его организации
        включается в письмо, а на адрес user.email или user.profile.org.email идет копия
        сообщения
    *   sender_name: заголовок смс, от кого. Обрезается до 11 символов.
        По умолчанию PohoronnoeD
    *   error_email: отправлять ли письмо при ошибке смс сервиса

    -   функцию вызывать, если not settings.DEBUG!
    
    -   Возвращает кортеж:
            sent,   True, если успешно
            message, сообщение: пустое, если успешно, иначе причину отказа в отправке
    """
    if settings.DO_NOT_SEND_SMS:
        return True, ''
    phone_number = str(phone_number)
    default_serv = your_serv = None
    message = ''
    no_gate = False
    email_copy = None
    have_code = False
    for serv in settings.SMS_SERVICE:
        if serv['country_code'] == 'default':
            default_serv = serv
        if phone_number.startswith(serv['country_code']):
            your_serv = serv
    if not your_serv:
        if default_serv:
            your_serv = default_serv
        else:
            message = _("Оператора телефона нет в настройках системы")
    if not message:
        have_code = True
        try:
            smsapi = sms24x7.smsapi(your_serv['user'], your_serv['password'])
            print('DEBUG: send_sms, country_code=%s, user=%s' % (
                your_serv['country_code'],
                your_serv['user'],
            ))
            smsapi.push_msg(
                text,
                phone_number,
                # 11 chars max
                sender_name=sender_name and sender_name[:11] or 'PohoronnoeD',
                nologin = True
            )
        # Некоторые ошибки идут с нормальной расшифровкой, но иные только
        # с цифровыми кодами, приходится перечислять
        except sms24x7.smsapi_nogate_exception:
            message = _("Ошибка СМС-сервиса: сотовый оператор не подключен")
            no_gate = True
            have_code = False
        except sms24x7.smsapi_auth_exception as excpt:
            message = _("Ошибка СМС-сервиса: аутентификация, код: %s") % excpt
        except sms24x7.smsapi_spam_exception as excpt:
            message = _("Ошибка СМС-сервиса: спам, код: %s") % excpt
        except sms24x7.smsapi_encoding_exception as excpt:
            message = _("Ошибка СМС-сервиса: кодировка, код: %s") % excpt
        except sms24x7.smsapi_other_exception as excpt:
            message = _("Ошибка СМС-сервиса: иная, код: %s") % excpt
        # Все остальные идут с нормальной тестовой расшифрровкой
        except sms24x7.smsapi_exception as excpt:
            message = _("Ошибка СМС-сервиса, %s") % excpt
    if message and error_email:
        if no_gate and user:
            try:
                email_error_text += "\n\n%s: %s / %s / %s\n" % (
                    _('Регистратор'),
                    user.username,
                    user.profile.full_name(),
                    user.profile.org.name,
                )
                email_copy = user.email or user.profile.org.email or None
            except (AttributeError, Profile.DoesNotExist, ):
                pass
        email_error_text += "\n%s%s" % (
            message,
            "\n%s" % _("Справка по числовому коду: https://outbox.sms24x7.ru/api_manual/errors.html") \
                    if have_code else '',
        )
        email_from = settings.DEFAULT_FROM_EMAIL
        email_to = settings.SUPPORT_EMAILS
        email_subject = _('Ошибка СМС-сервиса при отправке на %s') % phone_number
        email_text = email_error_text
        kwargs = dict()
        if email_copy:
            kwargs['cc'] = (email_copy, )
        email_message = EmailMessage(email_subject, email_text, email_from, email_to, **kwargs ).send()
    return bool(not message), message
