from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from uvicorn import run
from variables import API_srv_port
from backend import DataParser,\
    json_ops_daemon_thread
from _base import configure_logger
from logging import getLogger
from traceback import format_exc

if __name__ == '__main__':

    configure_logger()
    _log = getLogger()

    # app Setup
    app = FastAPI()
    data_parser = DataParser()
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

    @app.get("/total_supply")
    def get_total_supply():
        try:
            return data_parser.return_latest_total_supply()
        except:
            _log.error('Error while returning total_supply. Will return NA instead. Reason: \n{}'.format(format_exc(chain=False)))
            return 'NA'

    @app.get("/circulating_supply")
    def get_circulating_supply():
        try:
            return data_parser.return_latest_circulating_supply()
        except:
            _log.error('Error while returning circulating_supply. Will return NA instead. Reason: \n{}'.format(format_exc(chain=False)))
            return 'NA'

    # Infinite Loop
    run(app,
        host="0.0.0.0",
        port=API_srv_port)