from __future__ import annotations
# ^ this thing should fix problem for python3.9 and lower(?)

from time import sleep
from json import dumps
from typing import BinaryIO
from threading import Thread
from httpx import Timeout as TimeoutConfig

from .socket import Callbacks, SocketHandler
from ..lib import exceptions, headers, objects, helpers
from ..lib.facades import AiohttpClient, AiohttpResponse, AsyncHttpxClient
from ..lib.helpers import gen_deviceId, inttime, clientrefid, str_uuid4, bytes_to_b64, LOCAL_TIMEZONE

class Client(Callbacks, SocketHandler):
    def __init__(
        self,
        deviceId: str = None, userAgent: str = None, proxies: dict = None,
        socket_trace = False, socketDebugging = False, socket_enabled = True,
        autoDevice = False, http2_enabled: bool = True,
        
        disable_timeout: bool = False,
        default_timeout: int | None = 30, own_timeout: TimeoutConfig | None = None,

        connect_timeout: int | None = None, pool_timeout: int | None = None,
        read_timeout: int | None = None, write_timeout: int | None= None,

        api_library: objects.APILibraries = objects.APILibraries.HTTPX
    ):
        self.api = "https://service.aminoapps.com/api/v1"
        self.proxies = proxies
        self.configured = False
        self.authenticated = False
        self.autoDevice = autoDevice
        self.api_library = api_library
        self.socket_enabled = socket_enabled
        self.device_id = deviceId if deviceId else gen_deviceId()
        self.user_agent = userAgent if userAgent else helpers.gen_userAgent()

        if disable_timeout:
            self.timeout_settings = TimeoutConfig(None)
        elif isinstance(own_timeout, TimeoutConfig):
            self.timeout_settings = own_timeout
        elif read_timeout or write_timeout or pool_timeout or connect_timeout:
            self.timeout_settings = TimeoutConfig(
                read=read_timeout,
                write=write_timeout,
                pool=pool_timeout,
                connect=connect_timeout
            )
        else:
            self.timeout_settings = TimeoutConfig(default_timeout or 60)
        
        if self.api_library == objects.APILibraries.REQUESTS:
            raise Exception("You cant use requests in async client. Requests is sync library.")
        elif self.api_library == objects.APILibraries.AIOHTTP:
            self.session = AiohttpClient(
                headers=headers.BASIC_HEADERS,
                http2=http2_enabled,
                base_url=self.api,
                proxies=proxies,
                timeout=self.timeout_settings
            )
        else:
            self.session = AsyncHttpxClient(
                headers=headers.BASIC_HEADERS,
                http2=http2_enabled,
                base_url=self.api,
                proxies=proxies,
                timeout=self.timeout_settings
            )
            
        if self.socket_enabled:
            SocketHandler.__init__(self, self, socket_trace=socket_trace, debug=socketDebugging)
            Callbacks.__init__(self, self)
        self.sid = None
        self.json = None
        self.secret = None
        self.userId = None
        self.account: objects.UserProfile = objects.UserProfile(None)
        self.profile: objects.UserProfile = objects.UserProfile(None)

        self.stop_loop = False
        self.active_live_chats = []

    def additional_headers(self, data: str = None, content_type: str = None):
        return headers.additionals(
            data=data,
            content_type=content_type,
            user_agent=self.user_agent,
            sid=self.sid,
            auid=self.userId,
            deviceId=gen_deviceId() if self.autoDevice else self.device_id
        )

    async def activity_status(self, status: str):
        if "on" in status.lower(): status = 1
        elif "off" in status.lower(): status = 2
        else: raise exceptions.WrongType(status)

        data = dumps({
            "onlineStatus": status,
            "duration": 86400,
            "timestamp": inttime()
        })
        
        response = await self.session.post(f"/g/s/user-profile/{self.profile.userId}/online-status", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    async def join_voice_chat(self, comId: str, chatId: str, joinType: int = 1):
        """
        Joins a Voice Chat
        **Parameters**
            - **comId** : ID of the Community
            - **chatId** : ID of the Chat
        """

        # Made by Light, Ley and Phoenix

        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "joinRole": joinType,
                "id": "2154531"  # Need to change?
            },
            "t": 112
        }
        data = dumps(data)
        self.send(data)

    async def join_video_chat(self, comId: str, chatId: str, joinType: int = 1):
        """
        Joins a Video Chat
        **Parameters**
            - **comId** : ID of the Community
            - **chatId** : ID of the Chat
        """

        # Made by Light, Ley and Phoenix

        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "joinRole": joinType,
                "channelType": 5,
                "id": "2154531"  # Need to change?
            },
            "t": 108
        }
        data = dumps(data)
        self.send(data)

    async def join_video_chat_as_viewer(self, comId: str, chatId: str):
        data = {
            "o":
                {
                    "ndcId": int(comId),
                    "threadId": chatId,
                    "joinRole": 2,
                    "id": "72446"
                },
            "t": 112
        }
        data = dumps(data)
        self.send(data)
    
    # Fixed by vedansh#4039
    async def leave_from_live_chat(self, chatId: str):
        if chatId in self.active_live_chats:
            self.active_live_chats.remove(chatId)

    async def run_vc(self, comId: str, chatId: str, joinType: str):
        while chatId in self.active_live_chats and not self.stop_loop:
            data = {
                "o": {
                    "ndcId": int(comId),
                    "threadId": chatId,
                    "joinRole": joinType,
                    "id": "2154531"  # Need to change?
                },
                "t": 112
            }
            data = dumps(data)
            self.send(data)
            sleep(60)
            if self.stop_loop:
                break

    async def start_vc(self, comId: str, chatId: str, joinType: int = 1):
        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "joinRole": joinType,
                "id": "2154531"  # Need to change?
            },
            "t": 112
        }
        data = dumps(data)
        self.send(data)
        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "channelType": 1,
                "id": "2154531"  # Need to change?
            },
            "t": 108
        }
        data = dumps(data)
        self.send(data)
        self.active_live_chats.append(chatId)
        Thread(target=lambda: self.run_vc(comId, chatId, joinType)).start()

    async def end_vc(self, comId: str, chatId: str, joinType: int = 2):
        self.leave_from_live_chat(chatId)
        data = {
            "o": {
                "ndcId": int(comId),
                "threadId": chatId,
                "joinRole": joinType,
                "id": "2154531"  # Need to change?
            },
            "t": 112
        }
        data = dumps(data)
        self.send(data)
        self.active_live_chats.remove(chatId)
        self.stop_loop = True

    async def login_sid(self, SID: str):
        """
        Login into an account with an SID

        **Parameters**
            - **SID** : SID of the account
        """
        uId = helpers.sid_to_uid(SID)
        self.authenticated = True
        self.sid = SID
        self.userId = uId

        self.account: objects.UserProfile = await self.get_user_info(uId)
        self.profile: objects.UserProfile = await self.get_user_info(uId)

        if self.socket_enabled:
            self.run_amino_socket()

    async def login(self, email: str, password: str, client_type: int = 100):
        """
        Login into an account.

        **Parameters**
            - **email** : Email of the account.
            - **password** : Password of the account.
            - **client_type**: Type of Client.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """

        data = dumps({
            "email": email,
            "v": 2,
            "secret": f"0 {password}",
            "deviceID": self.device_id,
            "clientType": client_type,
            "action": "normal",
            "timestamp": inttime()
        })

        response = await self.session.post(f"/g/s/auth/login", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: exceptions.CheckException(response)
        else:
            self.authenticated = True
            self.json = response.json()
            self.sid = self.json["sid"]
            self.userId = self.json["account"]["uid"]
            self.account: objects.UserProfile = objects.UserProfile(self.json["account"]).UserProfile
            self.profile: objects.UserProfile = objects.UserProfile(self.json["userProfile"]).UserProfile
            self.secret = self.json.get("secret")

            if self.socket_enabled:
                self.run_amino_socket()

            return response.json()

    async def login_phone(self, phoneNumber: str, password: str, client_type: int = 100):
        """
        Login into an account.

        **Parameters**
            - **phoneNumber** : Phone number of the account.
            - **password** : Password of the account.
            - **client_type**: Type of Client.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({
            "phoneNumber": phoneNumber,
            "v": 2,
            "secret": f"0 {password}",
            "deviceID": self.device_id,
            "clientType": client_type,
            "action": "normal",
            "timestamp": inttime()
        })

        response = await self.session.post(f"/g/s/auth/login", headers=self.additional_headers(data=data), data=data)
        self.run_amino_socket()
        if response.status_code != 200: exceptions.CheckException(response)

        else:
            self.authenticated = True
            self.json = response.json()
            self.sid = self.json["sid"]
            self.userId = self.json["account"]["uid"]

            self.account: objects.UserProfile = objects.UserProfile(self.json["account"]).UserProfile
            self.profile: objects.UserProfile = objects.UserProfile(self.json["userProfile"]).UserProfile
            self.secret = self.json["secret"]

            if self.socket_enabled:
                self.run_amino_socket()

            return response.json()

    async def login_secret(self, secret: str):
        """
        Login into an account.

        **Parameters**
            - **secret** : Secret of the account.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({
            "v": 2,
            "secret": secret,
            "deviceID": self.device_id,
            "clientType": 100,
            "action": "normal",
            "timestamp": inttime()
        })

        response = await self.session.post(f"/g/s/auth/login", headers=self.additional_headers(data=data), data=data)
        self.run_amino_socket()
        if response.status_code != 200: exceptions.CheckException(response)

        else:
            self.authenticated = True
            self.json = response.json()
            self.sid = self.json["sid"]
            self.userId = self.json["account"]["uid"]

            self.account: objects.UserProfile = objects.UserProfile(self.json["account"]).UserProfile
            self.profile: objects.UserProfile = objects.UserProfile(self.json["userProfile"]).UserProfile

            if self.socket_enabled:
                self.run_amino_socket()

            return response.json()

    async def register(self, nickname: str, email: str, password: str, verificationCode: str, deviceId: str = None, timeout: int = None):
        """
        Register an account.

        **Parameters**
            - **nickname** : Nickname of the account.
            - **email** : Email of the account.
            - **password** : Password of the account.
            - **verificationCode** : Verification code.
            - **deviceId** : The device id being registered to.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """

        if deviceId == None: deviceId = self.device_id

        data = dumps({
            "secret": f"0 {password}",
            "deviceID": deviceId,
            "email": email,
            "clientType": 100,
            "nickname": nickname,
            "latitude": 0,
            "longitude": 0,
            "address": None,
            "clientCallbackURL": "narviiapp://relogin",
            "validationContext": {
                "data": {
                    "code": verificationCode
                },
                "type": 1,
                "identity": email
            },
            "type": 1,
            "identity": email,
            "timestamp": inttime()
        })        

        response = await self.session.post(f"/g/s/auth/register", data=data, headers=self.additional_headers(data=data), timeout=timeout)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.json()

    async def restore(self, email: str, password: str):
        """
        Restore a deleted account.

        **Parameters**
            - **email** : Email of the account.
            - **password** : Password of the account.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({
            "secret": f"0 {password}",
            "deviceID": self.device_id,
            "email": email,
            "timestamp": inttime()
        })

        response = await self.session.post(f"/g/s/account/delete-request/cancel", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def logout(self):
        """
        Logout from an account.

        **Parameters**
            - No parameters required.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({
            "deviceID": self.device_id,
            "clientType": 100,
            "timestamp": inttime()
        })

        response = await self.session.post(f"/g/s/auth/logout", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:

            self.authenticated = False
            self.json = None
            self.sid = None
            self.userId = None
            self.account: None
            self.profile: None

            if self.socket_enabled:
                self.close()

            return response.status_code

    async def configure(self, age: int, gender: str):
        """
        Configure the settings of an account.

        **Parameters**
            - **age** : Age of the account. Minimum is 13.
            - **gender** : Gender of the account.
                - ``Male``, ``Female`` or ``Non-Binary``

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if gender.lower() == "male": gender = 1
        elif gender.lower() == "female": gender = 2
        elif gender.lower() == "non-binary": gender = 255
        else: raise exceptions.SpecifyType()

        if age <= 12: raise exceptions.AgeTooLow()

        data = dumps({
            "age": age,
            "gender": gender,
            "timestamp": inttime()
        })

        response = await self.session.post(f"/g/s/persona/profile/basic", data=data, headers=self.additional_headers(data=data))
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def verify(self, email: str, code: str):
        """
        Verify an account.

        **Parameters**
            - **email** : Email of the account.
            - **code** : Verification code.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({
            "validationContext": {
                "type": 1,
                "identity": email,
                "data": {"code": code}},
            "deviceID": self.device_id,
            "timestamp": inttime()
        })

        response = await self.session.post(f"/g/s/auth/check-security-validation", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def request_verify_code(self, email: str, resetPassword: bool = False, timeout: int = None):
        """
        Request an verification code to the targeted email.

        **Parameters**
            - **email** : Email of the account.
            - **resetPassword** : If the code should be for Password Reset.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = {
            "identity": email,
            "type": 1,
            "deviceID": self.device_id
        }

        if resetPassword is True:
            data["level"] = 2
            data["purpose"] = "reset-password"

        data = dumps(data)
        response = await self.session.post(f"/g/s/auth/request-security-validation", headers=self.additional_headers(data=data), data=data, timeout=timeout)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def activate_account(self, email: str, code: str):
        """
        Activate an account.

        **Parameters**
            - **email** : Email of the account.
            - **code** : Verification code.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """

        data = dumps({
            "type": 1,
            "identity": email,
            "data": {"code": code},
            "deviceID": self.device_id
        })

        response = await self.session.post(f"/g/s/auth/activate-email", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    # Provided by "𝑰 𝑵 𝑻 𝑬 𝑹 𝑳 𝑼 𝑫 𝑬#4082"
    async def delete_account(self, password: str):
        """
        Delete an account.

        **Parameters**
            - **password** : Password of the account.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """

        data = dumps({
            "deviceID": self.device_id,
            "secret": f"0 {password}"
        })

        response = await self.session.post(f"/g/s/account/delete-request", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def change_password(
            self, email: str, code: str | int,
            old_password: str, new_password: str,
        ):
        """
        Change password of an account.

        **Parameters**
            - **email** : Email of the account.
            - **code** : Verification code.
            - **old_password** : old password of account.
            - **new_password** : new password for account.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """

        data = dumps({
            "secret": f"0 {old_password}",
            "deviceTokenType": 0,
            "clientType": 100,
            "systemPushEnabled": 1,
            "clientCallbackURL": "narviiapp://default",
            "timestamp": inttime(),
            "locale": "en_US",
            "bundleID": "com.narvii.master",
            "validationContext": {
                "identity": email,
                "data": {
                    "code": str(code)
                },
                "deviceID": self.device_id,
                "type": 1,
                "level": 1
            },
            "deviceID": self.device_id,
            "timezone": LOCAL_TIMEZONE,
            "updateSecret": f"0 {new_password}"
        })

        response = await self.session.post(f"/g/s/auth/change-password", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code
        
    async def change_email(
            self, password: str,
            old_email: str, old_code: str | int,
            new_email: str, new_code: str | int
        ):
        """
        Change email of an account.

        **Parameters**
            - **password** : Password from account.
            - **old_email** : Old email of the account.
            - **old_code** : Verification code from old email.
            - **new_email** : New email for account.
            - **new_code** : Verification code from new email.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """

        data = dumps({
            "secret": f"0 {password}",
            "deviceTokenType": 0,
            "clientType": 100,
            "systemPushEnabled": 1,
            "timestamp": inttime(),
            "newValidationContext": {
                "identity": new_email,
                "data": {
                    "code": str(new_code)
                },
                "deviceID": self.device_id,
                "type": 1,
                "level": 1
            },
            "locale": "en_BY",
            "level": 1,
            "oldValidationContext": {
                "identity": old_email,
                "data": {
                    "code": str(old_code)
                },
                "deviceID": self.device_id,
                "type": 1,
                "level": 1
            },
            "bundleID": "com.narvii.master",
            "timezone": LOCAL_TIMEZONE,
            "deviceID": self.device_id,
            "clientCallbackURL": "narviiapp://default"
        })

        response = await self.session.post(f"/g/s/auth/update-email", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def check_device(self, deviceId: str, locale: str = "en_US"):
        """
        Check if the Device ID is valid.

        **Parameters**
            - **deviceId** : ID of the Device.
            - **locale** : Locale like "ru_RU", "en_US"

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({
            "deviceID": deviceId,
            "bundleID": "com.narvii.amino.master",
            "clientType": 100,
            "timezone": LOCAL_TIMEZONE,
            "systemPushEnabled": True,
            "locale": locale,
            "timestamp": inttime()
        })

        response = await self.session.post(f"/g/s/device", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            self.configured = True; return response.status_code

    async def get_account_info(self):
        response = await self.session.get(f"/g/s/account", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.UserProfile(response.json()["account"]).UserProfile

    async def upload_media(self, file: BinaryIO, fileType: str):
        """
        Upload file to the amino servers.

        **Parameters**
            - **file** : File to be uploaded.

        **Returns**
            - **Success** : Url of the file uploaded to the server.

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if fileType == "audio":
            t = "audio/aac"
        elif fileType == "image":
            t = "image/jpg"
        elif fileType == "gif":
            t = "image/gif"
        else: raise exceptions.SpecifyType(fileType)

        data = file.read()

        response = await self.session.post(f"/g/s/media/upload", data=data, headers=self.additional_headers(content_type=t, data=data))
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.json()["mediaValue"]

    def handle_socket_message(self, data):
        return self.resolve(data)

    async def get_eventlog(self):
        response = await self.session.get(f"/g/s/eventlog/profile?language=en", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.json()

    async def sub_clients(self, start: int = 0, size: int = 25):
        """
        List of Communities the account is in.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Community List <aminofixfix.lib.objects.CommunityList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if not self.authenticated: raise exceptions.NotLoggedIn()
        response = await self.session.get(f"/g/s/community/joined?v=1&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.CommunityList(response.json()["communityList"]).CommunityList

    async def sub_clients_profile(self, start: int = 0, size: int = 25):
        if not self.authenticated: raise exceptions.NotLoggedIn()
        response = await self.session.get(f"/g/s/community/joined?v=1&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.json()["userInfoInCommunities"]

    async def get_user_info(self, userId: str):
        """
        Information of an User.

        **Parameters**
            - **userId** : ID of the User.

        **Returns**
            - **Success** : :meth:`User Object <aminofixfix.lib.objects.UserProfile>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/user-profile/{userId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.UserProfile(response.json()["userProfile"]).UserProfile

    async def watch_ad(self, userId: str = None):
        data = headers.Tapjoy.Data(userId or self.userId)
        response = await self.session.post("https://ads.tapdaq.com/v4/analytics/reward", data=data, headers=headers.Tapjoy.Headers())
        if response.status_code != 204: return exceptions.CheckException(response)
        else: return response.status_code

    async def get_chat_threads(self, start: int = 0, size: int = 25):
        """
        List of Chats the account is in.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Chat List <aminofixfix.lib.objects.ThreadList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/chat/thread?type=joined-me&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.ThreadList(response.json()["threadList"]).ThreadList

    async def get_chat_thread(self, chatId: str):
        """
        Get the Chat Object from an Chat ID.

        **Parameters**
            - **chatId** : ID of the Chat.

        **Returns**
            - **Success** : :meth:`Chat Object <aminofixfix.lib.objects.Thread>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/chat/thread/{chatId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.Thread(response.json()["thread"]).Thread

    async def get_chat_users(self, chatId: str, start: int = 0, size: int = 25):
        response = await self.session.get(f"/g/s/chat/thread/{chatId}/member?start={start}&size={size}&type=default&cv=1.2", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.UserProfileList(response.json()["memberList"]).UserProfileList

    async def join_chat(self, chatId: str):
        """
        Join an Chat.

        **Parameters**
            - **chatId** : ID of the Chat.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.post(f"/g/s/chat/thread/{chatId}/member/{self.userId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def leave_chat(self, chatId: str):
        """
        Leave an Chat.

        **Parameters**
            - **chatId** : ID of the Chat.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.delete(f"/g/s/chat/thread/{chatId}/member/{self.userId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def start_chat(self, userId: str | list, message: str, title: str = None, content: str = None, isGlobal: bool = False, publishToGlobal: bool = False):
        """
        Start an Chat with an User or List of Users.

        **Parameters**
            - **userId** : ID of the User or List of User IDs.
            - **message** : Starting Message.
            - **title** : Title of Group Chat.
            - **content** : Content of Group Chat.
            - **isGlobal** : If Group Chat is Global.
            - **publishToGlobal** : If Group Chat should show in Global.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if isinstance(userId, str): userIds = [userId]
        elif isinstance(userId, list): userIds = userId
        else: raise exceptions.WrongType()

        data = {
            "title": title,
            "inviteeUids": userIds,
            "initialMessageContent": message,
            "content": content,
            "timestamp": inttime()
        }

        if isGlobal is True: data["type"] = 2; data["eventSource"] = "GlobalComposeMenu"
        else: data["type"] = 0

        if publishToGlobal is True: data["publishToGlobal"] = 1
        else: data["publishToGlobal"] = 0

        data = dumps(data)


        response = await self.session.post(f"/g/s/chat/thread", data=data, headers=self.additional_headers(data=data))
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.Thread(response.json()["thread"]).Thread

    async def invite_to_chat(self, userId: str | list, chatId: str):
        """
        Invite a User or List of Users to a Chat.

        **Parameters**
            - **userId** : ID of the User or List of User IDs.
            - **chatId** : ID of the Chat.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if isinstance(userId, str): userIds = [userId]
        elif isinstance(userId, list): userIds = userId
        else: raise exceptions.WrongType

        data = dumps({
            "uids": userIds,
            "timestamp": inttime()
        })

        response = await self.session.post(f"/g/s/chat/thread/{chatId}/member/invite", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def kick(self, userId: str, chatId: str, allowRejoin: bool = True):
        if allowRejoin: allowRejoin = 1
        if not allowRejoin: allowRejoin = 0
        response = await self.session.delete(f"/g/s/chat/thread/{chatId}/member/{userId}?allowRejoin={allowRejoin}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def get_chat_messages(self, chatId: str, size: int = 25, pageToken: str = None):
        """
        List of Messages from an Chat.

        **Parameters**
            - **chatId** : ID of the Chat.
            - *size* : Size of the list.
            - *size* : Size of the list.
            - *pageToken* : Next Page Token.

        **Returns**
            - **Success** : :meth:`Message List <aminofixfix.lib.objects.MessageList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if pageToken is not None: url = f"/g/s/chat/thread/{chatId}/message?v=2&pagingType=t&pageToken={pageToken}&size={size}"
        else: url = f"/g/s/chat/thread/{chatId}/message?v=2&pagingType=t&size={size}"

        response = await self.session.get(url, headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.GetMessages(response.json()).GetMessages

    async def get_message_info(self, chatId: str, messageId: str):
        """
        Information of an Message from an Chat.

        **Parameters**
            - **chatId** : ID of the Chat.
            - **messageId** : ID of the Message.

        **Returns**
            - **Success** : :meth:`Message Object <aminofixfix.lib.objects.Message>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/chat/thread/{chatId}/message/{messageId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.Message(response.json()["message"]).Message

    async def get_community_info(self, comId: str):
        """
        Information of an Community.

        **Parameters**
            - **comId** : ID of the Community.

        **Returns**
            - **Success** : :meth:`Community Object <aminofixfix.lib.objects.Community>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s-x{comId}/community/info?withInfluencerList=1&withTopicList=true&influencerListOrderStrategy=fansCount", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.Community(response.json()["community"]).Community

    async def search_community(self, aminoId: str):
        """
        Search a Community byt its Amino ID.

        **Parameters**
            - **aminoId** : Amino ID of the Community.

        **Returns**
            - **Success** : :meth:`Community List <aminofixfix.lib.objects.CommunityList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/search/amino-id-and-link?q={aminoId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:

            response = response.json()["resultList"]
            if len(response) == 0: raise exceptions.CommunityNotFound(aminoId)
            else: return objects.CommunityList([com["refObject"] for com in response]).CommunityList

    async def get_user_following(self, userId: str, start: int = 0, size: int = 25):
        """
        List of Users that the User is Following.

        **Parameters**
            - **userId** : ID of the User.
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`User List <aminofixfix.lib.objects.UserProfileList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/user-profile/{userId}/joined?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.UserProfileList(response.json()["userProfileList"]).UserProfileList

    async def get_user_followers(self, userId: str, start: int = 0, size: int = 25):
        """
        List of Users that are Following the User.

        **Parameters**
            - **userId** : ID of the User.
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`User List <aminofixfix.lib.objects.UserProfileList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/user-profile/{userId}/member?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.UserProfileList(response.json()["userProfileList"]).UserProfileList

    async def get_user_visitors(self, userId: str, start: int = 0, size: int = 25):
        """
        List of Users that Visited the User.

        **Parameters**
            - **userId** : ID of the User.
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Visitors List <aminofixfix.lib.objects.VisitorsList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/user-profile/{userId}/visitors?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.VisitorsList(response.json()).VisitorsList

    async def get_blocked_users(self, start: int = 0, size: int = 25):
        """
        List of Users that the User Blocked.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Users List <aminofixfix.lib.objects.UserProfileList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/block?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.UserProfileList(response.json()["userProfileList"]).UserProfileList

    async def get_blog_info(self, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None):
        if blogId or quizId:
            if quizId is not None: blogId = quizId
            response = await self.session.get(f"/g/s/blog/{blogId}", headers=self.additional_headers())
            if response.status_code != 200: 
                return exceptions.CheckException(response)
            else:
                return objects.GetBlogInfo(response.json()).GetBlogInfo

        elif wikiId:
            response = await self.session.get(f"/g/s/item/{wikiId}", headers=self.additional_headers())
            if response.status_code != 200: 
                return exceptions.CheckException(response)
            else:
                return objects.GetBlogInfo(response.json()).GetWikiInfo

        elif fileId:
            response = await self.session.get(f"/g/s/shared-folder/files/{fileId}", headers=self.additional_headers())
            if response.status_code != 200: 
                return exceptions.CheckException(response)
            else:
                return objects.SharedFolderFile(response.json()["file"]).SharedFolderFile

        else: raise exceptions.SpecifyType()

    async def get_blog_comments(self, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None, sorting: str = "newest", start: int = 0, size: int = 25):
        if sorting == "newest": sorting = "newest"
        elif sorting == "oldest": sorting = "oldest"
        elif sorting == "top": sorting = "vote"
        else: raise exceptions.WrongType(sorting)

        if blogId or quizId:
            if quizId is not None: blogId = quizId
            response = await self.session.get(f"/g/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}", headers=self.additional_headers())
        elif wikiId: response = await self.session.get(f"/g/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}", headers=self.additional_headers())
        elif fileId: response = await self.session.get(f"/g/s/shared-folder/files/{fileId}/comment?sort={sorting}&start={start}&size={size}", headers=self.additional_headers())
        else: raise exceptions.SpecifyType()

        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.CommentList(response.json()["commentList"]).CommentList

    async def get_blocker_users(self, start: int = 0, size: int = 25):
        """
        List of Users that are Blocking the User.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`List of User IDs <None>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/block/full-list?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.json()["blockerUidList"]

    async def get_wall_comments(self, userId: str, sorting: str, start: int = 0, size: int = 25):
        """
        List of Wall Comments of an User.

        **Parameters**
            - **userId** : ID of the User.
            - **sorting** : Order of the Comments.
                - ``newest``, ``oldest``, ``top``
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Comments List <aminofixfix.lib.objects.CommentList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if sorting.lower() == "newest": sorting = "newest"
        elif sorting.lower() == "oldest": sorting = "oldest"
        elif sorting.lower() == "top": sorting = "vote"
        else: raise exceptions.WrongType(sorting)

        response = await self.session.get(f"/g/s/user-profile/{userId}/g-comment?sort={sorting}&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.CommentList(response.json()["commentList"]).CommentList

    async def flag(self, reason: str, flagType: int, userId: str = None, blogId: str = None, wikiId: str = None, asGuest: bool = False):
        """
        Flag a User, Blog or Wiki.

        **Parameters**
            - **reason** : Reason of the Flag.
            - **flagType** : Type of the Flag.
            - **userId** : ID of the User.
            - **blogId** : ID of the Blog.
            - **wikiId** : ID of the Wiki.
            - *asGuest* : Execute as a Guest.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if reason is None: raise exceptions.ReasonNeeded
        if flagType is None: raise exceptions.FlagTypeNeeded

        data = {
            "flagType": flagType,
            "message": reason,
            "timestamp": inttime()
        }

        if userId:
            data["objectId"] = userId
            data["objectType"] = 0

        elif blogId:
            data["objectId"] = blogId
            data["objectType"] = 1

        elif wikiId:
            data["objectId"] = wikiId
            data["objectType"] = 2

        else: raise exceptions.SpecifyType

        if asGuest: flg = "g-flag"
        else: flg = "flag"

        data = dumps(data)
        response = await self.session.post(f"/g/s/{flg}", data=data, headers=self.additional_headers(data=data))
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def send_message(
            self,
            chatId: str, message: str = None, messageType: int = 0,
            file: BinaryIO = None, fileType: str = None,
            replyTo: str = None, mentionUserIds: list = None,
            stickerId: str = None,
        
            embedId: str = None, embedObjectType: int = None, embedLink: str = None, embedTitle: str = None, embedContent: str = None, embedImage: BinaryIO = None,
            embedType: objects.EmbedTypes = objects.EmbedTypes.LINK_SNIPPET
        ):
        """
        Send a Message to a Chat.

        **Parameters**
            - **message** : Message to be sent
            - **chatId** : ID of the Chat.
            - **file** : File to be sent.
            - **fileType** : Type of the file.
                - ``audio``, ``image``, ``gif``
            - **messageType** : Type of the Message.
            - **mentionUserIds** : List of User IDS to mention. '@' needed in the Message.
            - **replyTo** : Message ID to reply to.
            - **stickerId** : Sticker ID to be sent.
            - **embedType** : Type of the Embed. Can be aminofixfix.lib.objects.EmbedTypes only. By default it's LinkSnippet one.
            - **embedLink** : Link of the Embed. Can be only "ndc://" link if its AttachedObject.
            - **embedImage** : Image of the Embed. Required to send Embed, if its LinkSnippet. Can be only 1024x1024 max. Can be string to existing image uploaded to Amino or it can be opened (not readed) file.
            - **embedId** : ID of the Embed. Works only in AttachedObject Embeds. It can be any ID, just gen it using str_uuid4().
            - **embedType** : Type of the AttachedObject Embed. Works only in AttachedObject Embeds. Just look what values AttachedObjectTypes enum contains.
            - **embedTitle** : Title of the Embed. Works only in AttachedObject Embeds. Can be empty.
            - **embedContent** : Content of the Embed. Works only in AttachedObject Embeds. Can be empty.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """

        if message is not None and file is None:
            message = message.replace("<$", "‎‏").replace("$>", "‬‭")

        mentions = []
        if mentionUserIds:
            mentions = [{"uid": mention_uid} for mention_uid in mentionUserIds]

        if embedImage and not isinstance(embedImage, str):
            try: readEmbed = embedImage.read()
            except: embedType = None

        if embedType == objects.EmbedTypes.LINK_SNIPPET:
            data = {
                "type": messageType,
                "content": message,
                "clientRefId": clientrefid(),
                "extensions": {
                    "linkSnippetList": [{
                        "link": embedLink,
                        "mediaType": 100,
                        "mediaUploadValue": bytes_to_b64(readEmbed),
                        "mediaUploadValueContentType": "image/png"
                    }],
                    "mentionedArray": mentions
                },
                "timestamp": inttime()
            }
        elif embedType == objects.EmbedTypes.ATTACHED_OBJECT:
            try: embedObjectType.value
            except: raise Exception("You SHOULD pass AttachedEmbedTypes.")

            if isinstance(embedImage, str):
                image = [[100, embedImage, None]]
            elif embedImage:
                image = [[100, await self.upload_media(embedImage, "image"), None]]
            else:
                image = None

            data = {
                "type": messageType,
                "content": message,
                "clientRefId": clientrefid(),
                "attachedObject": {
                    "objectId": embedId,
                    "objectType": embedObjectType.value,
                    "link": embedLink,
                    "title": embedTitle,
                    "content": embedContent,
                    "mediaList": image
                },
                "extensions": {"mentionedArray": mentions},
                "timestamp": inttime()
            }
        else:
            data = {
                "type": messageType,
                "content": message,
                "clientRefId": clientrefid(),
                "extensions": {"mentionedArray": mentions},
                "timestamp": inttime()
            }

        if replyTo: data["replyMessageId"] = replyTo

        if stickerId:
            data["content"] = None
            data["stickerId"] = stickerId
            data["type"] = 3

        if file:
            data["content"] = None
            if fileType == "audio":
                data["type"] = 2
                data["mediaType"] = 110

            elif fileType == "image":
                data["mediaType"] = 100
                data["mediaUploadValueContentType"] = "image/jpg"
                data["mediaUhqEnabled"] = True

            elif fileType == "gif":
                data["mediaType"] = 100
                data["mediaUploadValueContentType"] = "image/gif"
                data["mediaUhqEnabled"] = True

            else: raise exceptions.SpecifyType(fileType)

            data["mediaUploadValue"] = bytes_to_b64(file.read())

        data = dumps(data)

        response = await self.session.post(f"/g/s/chat/thread/{chatId}/message", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    async def delete_message(self, chatId: str, messageId: str, asStaff: bool = False, reason: str = None):
        """
        Delete a Message from a Chat.

        **Parameters**
            - **messageId** : ID of the Message.
            - **chatId** : ID of the Chat.
            - **asStaff** : If execute as a Staff member (Leader or Curator).
            - **reason** : Reason of the action to show on the Moderation History.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = {
            "adminOpName": 102,
            "adminOpNote": {"content": reason},
            "timestamp": inttime()
        }

        data = dumps(data)
        
        if not asStaff: response = await self.session.delete(f"/g/s/chat/thread/{chatId}/message/{messageId}", headers=self.additional_headers())
        else: response = await self.session.post(f"/g/s/chat/thread/{chatId}/message/{messageId}/admin", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def mark_as_read(self, chatId: str, messageId: str):
        """
        Mark a Message from a Chat as Read.

        **Parameters**
            - **messageId** : ID of the Message.
            - **chatId** : ID of the Chat.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({
            "messageId": messageId,
            "timestamp": inttime()
        })
        
        response = await self.session.post(f"/g/s/chat/thread/{chatId}/mark-as-read", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def edit_chat(self, chatId: str, doNotDisturb: bool = None, pinChat: bool = None, title: str = None, icon: str = None, backgroundImage: str = None, content: str = None, announcement: str = None, coHosts: list = None, keywords: list = None, pinAnnouncement: bool = None, publishToGlobal: bool = None, canTip: bool = None, viewOnly: bool = None, canInvite: bool = None, fansOnly: bool = None):
        """
        Send a Message to a Chat.

        **Parameters**
            - **chatId** : ID of the Chat.
            - **title** : Title of the Chat.
            - **content** : Content of the Chat.
            - **icon** : Icon of the Chat.
            - **backgroundImage** : Url of the Background Image of the Chat.
            - **announcement** : Announcement of the Chat.
            - **pinAnnouncement** : If the Chat Announcement should Pinned or not.
            - **coHosts** : List of User IDS to be Co-Host.
            - **keywords** : List of Keywords of the Chat.
            - **viewOnly** : If the Chat should be on View Only or not.
            - **canTip** : If the Chat should be Tippable or not.
            - **canInvite** : If the Chat should be Invitable or not.
            - **fansOnly** : If the Chat should be Fans Only or not.
            - **publishToGlobal** : If the Chat should show on Public Chats or not.
            - **doNotDisturb** : If the Chat should Do Not Disturb or not.
            - **pinChat** : If the Chat should Pinned or not.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = {"timestamp": inttime()}

        if title: data["title"] = title
        if content: data["content"] = content
        if icon: data["icon"] = icon
        if keywords: data["keywords"] = keywords
        if announcement: data["extensions"] = {"announcement": announcement}
        if pinAnnouncement: data["extensions"] = {"pinAnnouncement": pinAnnouncement}
        if fansOnly: data["extensions"] = {"fansOnly": fansOnly}

        if publishToGlobal: data["publishToGlobal"] = 0
        if not publishToGlobal: data["publishToGlobal"] = 1

        res = []

        if doNotDisturb is not None:
            if doNotDisturb:
                data = dumps({"alertOption": 2, "timestamp": inttime()})
                
                response = await self.session.post(f"/g/s/chat/thread/{chatId}/member/{self.userId}/alert", data=data, headers=self.additional_headers(data=data))
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

            if not doNotDisturb:
                data = dumps({"alertOption": 1, "timestamp": inttime()})
                
                response = await self.session.post(f"/g/s/chat/thread/{chatId}/member/{self.userId}/alert", data=data, headers=self.additional_headers(data=data))
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

        if pinChat is not None:
            if pinChat:
                response = await self.session.post(f"/g/s/chat/thread/{chatId}/pin", data=data, headers=self.additional_headers())
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

            if not pinChat:
                response = await self.session.post(f"/g/s/chat/thread/{chatId}/unpin", data=data, headers=self.additional_headers())
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

        if backgroundImage is not None:
            data = dumps({"media": [100, backgroundImage, None], "timestamp": inttime()})
            
            response = await self.session.post(f"/g/s/chat/thread/{chatId}/member/{self.userId}/background", data=data, headers=self.additional_headers(data=data))
            if response.status_code != 200: res.append(exceptions.CheckException(response))
            else: res.append(response.status_code)

        if coHosts is not None:
            data = dumps({"uidList": coHosts, "timestamp": inttime()})
            
            response = await self.session.post(f"/g/s/chat/thread/{chatId}/co-host", data=data, headers=self.additional_headers(data=data))
            if response.status_code != 200: res.append(exceptions.CheckException(response))
            else: res.append(response.status_code)

        if viewOnly is not None:
            if viewOnly:
                
                response = await self.session.post(f"/g/s/chat/thread/{chatId}/view-only/enable", headers=self.additional_headers())
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

            if not viewOnly:
                
                response = await self.session.post(f"/g/s/chat/thread/{chatId}/view-only/disable", headers=self.additional_headers())
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

        if canInvite is not None:
            if canInvite:
                
                response = await self.session.post(f"/g/s/chat/thread/{chatId}/members-can-invite/enable", data=data, headers=self.additional_headers(data=data))
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

            if not canInvite:
                
                response = await self.session.post(f"/g/s/chat/thread/{chatId}/members-can-invite/disable", data=data, headers=self.additional_headers(data=data))
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

        if canTip is not None:
            if canTip:
                
                response = await self.session.post(f"/g/s/chat/thread/{chatId}/tipping-perm-status/enable", data=data, headers=self.additional_headers(data=data))
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

            if not canTip:
                
                response = await self.session.post(f"/g/s/chat/thread/{chatId}/tipping-perm-status/disable", data=data, headers=self.additional_headers(data=data))
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

        data = dumps(data)
        
        response = await self.session.post(f"/g/s/chat/thread/{chatId}", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: res.append(exceptions.CheckException(response))
        else: res.append(response.status_code)

        return res

    async def visit(self, userId: str):
        """
        Visit an User.

        **Parameters**
            - **userId** : ID of the User.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/user-profile/{userId}?action=visit", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def send_coins(self, coins: int, blogId: str = None, chatId: str = None, objectId: str = None, transactionId: str = None):
        url = None
        if transactionId is None: transactionId = str_uuid4()

        data = {
            "coins": coins,
            "tippingContext": {"transactionId": transactionId},
            "timestamp": inttime()
        }

        if blogId is not None: url = f"/g/s/blog/{blogId}/tipping"
        if chatId is not None: url = f"/g/s/chat/thread/{chatId}/tipping"
        if objectId is not None:
            data["objectId"] = objectId
            data["objectType"] = 2
            url = f"/g/s/tipping"

        if url is None: raise exceptions.SpecifyType()

        data = dumps(data)
        response = await self.session.post(url, headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def follow(self, userId: str | list):
        """
        Follow an User or Multiple Users.

        **Parameters**
            - **userId** : ID of the User or List of IDs of the Users.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if isinstance(userId, str):
            # looks like not working
            # response = await self.session.post(f"/g/s/user-profile/{userId}/member", headers=self.additional_headers())
            data = dumps({"targetUidList": [userId], "timestamp": inttime()})
            
            response = await self.session.post(f"/g/s/user-profile/{self.userId}/joined", headers=self.additional_headers(data=data), data=data)

        elif isinstance(userId, list):
            data = dumps({"targetUidList": userId, "timestamp": inttime()})
            
            response = await self.session.post(f"/g/s/user-profile/{self.userId}/joined", headers=self.additional_headers(data=data), data=data)

        else: raise exceptions.WrongType

        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def unfollow(self, userId: str):
        """
        Unfollow an User.

        **Parameters**
            - **userId** : ID of the User.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.delete(f"/g/s/user-profile/{userId}/member/{self.userId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def block(self, userId: str):
        """
        Block an User.

        **Parameters**
            - **userId** : ID of the User.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.post(f"/g/s/block/{userId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def unblock(self, userId: str):
        """
        Unblock an User.

        **Parameters**
            - **userId** : ID of the User.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.delete(f"/g/s/block/{userId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def join_community(self, comId: str, invitationId: str = None):
        """
        Join a Community.

        **Parameters**
            - **comId** : ID of the Community.
            - **invitationId** : ID of the Invitation Code.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = {"timestamp": inttime()}
        if invitationId: data["invitationId"] = invitationId

        data = dumps(data)
        response = await self.session.post(f"/x{comId}/s/community/join", data=data, headers=self.additional_headers(data=data))
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def request_join_community(self, comId: str, message: str = None):
        """
        Request to join a Community.

        **Parameters**
            - **comId** : ID of the Community.
            - **message** : Message to be sent.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({"message": message, "timestamp": inttime()})
        response = await self.session.post(f"/x{comId}/s/community/membership-request", data=data, headers=self.additional_headers(data=data))
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def leave_community(self, comId: str):
        """
        Leave a Community.

        **Parameters**
            - **comId** : ID of the Community.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.post(f"/x{comId}/s/community/leave", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def flag_community(self, comId: str, reason: str, flagType: int, isGuest: bool = False):
        """
        Flag a Community.

        **Parameters**
            - **comId** : ID of the Community.
            - **reason** : Reason of the Flag.
            - **flagType** : Type of Flag.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if reason is None: raise exceptions.ReasonNeeded
        if flagType is None: raise exceptions.FlagTypeNeeded

        data = dumps({
            "objectId": comId,
            "objectType": 16,
            "flagType": flagType,
            "message": reason,
            "timestamp": inttime()
        })

        if isGuest: flg = "g-flag"
        else: flg = "flag"
        
        response = await self.session.post(f"/x{comId}/s/{flg}", data=data, headers=self.additional_headers(data=data))
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def edit_profile(self, nickname: str = None, content: str = None, icon: BinaryIO = None, backgroundColor: str = None, backgroundImage: str = None, defaultBubbleId: str = None):
        """
        Edit account's Profile.

        **Parameters**
            - **nickname** : Nickname of the Profile.
            - **content** : Biography of the Profile.
            - **icon** : Icon of the Profile.
            - **backgroundImage** : Url of the Background Picture of the Profile.
            - **backgroundColor** : Hexadecimal Background Color of the Profile.
            - **defaultBubbleId** : Chat bubble ID.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = {
            "address": None,
            "latitude": 0,
            "longitude": 0,
            "mediaList": None,
            "eventSource": "UserProfileView",
            "timestamp": inttime()
        }

        if nickname: data["nickname"] = nickname
        if icon: data["icon"] = self.upload_media(icon, "image")
        if content: data["content"] = content
        if backgroundColor: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}
        if backgroundImage: data["extensions"] = {"style": {"backgroundMediaList": [[100, backgroundImage, None, None, None]]}}
        if defaultBubbleId: data["extensions"] = {"defaultBubbleId": defaultBubbleId}

        data = dumps(data)
        response = await self.session.post(f"/g/s/user-profile/{self.userId}", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def set_privacy_status(self, isAnonymous: bool = False, getNotifications: bool = False):
        """
        Edit account's Privacy Status.

        **Parameters**
            - **isAnonymous** : If visibility should be Anonymous or not.
            - **getNotifications** : If account should get new Visitors Notifications.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """

        data = {"timestamp": inttime()}

        if not isAnonymous: data["privacyMode"] = 1
        if isAnonymous: data["privacyMode"] = 2
        if not getNotifications: data["notificationStatus"] = 2
        if getNotifications: data["privacyMode"] = 1

        data = dumps(data)
        response = await self.session.post(f"/g/s/account/visit-settings", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def set_amino_id(self, aminoId: str):
        """
        Edit account's Amino ID.

        **Parameters**
            - **aminoId** : Amino ID of the Account.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({"aminoId": aminoId, "timestamp": inttime()})
        response = await self.session.post(f"/g/s/account/change-amino-id", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def get_linked_communities(self, userId: str):
        """
        Get a List of Linked Communities of an User.

        **Parameters**
            - **userId** : ID of the User.

        **Returns**
            - **Success** : :meth:`Community List <aminofixfix.lib.objects.CommunityList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/user-profile/{userId}/linked-community", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.CommunityList(response.json()["linkedCommunityList"]).CommunityList

    async def get_unlinked_communities(self, userId: str):
        """
        Get a List of Unlinked Communities of an User.

        **Parameters**
            - **userId** : ID of the User.

        **Returns**
            - **Success** : :meth:`Community List <aminofixfix.lib.objects.CommunityList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/user-profile/{userId}/linked-community", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.CommunityList(response.json()["unlinkedCommunityList"]).CommunityList

    async def reorder_linked_communities(self, comIds: list):
        """
        Reorder List of Linked Communities.

        **Parameters**
            - **comIds** : IDS of the Communities.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({"ndcIds": comIds, "timestamp": inttime()})
        response = await self.session.post(f"/g/s/user-profile/{self.userId}/linked-community/reorder", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def add_linked_community(self, comId: str):
        """
        Add a Linked Community on your profile.

        **Parameters**
            - **comId** : ID of the Community.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.post(f"/g/s/user-profile/{self.userId}/linked-community/{comId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def remove_linked_community(self, comId: str):
        """
        Remove a Linked Community on your profile.

        **Parameters**
            - **comId** : ID of the Community.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.delete(f"/g/s/user-profile/{self.userId}/linked-community/{comId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def comment(self, message: str, userId: str = None, blogId: str = None, wikiId: str = None, replyTo: str = None):
        """
        Comment on a User's Wall, Blog or Wiki.

        **Parameters**
            - **message** : Message to be sent.
            - **userId** : ID of the User. (for Walls)
            - **blogId** : ID of the Blog. (for Blogs)
            - **wikiId** : ID of the Wiki. (for Wikis)
            - **replyTo** : ID of the Comment to Reply to.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if message is None: raise exceptions.MessageNeeded

        data = {
            "content": message,
            "stickerId": None,
            "type": 0,
            "timestamp": inttime()
        }

        if replyTo: data["respondTo"] = replyTo

        if userId:
            data["eventSource"] = "UserProfileView"
            data = dumps(data)
            
            response = await self.session.post(f"/g/s/user-profile/{userId}/g-comment", headers=self.additional_headers(data=data), data=data)

        elif blogId:
            data["eventSource"] = "PostDetailView"
            data = dumps(data)
            
            response = await self.session.post(f"/g/s/blog/{blogId}/g-comment", headers=self.additional_headers(data=data), data=data)

        elif wikiId:
            data["eventSource"] = "PostDetailView"
            data = dumps(data)
            
            response = await self.session.post(f"/g/s/item/{wikiId}/g-comment", headers=self.additional_headers(data=data), data=data)

        else: raise exceptions.SpecifyType
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def delete_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None):
        """
        Delete a Comment on a User's Wall, Blog or Wiki.

        **Parameters**
            - **commentId** : ID of the Comment.
            - **userId** : ID of the User. (for Walls)
            - **blogId** : ID of the Blog. (for Blogs)
            - **wikiId** : ID of the Wiki. (for Wikis)

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if userId: response = await self.session.delete(f"/g/s/user-profile/{userId}/g-comment/{commentId}", headers=self.additional_headers())
        elif blogId: response = await self.session.delete(f"/g/s/blog/{blogId}/g-comment/{commentId}", headers=self.additional_headers())
        elif wikiId: response = await self.session.delete(f"/g/s/item/{wikiId}/g-comment/{commentId}", headers=self.additional_headers())
        else: raise exceptions.SpecifyType

        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def like_blog(self, blogId: str | list = None, wikiId: str = None):
        """
        Like a Blog, Multiple Blogs or a Wiki.

        **Parameters**
            - **blogId** : ID of the Blog or List of IDs of the Blogs. (for Blogs)
            - **wikiId** : ID of the Wiki. (for Wikis)

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = {
            "value": 4,
            "timestamp": inttime()
        }

        if blogId:
            if isinstance(blogId, str):
                data["eventSource"] = "UserProfileView"
                data = dumps(data)
                
                response = await self.session.post(f"/g/s/blog/{blogId}/g-vote?cv=1.2", headers=self.additional_headers(data=data), data=data)

            elif isinstance(blogId, list):
                data["targetIdList"] = blogId
                data = dumps(data)
                
                response = await self.session.post(f"/g/s/feed/g-vote", headers=self.additional_headers(data=data), data=data)

            else: raise exceptions.WrongType(type(blogId))

        elif wikiId:
            data["eventSource"] = "PostDetailView"
            data = dumps(data)
            
            response = await self.session.post(f"/g/s/item/{wikiId}/g-vote?cv=1.2", headers=self.additional_headers(data=data), data=data)

        else: raise exceptions.SpecifyType()

        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def unlike_blog(self, blogId: str = None, wikiId: str = None):
        """
        Remove a like from a Blog or Wiki.

        **Parameters**
            - **blogId** : ID of the Blog. (for Blogs)
            - **wikiId** : ID of the Wiki. (for Wikis)

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if blogId: response = await self.session.delete(f"/g/s/blog/{blogId}/g-vote?eventSource=UserProfileView", headers=self.additional_headers())
        elif wikiId: response = await self.session.delete(f"/g/s/item/{wikiId}/g-vote?eventSource=PostDetailView", headers=self.additional_headers())
        else: raise exceptions.SpecifyType

        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def like_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None):
        """
        Like a Comment on a User's Wall, Blog or Wiki.

        **Parameters**
            - **commentId** : ID of the Comment.
            - **userId** : ID of the User. (for Walls)
            - **blogId** : ID of the Blog. (for Blogs)
            - **wikiId** : ID of the Wiki. (for Wikis)

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = {
            "value": 4,
            "timestamp": inttime()
        }

        if userId:
            data["eventSource"] = "UserProfileView"
            data = dumps(data)
            
            response = await self.session.post(f"/g/s/user-profile/{userId}/comment/{commentId}/g-vote?cv=1.2&value=1", headers=self.additional_headers(data=data), data=data)

        elif blogId:
            data["eventSource"] = "PostDetailView"
            data = dumps(data)
            
            response = await self.session.post(f"/g/s/blog/{blogId}/comment/{commentId}/g-vote?cv=1.2&value=1", headers=self.additional_headers(data=data), data=data)

        elif wikiId:
            data["eventSource"] = "PostDetailView"
            data = dumps(data)
            
            response = await self.session.post(f"/g/s/item/{wikiId}/comment/{commentId}/g-vote?cv=1.2&value=1", headers=self.additional_headers(data=data), data=data)

        else: raise exceptions.SpecifyType

        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def unlike_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None):
        """
        Remove a like from a Comment on a User's Wall, Blog or Wiki.

        **Parameters**
            - **commentId** : ID of the Comment.
            - **userId** : ID of the User. (for Walls)
            - **blogId** : ID of the Blog. (for Blogs)
            - **wikiId** : ID of the Wiki. (for Wikis)

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if userId: response = await self.session.delete(f"/g/s/user-profile/{userId}/comment/{commentId}/g-vote?eventSource=UserProfileView", headers=self.additional_headers())
        elif blogId: response = await self.session.delete(f"/g/s/blog/{blogId}/comment/{commentId}/g-vote?eventSource=PostDetailView", headers=self.additional_headers())
        elif wikiId: response = await self.session.delete(f"/g/s/item/{wikiId}/comment/{commentId}/g-vote?eventSource=PostDetailView", headers=self.additional_headers())
        else: raise exceptions.SpecifyType

        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def get_membership_info(self):
        """
        Get Information about your Amino+ Membership.

        **Parameters**
            - No parameters required.

        **Returns**
            - **Success** : :meth:`Membership Object <aminofixfix.lib.objects.Membership>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/membership?force=true", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.Membership(response.json()).Membership

    async def get_ta_announcements(self, language: str = "en", start: int = 0, size: int = 25):
        """
        Get the list of Team Amino's Announcement Blogs.

        **Parameters**
            - **language** : Language of the Blogs.
                - ``en``, ``es``, ``pt``, ``ar``, ``ru``, ``fr``, ``de``
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Blogs List <aminofixfix.lib.objects.BlogList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if language not in await self.get_supported_languages(): raise exceptions.UnsupportedLanguage(language)
        response = await self.session.get(f"/g/s/announcement?language={language}&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.BlogList(response.json()["blogList"]).BlogList

    async def get_wallet_info(self):
        """
        Get Information about the account's Wallet.

        **Parameters**
            - No parameters required.

        **Returns**
            - **Success** : :meth:`Wallet Object <aminofixfix.lib.objects.WalletInfo>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/wallet", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.WalletInfo(response.json()["wallet"]).WalletInfo

    async def get_wallet_history(self, start: int = 0, size: int = 25):
        """
        Get the Wallet's History Information.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Wallet Object <aminofixfix.lib.objects.WalletInfo>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/wallet/coin/history?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.WalletHistory(response.json()["coinHistoryList"]).WalletHistory

    async def get_from_deviceid(self, deviceId: str):
        """
        Get the User ID from an Device ID.

        **Parameters**
            - **deviceID** : ID of the Device.

        **Returns**
            - **Success** : :meth:`User ID <aminofixfix.lib.objects.UserProfile.userId>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/auid?deviceId={deviceId}")
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.json()["auid"]

    async def get_from_code(self, code: str):
        """
        Get the Object Information from the Amino URL Code.

        **Parameters**
            - **code** : Code from the Amino URL.
                - ``http://aminoapps.com/p/EXAMPLE``, the ``code`` is 'EXAMPLE'.

        **Returns**
            - **Success** : :meth:`From Code Object <aminofixfix.lib.objects.FromCode>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/link-resolution?q={code}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.FromCode(response.json()["linkInfoV2"]).FromCode

    async def get_from_id(self, objectId: str, objectType: int, comId: str = None):
        """
        Get the Object Information from the Object ID and Type.

        **Parameters**
            - **objectID** : ID of the Object. User ID, Blog ID, etc.
            - **objectType** : Type of the Object.
            - *comId* : ID of the Community. Use if the Object is in a Community.

        **Returns**
            - **Success** : :meth:`From Code Object <aminofixfix.lib.objects.FromCode>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({
            "objectId": objectId,
            "targetCode": 1,
            "objectType": objectType,
            "timestamp": inttime()
        })
        
        if comId: response = await self.session.post(f"/g/s-x{comId}/link-resolution", headers=self.additional_headers(data=data), data=data)
        else: response = await self.session.post(f"/g/s/link-resolution", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.FromCode(response.json()["linkInfoV2"]).FromCode

    async def get_supported_languages(self):
        """
        Get the List of Supported Languages by Amino.

        **Parameters**
            - No parameters required.

        **Returns**
            - **Success** : :meth:`List of Supported Languages <List>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/community-collection/supported-languages?start=0&size=100", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.json()["supportedLanguages"]

    async def claim_new_user_coupon(self):
        """
        Claim the New User Coupon available when a new account is created.

        **Parameters**
            - No parameters required.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.post(f"/g/s/coupon/new-user-coupon/claim", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def get_subscriptions(self, start: int = 0, size: int = 25):
        """
        Get Information about the account's Subscriptions.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`List <List>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/store/subscription?objectType=122&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.json()["storeSubscriptionItemList"]

    async def get_all_users(self, start: int = 0, size: int = 25):
        """
        Get list of users of Amino.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`User Profile Count List Object <aminofixfix.lib.objects.UserProfileCountList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = await self.session.get(f"/g/s/user-profile?type=recent&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.UserProfileCountList(response.json()).UserProfileCountList

    async def accept_host(self, chatId: str, requestId: str):
        data = dumps({})
        response = await self.session.post(f"/g/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def accept_organizer(self, chatId: str, requestId: str):
        self.accept_host(chatId, requestId)

    # Contributed by 'https://github.com/LynxN1'
    async def link_identify(self, code: str):
        response = await self.session.get(f"/g/s/community/link-identify?q=http%3A%2F%2Faminoapps.com%2Finvite%2F{code}", headers=self.additional_headers())
        return response.json()

    async def invite_to_vc(self, chatId: str, userId: str):
        """
        Invite a User to a Voice Chat

        **Parameters**
            - **chatId** - ID of the Chat
            - **userId** - ID of the User

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """

        data = dumps({
            "uid": userId
        })

        response = await self.session.post(f"/g/s/chat/thread/{chatId}/vvchat-presenter/invite", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def wallet_config(self, level: int):
        """
        Changes ads config

        **Parameters**
            - **level** - Level of the ads.
                - ``1``, ``2``

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """

        data = dumps({
            "adsLevel": level,
            "timestamp": inttime()
        })

        response = await self.session.post(f"/g/s/wallet/ads/config", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return response.status_code

    async def purchase(self, objectId: str, isAutoRenew: bool = False):
        data = dumps({
            "objectId": objectId,
            "objectType": 114,
            "v": 1,
            "paymentContext":
            {
                "discountStatus": 0,
                "isAutoRenew": isAutoRenew
            },
            "timestamp": inttime()
        })

        response = await self.session.post(f"/g/s/store/purchase", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: return exceptions.CheckException(response.json())
        else: return response.status_code

    async def get_public_communities(self, language: str = "en", size: int = 25):
        """
        Get public communites

        **Parameters**
            - **language** - Set up language

        **Returns**
            - **Success** : :meth:`Community List <aminofixfix.lib.objects.CommunityList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """

        response = await self.session.get(f"/g/s/topic/0/feed/community?language={language}&type=web-explore&categoryKey=recommendation&size={size}&pagingType=t", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.CommunityList(response.json()["communityList"]).CommunityList
        
    async def get_link_from_id(self, objectId: str, objectType: int = 0):
        """
        Get link from id

        **Parameters**
            - **objectId** - id of object
            - **objectType** - type of object

        **Returns**
            - **Success** : :meth:`Community List <aminofixfix.lib.objects.CommunityList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({
            "objectId": objectId,
            "objectType": objectType,
            "timestamp": inttime()
        })
        response = await self.session.post(f"/g/s/link-translation", data=data, headers=self.additional_headers(data=data))
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            return objects.LinkInfo(response.json()).LinkInfo

