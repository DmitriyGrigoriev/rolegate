import os

from server import settings

DOCS_ROOT = os.path.join(settings.BASE_DIR, 'docs/_build/html')

# В продакшене документация недоступна
DOCS_ACCESS = 'disabled'

# Альтернативный подход - можете использовать вместо 'disabled'
# DOCS_ACCESS = 'staff'  # только для staff пользователей в продакшене
