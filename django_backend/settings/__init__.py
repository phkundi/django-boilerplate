from .base import *

if from_env("ENVIRONMENT") == "production":
    from .production import *
elif from_env("ENVIRONMENT") == "staging":
    from .staging import *
else:
    from .development import *
