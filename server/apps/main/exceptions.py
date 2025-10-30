# import sentry_sdk
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler
from django.utils.translation import gettext_lazy as _

_HTTP_550_PROTECTED_ERROR = 550

class AppServiceException(Exception):
    """Inherit your custom service exceptions from this class."""


class AppsProtectedError(APIException):
    status_code = _HTTP_550_PROTECTED_ERROR
    default_detail = _('Cannot delete some instances of model.')
    default_code = 'protected_error'

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code

        super(AppsProtectedError, self).__init__(detail=detail, code=code)


def app_service_exception_handler(exc: Exception, context: dict) -> Response | None:
    """
    Transform service errors to standard 400 errors and
    Log all DRF exceptions to sentry, including ValidationErrors
    """


    # sentry_sdk.capture_exception(exc)

    if not isinstance(exc, AppServiceException):
        return exception_handler(exc, context)

    return Response(status=400, data={"serviceError": str(exc)})
