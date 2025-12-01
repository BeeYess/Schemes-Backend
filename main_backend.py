from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

# Allow only frontend later after deploy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # will update to your Vercel domain after deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputData(BaseModel):
    cityId: str
    phoneNumber: str
    customerId: str
    lenderId: str
    loanAmount: str
    loanType: str | None = None
    loanAppId: str | None = None
    source: str

@app.get("/")
def health_check():
    return {"status": "Backend OK"}

@app.post("/process")
def process_data(data: InputData):

    cleaned_source = ",".join([s.strip().capitalize() for s in data.source.split(",")])

    payload = {
        "cityId": data.cityId,
        "phoneNumber": data.phoneNumber,
        "customerId": data.customerId,
        "lenderId": data.lenderId,
        "fulfillmentChannels": ["doorstep", "digital-platforms"],
        "groupTags": {"exclusiveList": [], "inclusiveList": []},
        "loanAmount": data.loanAmount,
        "loanType": data.loanType or "fresh-loan",
        "schemeRanking": True,
        "schemeRankingGroupTags": {
            "exclusiveList": [],
            "inclusiveList": ["Pricing"]
        },
        "source": cleaned_source
    }

    if data.loanType == "takeover-loan" and data.loanAppId:
        payload["loanApplicationId"] = data.loanAppId

    headers = {
        "Authorization": "Basic NjBkMGEyM2U4MTZmZjgzZmY2YWZiMmFmOlRWMkpBNllS",
        "Content-Type": "application/json",
    }

    url = "https://casapi.rupeek.com/api/v1/suggested-schemes"

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        resp_json = response.json()
    except Exception as e:
        return {"error": f"API failed: {str(e)}"}

    reference_names = set()

    for scheme in resp_json.get("data", {}).get("schemes", []):
        if scheme.get("referenceName"):
            reference_names.add(scheme["referenceName"])

        if scheme.get("pricingInfo", {}).get("referenceName"):
            reference_names.add(scheme["pricingInfo"]["referenceName"])

        for config in scheme.get("displayConfigs", []):
            props = config.get("displayProperties", {})
            if props.get("referenceName"):
                reference_names.add(props["referenceName"])

    reference_list = sorted(reference_names)

    if not reference_list:
        return {"message": "No schemes found"}

    return {"referenceNames": reference_list}
