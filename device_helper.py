import csv
import logging

logger = logging.getLogger(__name__)

model_datas = []

with open("./models.csv",encoding="utf-8") as file_datas:
    datas = csv.reader(file_datas)
    i = 1
    for data in datas:
        if i == 1:
            i += 1
            continue
        #print(data)
        i += 1
        model_datas.append([data[0],data[2],data[5],data[6]])
        