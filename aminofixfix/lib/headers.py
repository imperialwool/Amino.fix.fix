from .helpers import signature, str_uuid4

BASIC_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Host": "service.aminoapps.com",
    "Connection": "keep-alive",
    "NDCLANG": "en"
}

def additionals(data = None, user_agent = None, content_type = None, deviceId: str = None, sig: str = None, sid: str = None, auid: str = None):
    headers = {
        "AUID": auid or str_uuid4()
    }

    if user_agent:
        headers['User-Agent'] = user_agent
    if deviceId:
        headers["NDCDEVICEID"] = deviceId
    if data:
        headers["Content-Length"] = str(len(data))
        headers["NDC-MSG-SIG"] = signature(data)
    if sid:
        headers["NDCAUTH"] = f"sid={sid}"
    if sig:
        headers["NDC-MSG-SIG"] = sig

    if isinstance(content_type, str) and content_type.lower() == "default":
        pass # letting HTTPX do its job
    elif content_type: 
        headers["Content-Type"] = content_type
    else:
        headers["Content-Type"] = "application/json; charset=utf-8"

    return headers

class Tapjoy:
    @staticmethod
    def Headers() -> dict:
        return {
            "cookies": "__cfduid=d0c98f07df2594b5f4aad802942cae1f01619569096",
            "authorization": "Basic NWJiNTM0OWUxYzlkNDQwMDA2NzUwNjgwOmM0ZDJmYmIxLTVlYjItNDM5MC05MDk3LTkxZjlmMjQ5NDI4OA==",
            "X-Tapdaq-SDK-Version": "android-sdk_7.1.1",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; Redmi Note 9 Pro Build/QQ3A.200805.001; com.narvii.amino.master/3.4.33585)"
        }

    @staticmethod
    def Data(userId: str = None) -> str:
        data = '{"reward":{"ad_unit_id":"t00_tapjoy_android_master_checkinwallet_rewardedvideo_322","credentials_type":"publisher","custom_json":{"hashed_user_id":"[$UID$]"},"demand_type":"sdk_bidding","event_id":"[$EID$]","network":"tapjoy","placement_tag":"default","reward_name":"Amino Coin","reward_valid":true,"reward_value":2,"shared_id":"4d7cc3d9-8c8a-4036-965c-60c091e90e7b","version_id":"1569147951493","waterfall_id":"4d7cc3d9-8c8a-4036-965c-60c091e90e7b"},"app":{"bundle_id":"com.narvii.amino.master","current_orientation":"portrait","release_version":"3.4.33585","user_agent":"Dalvik\\/2.1.0 (Linux; U; Android 10; G8231 Build\\/41.2.A.0.219; com.narvii.amino.master\\/3.4.33567)"},"device_user":{"country":"US","device":{"architecture":"aarch64","carrier":{"country_code":255,"name":"Vodafone","network_code":0},"is_phone":true,"model":"GT-S5360","model_type":"Samsung","operating_system":"android","operating_system_version":"29","screen_size":{"height":2300,"resolution":2.625,"width":1080}},"do_not_track":false,"idfa":"0c26b7c3-4801-4815-a155-50e0e6c27eeb","ip_address":"","locale":"ru","timezone":{"location":"Asia\\/Seoul","offset":"GMT+02:00"},"volume_enabled":true},"session_id":"7fe1956a-6184-4b59-8682-04ff31e24bc0","date_created": 1633283996}'
        return data.replace("[$UID$]", userId).replace("[$EID$]", str_uuid4())
    
    # Just in case
    @staticmethod
    def Data_Legacy(userId: str = None) -> dict:
        return {
            "reward": {
                "ad_unit_id": "t00_tapjoy_android_master_checkinwallet_rewardedvideo_322",
                "credentials_type": "publisher",
                "custom_json": {
                    "hashed_user_id": userId
                },
                "demand_type": "sdk_bidding",
                "event_id": str_uuid4(),
                "network": "tapjoy",
                "placement_tag": "default",
                "reward_name": "Amino Coin",
                "reward_valid": True,
                "reward_value": 2,
                "shared_id": "4d7cc3d9-8c8a-4036-965c-60c091e90e7b",
                "version_id": "1569147951493",
                "waterfall_id": "4d7cc3d9-8c8a-4036-965c-60c091e90e7b"
            },
            "app": {
                "bundle_id": "com.narvii.amino.master",
                "current_orientation": "portrait",
                "release_version": "3.4.33585",
                "user_agent": "Dalvik\/2.1.0 (Linux; U; Android 10; G8231 Build\/41.2.A.0.219; com.narvii.amino.master\/3.4.33567)"
            },
            "device_user": {
                "country": "US",
                "device": {
                    "architecture": "aarch64",
                    "carrier": {
                        "country_code": 255,
                        "name": "Vodafone",
                        "network_code": 0
                    },
                    "is_phone": True,
                    "model": "GT-S5360",
                    "model_type": "Samsung",
                    "operating_system": "android",
                    "operating_system_version": "29",
                    "screen_size": {
                        "height": 2300,
                        "resolution": 2.625,
                        "width": 1080
                    }
                },
                "do_not_track": False,
                "idfa": "0c26b7c3-4801-4815-a155-50e0e6c27eeb",
                "ip_address": "",
                "locale": "ru",
                "timezone": {
                    "location": "Asia\/Seoul",
                    "offset": "GMT+02:00"
                },
                "volume_enabled": True
            },
            "session_id": "7fe1956a-6184-4b59-8682-04ff31e24bc0",
            "date_created": 1633283996
        }

def VCHeaders(data = None) -> dict:
    headers = {
        "Accept-Language": "en-US",
        "Content-Type": "application/json",
        "User-Agent": "Amino/45725 CFNetwork/1126 Darwin/19.5.0",  # Closest server (this one for me)
        "Host": "rt.applovin.com",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "Keep-Alive",
        "Accept": "*/*"
    }
    if data: headers["Content-Length"] = str(len(data))
    return headers
