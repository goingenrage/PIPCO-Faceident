from scripts import interfacedb


db_directory = '/home/michael/semesterprojekt.db'
tmp_directory = '/home/michael/tmp/'

if __name__ == "__main__":
    try:
        interfacedb.initialize(db_directory, tmp_directory)
        x = interfacedb.delete_action_by_name('test')
        #print(len(x))
    except Exception as e:
        print(e)
