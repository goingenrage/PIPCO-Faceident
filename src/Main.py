from Gesichtsreidentifikation import Gesichtsreidentifikation


class Main:

    @staticmethod
    def main():

        gesichtsreidentifikation = Gesichtsreidentifikation('config.cfg')
        gesichtsreidentifikation.start()
        gesichtsreidentifikation.join()


if __name__ == "__main__":
    Main.main()