import os
from dotenv import load_dotenv

load_dotenv()
# Set DEBUG based on the environment
level = os.environ.get('level', 'local')
if level == 'local':
    from .base_local import *
elif level == 'development':
    from .dev import *

# elif level=="prod":
#     from .production import *

else:
    raise ValueError("Add level variable in .env file")
