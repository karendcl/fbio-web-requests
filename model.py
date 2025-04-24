
import states
import automation
import datetime

class WebPostRequest:
    def __init__(self,
                 user_name,
                 user_email,
                 topic,
                 message,
                 images,
                 department,
                 file):
        self.user_name = user_name
        self.user_email = user_email
        self.topic = topic
        self.message = message
        self.images = images
        self.file = file
        self.state = states.PENDING
        self.department = department
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.code = hash(f"{self.user_name}{self.topic}{self.department}{self.message}")

        self.save_to_json()

    def save_to_json(self):

        new_data = {
            'code': self.code,
            'user_name': self.user_name,
            'user_email': self.user_email,
            'topic': self.topic,
            'message': self.message,
            'images': self.images,
            'file': self.file,
            'state': self.state,
            'department': self.department,
            'timestamp': self.timestamp
        }

        automation.update_json(new_data=new_data)


