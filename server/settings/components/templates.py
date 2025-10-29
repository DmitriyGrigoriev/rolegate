from server.settings.components import BASE_DIR

# Templates
# https://docs.djangoproject.com/en/4.2/ref/templates/api

TEMPLATES = [{
    # 'APP_DIRS': True,
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [
        # Contains plain text templates, like `robots.txt`:
        BASE_DIR.joinpath('server', 'templates'),
    ],
    'OPTIONS': {
        'context_processors': [
            # Default template context processors:
            'django.contrib.auth.context_processors.auth',
            'django.template.context_processors.debug',
            'django.template.context_processors.i18n',
            'django.template.context_processors.media',
            'django.contrib.messages.context_processors.messages',
            'django.template.context_processors.request',
        ],
        'loaders': [(
            'django.template.loaders.cached.Loader', [
            # Default Django loader
            'django.template.loaders.filesystem.Loader',
            # Inluding this is the same as APP_DIRS=True
            'django.template.loaders.app_directories.Loader',
            # Components loader
            # 'django_components.template_loader.Loader',
            ]
        )],
        # 'builtins': [
        #     'django_components.templatetags.component_tags',
        #     'django_expr.templatetags.expr',
        # ],
        # 'libraries': {
        #     'table_tags': 'server.templatetags.table_tags',
        #     'template_tags': 'server.templatetags.template_tags',
        # }
    },
}]
