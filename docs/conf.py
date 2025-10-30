# Конфигурационный файл для сборки документации, создан
# с помощью sphinx-quickstart

# Этот файл выполняется с помощью execfile() с текущей директорией, установленной
# на директорию, содержащую этот файл.

# Обратите внимание, что в этом автоматически сгенерированном файле
# присутствуют не все возможные конфигурационные значения.

# Все конфигурационные значения имеют значения по умолчанию; закомментированные
# значения показывают значения по умолчанию.

# Если расширения (или модули для документирования с помощью autodoc) находятся в другой директории,
# добавьте эти директории в sys.path здесь. Если директория относительна корня документации,
# используйте os.path.abspath для преобразования в абсолютный путь, как показано здесь.

import os
import sys

import django
import tomli

# Нам нужно, чтобы модуль `server` был доступен для импорта отсюда:
sys.path.insert(0, os.path.abspath('..'))

# Настройка Django, все зависимости должны быть установлены для успешного выполнения:
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

os.environ['NPLUSONE_DISABLE'] = '1'
# Устанавливаем флаг сборки Sphinx
os.environ['SPHINX_BUILD'] = '1'
os.environ['READTHEDOCS'] = '1'

# -- Информация о проекте -----------------------------------------------------

def _get_project_meta() -> dict[str, str]:  # lying abour return type
    with open('../pyproject.toml', mode='rb') as pyproject:
        return tomli.load(pyproject)['tool']['poetry']


pkg_meta = _get_project_meta()
project = pkg_meta['name']

# Короткая версия X.Y
version = pkg_meta['version']
# Полная версия, включая теги alpha/beta/rc
release = version


# -- Общая конфигурация ------------------------------------------------

# Если документации требуется минимальная версия Sphinx, укажите её здесь.
needs_sphinx = '7.2'

# Добавьте здесь имена модулей расширений Sphinx в виде строк. Это могут быть
# расширения, поставляемые вместе со Sphinx (именуемые 'sphinx.ext.*'), или ваши собственные.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx.ext.napoleon',

    # 3rd party, порядок имеет значение:
    # https://github.com/wemake-services/wemake-django-template/issues/159
    'sphinx_autodoc_typehints',
    'sphinx_togglebutton',
    # https://myst-parser.readthedocs.io/en/latest/syntax/roles-and-directives.html#roles-directives
    'myst_parser',
]

# Настройки ToggleButton
togglebutton_hint = "Кликните для просмотра"
togglebutton_hint_hide = "Кликните для скрытия"

# Настройки Napoleon
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_custom_sections = [
    ('Template', 'example'),
    ('Methods', 'params'),
    ('Attributes', 'params'),
    ('Context Variables', 'params'),
    ('Template Parameters', 'params'),
    ('Permissions', 'notes'),
]

# Настройки autodoc
autodoc_default_options = {
    'members': False,
    'undoc-members': False,
    'private-members': False,
    'special-members': False,
    'exclude-members': 'css, js, css_file, js_file, media, template, template_file',
}

# Мокирование зависимостей
autodoc_mock_imports = [
    'django',
    'django_components',
    'crispy_forms',
    'redis',
]

# Если True, Sphinx будет предупреждать о всех ссылках,
# где цель не может быть найдена. По умолчанию `False`.
# Вы можете временно активировать этот режим с помощью флага `-n` в командной строке.
nitpicky = False

# Не нужно документировать, это сторонний класс из django_components
nitpick_ignore = [
    (
        ('py:class', 'django_components.component.Component'),
        ('py:class', 'server.components.component.BaseComponent'),
        ('py:class', 'server.components.component.BaseColumnComponentMixin'),
        ('py:class', 'django_tables2.utils.AttributeDict'),
        ('py:class', 'django_tables2.utils.A'),
    ),
]

# Добавьте пути, содержащие шаблоны, сюда, относительно этой директории.
templates_path = ['_templates']

# Суффиксы исходных файлов.
# Можно указать несколько суффиксов в виде списка строк:
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Главный документ toctree.
master_doc = 'index'

# Язык для содержимого, автоматически генерируемого Sphinx. Смотрите документацию
# для списка поддерживаемых языков.
#
# Это также используется, если вы переводите содержимое через каталоги gettext.
# Обычно язык устанавливается из командной строки в таких случаях.
language = 'ru'

# Список шаблонов, относительно исходной директории, которые соответствуют файлам и
# директориям, игнорируемым при поиске исходных файлов.
# Эти шаблоны также влияют на html_static_path и html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Название стиля Pygments (для подсветки синтаксиса), который будет использоваться.
pygments_style = 'sphinx'

# Если True, `тодо` и `todoList` будут генерировать вывод, иначе они ничего не выведут.
todo_include_todos = True


# -- Настройки для вывода HTML ----------------------------------------------

# Тема для страниц HTML и HTML Help. Смотрите документацию для
# списка встроенных тем.
# href: https://www.sphinx-doc.org/en/master/usage/theming.html
html_theme = 'sphinx_rtd_theme'

# Добавьте пути, содержащие пользовательские статические файлы (например, таблицы стилей), сюда,
# относительно этой директории. Они копируются после встроенных статических файлов,
# поэтому файл с именем "default.css" перезапишет встроенный "default.css".
jquery_use_sri = True
html_permalinks_icon = '#'
html_static_path = ['_static']
