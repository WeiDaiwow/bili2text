from src.selfcheck import SelfCheck
from src.config import SERVER_HOST, SERVER_PORT, DEBUG_MODE
from src.webserver.server import app

if __name__ == "__main__":
    # SelfCheck().run()
    app.run(
        host=SERVER_HOST,
        port=SERVER_PORT,
        debug=DEBUG_MODE
    )