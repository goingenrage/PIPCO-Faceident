from src import test123


class Main:

    @staticmethod
    def main():
       ##### gesichtsidentifikation = Gesichtsidentifikation()
       ##### #gesichtsidentifikation.load_approved_faces()
       ##### gesichtsidentifikation.start();

       print("Preparing data...")
       faces, labels = test123.prepare_training_data("/home/reichenecker/Dokumente/Semesterprojekt2019/test")
       print("Data prepared")

       # print total faces and labels
       print("Total faces: ", len(faces))
       print("Total labels: ", len(labels))


if __name__ == "__main__":
    Main.main()