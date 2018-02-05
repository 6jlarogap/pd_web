05.02.2018
Eugene Suprun

Взято из django-nocaptcha-recaptcha 0.0.20,
    https://pypi.python.org/pypi/django-nocaptcha-recaptcha/

Вынужден был внести в проект, а не грузить в окружение
(source ... pip install ...), чтоб подправить здесь:
    
    - client.py:
        вместо:
        
        from django.utils.encoding import force_text
        
        есть:

        try:
            from django.utils.encoding import force_text
        except ImportError:
            from django.utils.encoding import force_unicode as force_text
