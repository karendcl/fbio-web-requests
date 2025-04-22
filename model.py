import json

import states


class WebPostRequest:
    def __init__(self,
                 user_name,
                 user_email,
                 topic,
                 message,
                 images,
                 department):
        self.user_name = user_name
        self.user_email = user_email
        self.topic = topic
        self.message = message
        self.images = images
        self.state = states.PENDING
        self.department = department

        self.save_to_json()

    def save_to_json(self):
        """Load the json 'data' and append the new post request to it."""
        # Load the json file
        with open('data.json', 'r') as f:
            data = json.load(f)

        # Append the new post request to the data
        data.append({
            'user_name': self.user_name,
            'user_email': self.user_email,
            'topic': self.topic,
            'message': self.message,
            'images': self.images,
            'state': self.state,
            'department': self.department
        })

        # Save the data back to the json file
        with open('data.json', 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=True)