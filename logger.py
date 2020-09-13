from datetime import datetime
import os

class Logger:
    def __init__(self, output_file_name):
        self.active_class = "Main"
        self.last_active_class = "Main"
        if not os.path.isdir("./log"):
            os.mkdir("log")
        
        self.log_file = open("log/" + output_file_name, "w")
        self.debug_file = open("log/debug.txt", "w")
        
        self.log_file.write("Log file created at: " + str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")) + "\n")

    def __del__(self):
        self.log_file.write("~~~~~~~~~~~~~~ END OF LOG ~~~~~~~~~~~~~~\n")
        self.log_file.close()
        self.debug_file.close()

    def set_active_class(self, class_name):
        self.last_active_class = self.active_class
        self.active_class = class_name
        self.info("Changed active class to: " +self.active_class)

    def get_active_class(self):
        return self.active_class

    def reset_active_class(self):
        self.active_class = self.last_active_class

    def warn(self, msg):
        self.log_file.write("[WARN] - " +self.active_class +": " + msg +"\n")

    def info(self, msg):
        self.log_file.write("[INFO] - " +self.active_class +": " + msg +"\n")

    def error(self, msg):
        self.log_file.write("[ERROR] - " +self.active_class +": " + msg +"\n")

    def debug(self, msg):
        self.debug_file.write("[DEBUG] - " +self.active_class +": " + msg +"\n")

    def _get_current_time(self):
        return str(datetime.now().strftime("%H:%M:%S"))