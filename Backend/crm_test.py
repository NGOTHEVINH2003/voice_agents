import os
from dotenv import load_dotenv
from hubspot import HubSpot
from hubspot.crm.owners import ApiException

load_dotenv()

HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")

api_client = HubSpot(access_token=HUBSPOT_ACCESS_TOKEN)

try:
    # Gọi API đơn giản để test
    owners = api_client.crm.owners.owners_api.get_page()
    print("✅ Kết nối thành công với HubSpot!")
    for o in owners.results:
        print(f"- {o.first_name} {o.last_name} ({o.email})")
except ApiException as e:
    print("❌ Lỗi khi kết nối tới HubSpot:")
    print(e)