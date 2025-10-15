# salt_and_light/settings/__init__.py
import os

env = os.getenv('DJANGO_ENV', 'dev')
if env == 'prod':
    from .prod import *
elif env == 'local':
    from .local import *
else:
    from .dev import *