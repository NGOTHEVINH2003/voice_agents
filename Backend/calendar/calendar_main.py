from googleapiclient.errors import HttpError

import json
import os

from calendar_crud import create_event, get_event, delete_event

# Lấy đường dẫn tuyệt đối tới file template.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(BASE_DIR, "template.json")

# Đọc nội dung file JSON
with open(template_path, "r", encoding="utf-8") as f:
    template_data = json.load(f)

def main():
    try:
        # test create event
        event = create_event(template_data)
        print(f"event created: %{event.get('htmlLink')}")

        # test get event
        # event = get_event("3gjc4jph9r6mm2i1ad4cg6f51k_20150528T160000Z")
        # print(event)
        
        # test delete event
        # event = delete_event("3gjc4jph9r6mm2i1ad4cg6f51k_20150528T160000Z")
        # print(event)

        # test update event


    except HttpError as error:
        print("An error occurred: ", error)

if __name__ == "__main__":
    main()