# Local
from .base import *  # noqa type: ignore NOSONAR
from .base import ALLOWED_HOSTS, INSTALLED_APPS, MIDDLEWARE

DEBUG = True

ALLOWED_HOSTS += ["host.docker.internal"]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
]

INSTALLED_APPS += ["django_extensions", "debug_toolbar"]

MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

# Setting up debug toolbar INTERNAL_IPS for Docker
if DEBUG:
    # Built-in
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + [
        "127.0.0.1",
    ]
