from Gesichtsidentifikation import Gesichtsidentifikation

class Main:

    @staticmethod
    def main():
        gesichtsidentifikation = Gesichtsidentifikation()
        #gesichtsidentifikation.load_approved_faces()
        gesichtsidentifikation.start();


if __name__ == "__main__":
    Main.main()