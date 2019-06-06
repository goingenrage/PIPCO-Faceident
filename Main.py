from src.Gesichtsreidentifikation import Gesichtsreidentifikation
from src.Webserver import Webserver
import logging
class Main:

    @staticmethod
    def main():
        logging.basicConfig(format='%(levelname)s:%(asctime)s %(message)s', filename='./logs/gesichtsreidentifikation.log', level=logging.DEBUG)
        gesichtsreidentifikation = Gesichtsreidentifikation('config.cfg') #Starte Thread mit bestimmten Config-file
        gesichtsreidentifikation.start()
        my_webserver = Webserver()
        my_webserver.app.run(port=8002, host='0.0.0.0', debug=False, threaded=True)
        gesichtsreidentifikation.join()


if __name__ == "__main__":
    Main.main()