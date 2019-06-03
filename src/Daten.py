

class Daten:
    __instance = None
    def __init__(self):
        self.__instance = self
        self.__image = None

    @staticmethod
    def get_instance():
        if Daten.__instance is None:
            Daten.__instance = Daten()
        return Daten.__instance

    def set_image(self, image):
        self.__image = image

    def get_image(self):
        #print(self.__image)
        return self.__image