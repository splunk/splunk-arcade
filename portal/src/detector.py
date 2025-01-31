import json

import pytz
class Detector:
    from datetime import datetime

    from pytz import timezone

    def __init__(self, data):
        self.questiontoship = {}


        try:

            #self.questiontoship["answerscore"] = data["inputs"]["A"]["value"]
            #self.questiontoship["questionbody"] = data["messageBody"]

            #self.questiontoship["time"] = Detector.datetime.fromisoformat(data["timestamp"]).astimezone(Detector.timezone('America/Los_Angeles'))
            #self.questiontoship["player_name"] = data["dimensions"]["player_name"]
            #self.questiontoship["question_name"] = "whats-the-high-score"
            #self.questiontoship["imageurl"] = data["imageUrl"]
            #self.questiontoship["title"] = data["dimensions"]["title"]
            #self.questiontoship["version"] = data["dimensions"]["version"]
            #self.questiontoship["message"] = data["messageBody"]
            #self.questiontoship["srcDetector"] = data["detector"]
            #self.questiontoship["detectorUrl"] = data["detectorUrl"]
            #self.questiontoship["NotifyAll"] = "True"
            #self.questiontoship["isQuizTopic"] = "True"
            #rawquestion = data["messageBody"]



            print(json.loads(data["messageBody"].replace("\\\"", "\"")))


        except:
            print("Something went wrong")




    def post_question_notification(self):

        try:

            #print(self.questiontoship)
            print(f"We have received data from the {self.questiontoship['srcDetector']} detector.")
            #Todo: Post Notification and Question to Redis?
            return f"We have received data from the {self.questiontoship['srcDetector']} detector."
        except:
            return "Looks Like the data is Bananas"


















