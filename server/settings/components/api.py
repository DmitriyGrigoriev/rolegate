from server.settings.components import config


DISABLE_THROTTLING = config("DISABLE_THROTTLING", cast=bool, default=config("DEBUG", cast=bool, default=False))

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Custom JWT Authentication Middleware
        'server.apps.authentication.authentication.JWTAuthentication',
    ],
    "DEFAULT_VERSION": "v1.0",
    "ALLOWED_VERSION": {'v1.0'},
    "VERSION_PARAM": "version",

    "DEFAULT_PAGINATION_CLASS": "server.apps.main.pagination.AppPagination",
    "EXCEPTION_HANDLER": "server.apps.main.exceptions.app_service_exception_handler",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_RATES": {
        "anon-auth": "10/min",
        "public-id": "60/hour",
        "notion-materials": "100/hour",
        "promocode": "100/hour",
        "purchase": "100/hour",
        "order-refund": "5/day",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DATE_INPUT_FORMATS": [
        '%d.%m.%Y',  # '25.10.2021'
        '%d.%m.%y',  # '25.10.21'
    ]
}
DRF_RECAPTCHA_SECRET_KEY = config("RECAPTCHA_SECRET_KEY", cast=str, default="")
DRF_RECAPTCHA_TESTING = DRF_RECAPTCHA_TESTING_PASS = not config("RECAPTCHA_ENABLED", cast=bool, default=True)

# Set up drf_spectacular, https://drf-spectacular.readthedocs.io/en/latest/settings.html
SPECTACULAR_SETTINGS = {
    "TITLE": "Rolegate API Документация",
    "DESCRIPTION": "API для аутентификации и управления ролями",
    "VERSION": "1.0.0",
    'SERVE_INCLUDE_SCHEMA': False,

    # Настройка схем безопасности
    'SECURITY': [{'bearerAuth': []}],
    'COMPONENTS': {
        'securitySchemes': {
            'bearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'Введите JWT токен, полученный при логине'
            }
        }
    },

    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    'COMPONENT_SPLIT_REQUEST': True,

    # Дополнительные настройки
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        # Сохраняет токен между обновлениями страницы
        'persistAuthorization': True,
        'displayOperationId': False,
    },
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
    ],
}
