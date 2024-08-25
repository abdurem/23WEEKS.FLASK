## DEVELOPMENT ##

import os
import ssl
from app import create_app

# ssl._create_default_https_context = ssl._create_unverified_context

# app = create_app()

# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 8000))
#     app.run(host="0.0.0.0", port=port, debug=True, use_reloader=True)

## PRODUCTION ##

from app import create_app
import patch

app = create_app()

if __name__ == "__main__":
    app.run()