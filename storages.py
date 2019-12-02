import os.path
import jsonpickle
import json
from toolz import filter
from models import *


class JsonStorage:
    def __init__(self):
        self.fileName = 'data.json'
        self.filePath = f'data/{self.fileName}'
        self.rootName = 'annotations'
        self.items = self.getAll()

    def insert(self, model):
        filteredItems = list(
            filter(
                lambda item: item.imageName == model.imageName,
                self.items))

        if len(filteredItems) > 0:
            firstElemet = filteredItems[0]
            firstElemet.boxes = firstElemet.boxes + model.boxes
        else:
            self.items.append(model)

        self.saveIntoFile()

    def getAll(self):
        if not os.path.isfile(self.filePath):
            open(self.filePath).close()

        if os.stat(self.filePath).st_size == 0:
            return []

        with open(self.filePath) as json_file:
            annotationsList = json.load(json_file)[self.rootName]

            return [
                Annotation(
                    a['imageName'],
                    a['width'],
                    a['height'], [
                        Box(
                            box['lowerRightX'],
                            box['lowerRightY'],
                            box['upperLeftX'],
                            box['upperLeftY'])
                        for box in a['boxes']])
                for a in annotationsList]

        # return jsonpickle.decode(jsonData)[self.rootName]

    def saveIntoFile(self):
        with open(self.filePath, 'w', encoding='utf-8') as f:
            f.write(jsonpickle.encode(
                {self.rootName: self.items}, unpicklable=False))

        # with open(self.filePath, 'w') as outfile:
        #     json.dump(jsonpickle.encode(
        #         {self.rootName: self.items}, unpicklable=False), outfile)
