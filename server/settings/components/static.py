import os.path
from server.settings.components import BASE_DIR
from server.settings.components import config

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
MEDIA_URL = '/media/'
SMEDIA_URL = '/smedia/'

# Проверяем режим работы Django
DJANGO_ENV = config("DJANGO_ENV", default="development")

if DJANGO_ENV != 'production':
    # Настройки для разработки
    MEDIA_ROOT = BASE_DIR.joinpath('media')
    SMEDIA_ROOT = BASE_DIR.joinpath('smedia')
    STATIC_URL = config("STATIC_URL", default="/static/")
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    STATICFILES_DIRS = [BASE_DIR / 'static']
else:
    # Настройки для продакшена
    # используется для управления путями во время collectstatic и docker deploy
    _COLLECTSTATIC_DRYRUN = config(
        'DJANGO_COLLECTSTATIC_DRYRUN', cast=bool, default=True,
    )

    if _COLLECTSTATIC_DRYRUN:
        # Режим dry-run: используем пути внутри контейнера для collectstatic
        MEDIA_ROOT = '.media'
        SMEDIA_ROOT = '.smedia'
        STATIC_URL = '/staticfiles/'
        STATIC_ROOT = '../../staticfiles'
    else:
        # Режим реального развертывания: используем относительные пути
        MEDIA_ROOT = '/var/www/django/media'
        SMEDIA_ROOT = '/var/www/django/smedia'
        STATIC_URL = config("STATIC_URL", default="/static/")
        STATIC_ROOT = '/var/www/django/static'

    # В продакшене также используем статические файлы из папки static
    STATICFILES_DIRS = [BASE_DIR / 'static']

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # Django components
    # 'django_components.finders.ComponentsFileSystemFinder',
)
