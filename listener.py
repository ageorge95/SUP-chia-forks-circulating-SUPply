from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from uvicorn import run
from variables import API_srv_port
from backend import json_ops_class,\
    json_ops_daemon_thread
from _base import configure_logger
from logging import getLogger

if __name__ == '__main__':

    configure_logger()
    _log = getLogger()

    # app Setup
    app = FastAPI()
    json_ops = json_ops_class()
    json_ops_daemon_thread().loop()

    @app.get("/",
                 response_class=HTMLResponse,
                 include_in_schema=False)
    async def index():
        return """
            <html>
                <head>
                    <title>HDDcoin info API server</title>
                </head>
                <body>
                <a href="/docs">Swagger UI</a><br/>
                (c) ageorge95
                </body>
            </html>
        """

    _log.info('app setup completed')

    # Infinite Loop
    run(app,
        host="0.0.0.0",
        port=API_srv_port)