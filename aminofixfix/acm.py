from __future__ import annotations
# ^ this thing should fix problem for python3.9 and lower(?)

from json import dumps
from typing import BinaryIO

from .client import Client
from .lib.helpers import inttime
from .lib import exceptions, headers, objects

class ACM(Client):
    """
    ACM is community manager.

    If you have leader or agent rights, you can edit your community.
    """
    def __init__(
            self, mainClient: Client,
            comId: str = None, aminoId: str = None, **kwargs
        ):
        """
        Init subclient.

        Accepting:
        - mainClient: aminofixfix.Client
        - comId: str | int | None
        - aminoId: str | None
            - you can pass only one thing
            - comId will be taken first

    
        
        \- imperialwool, where is another fields of subclient??? ;-;

        \- its in main client lol why you need to pass them again
        """
        Client.__init__(
            self, deviceId=mainClient.device_id, proxies=mainClient.proxies,
            autoDevice=mainClient.autoDevice, userAgent=mainClient.user_agent,
            http2_enabled=mainClient.http2_enabled,
            own_timeout=mainClient.timeout_settings,
            socket_enabled=False,
            api_library=mainClient.api_library or objects.APILibraries.HTTPX
        )

        self.profile = mainClient.profile
        if comId is not None:
            self.comId = comId

        if aminoId is not None:
            link = "http://aminoapps.com/c/"
            self.comId = self.get_from_code(link + aminoId).comId

    # TODO : Finish the imaging sizing, might not work for every picture...
    def create_community(self, name: str, tagline: str, icon: BinaryIO, themeColor: str, joinType: int = 0, primaryLanguage: str = "en"):
        """
        Creating community.

        Accepting:
        - name: str
        - tagline: str
        - icon: BinaryIO
        - themeColor: str
        - joinType: int = 0
            - 0 is open
            - 1 is semi-closed (you can request to be added in community)
            - 2 is fully closed (UNAVAILABLE AT ALL FOR ALL APPROVED COMMUNITIES)
        - primaryLanguage: str = "en"

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "icon": {
                "height": 512.0,
                "imageMatrix": [1.6875, 0.0, 108.0, 0.0, 1.6875, 497.0, 0.0, 0.0, 1.0],
                "path": self.upload_media(icon),
                "width": 512.0,
                "x": 0.0,
                "y": 0.0
            },
            "joinType": joinType,
            "name": name,
            "primaryLanguage": primaryLanguage,
            "tagline": tagline,
            "templateId": 9,
            "themeColor": themeColor,
            "timestamp": inttime()
        })

        response = self.session.post(f"/g/s/community", headers=self.additional_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.status_code

    def delete_community(self, email: str, password: str, verificationCode: str):
        """
        Deleting community.

        ...Why you need that?

        Accepting:
        - email: str
        - password: str
        - verificationCode: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "secret": f"0 {password}",
            "validationContext": {
                "data": {
                    "code": verificationCode
                },
                "type": 1,
                "identity": email
            },
            "deviceID": self.device_id
        })

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/g/s-x{self.comId}/community/delete-request", headers=self.additional_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.status_code

    def list_communities(self, start: int = 0, size: int = 25):
        """
        Getting all communities where you are leader.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `dict`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/g/s/community/managed?start={start}&size={size}", headers=self.additional_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return objects.CommunityList(response.json()["communityList"]).CommunityList

    def get_categories(self, start: int = 0, size: int = 25):
        """
        Getting categories of communities.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `dict`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.get(f"/x{self.comId}/s/blog-category?start={start}&size={size}", headers=self.additional_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.json()

    def change_sidepanel_color(self, color: str):
        """
        Change sidepanel color.

        Accepting:
        - color: str
            - should be hex color like "#123ABC"

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "path": "appearance.leftSidePanel.style.iconColor",
            "value": color if len(color) == 7 else "#000000",
            "timestamp": inttime()
        })

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/configuration", headers=self.additional_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return response.status_code
        else: return response.json()

    def get_themepack_info(self):
        """
        This method can be used for getting info about current themepack of community.

        Recieving:
        - object
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.get(f"/g/s-x{self.comId}/community/info?withTopicList=1&withInfluencerList=1&influencerListOrderStrategy=fansCount", headers=self.additional_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.json()['community']['themePack']
    
    def upload_themepack_raw(self, file: BinaryIO):
        """
        Uploading new themepack.

        File is technically a ZIP file, but you should rename .zip to .ndthemepack.
        Also this "zip" file have specific stucture.

        The structure is:
        - theme_info.json
        - images/
            - background/
                - background_375x667.jpeg
                - background_750x1334.jpeg
            - logo/
                - logo_219x44.png
                - logo_439x88.png
            - titlebar/
                - titlebar_320x64.jpeg
                - titlebar_640x128.jpeg
            - titlebarBackground/
                - titlebarBackground_375x667.jpeg
                - titlebarBackground_750x1334.jpeg
        
        And now its time to explain tricky "theme.json".
        
        - I can't really explain "id" here, *maybe* its random uuid4.
        - "format-version" **SHOULD** be "1.0", its themepack format version
        - "author" is.. nickname or aminoId of theme uploader (or agent, it doesnt matter)
        - "revision".. u *can* leave revision that you have, Amino will do all stuff instead of you
        - "theme-color" should be **VALID** hex color. I think they didn't fixed that you can pass invalid hex color, but it will cost a crash on every device
        
        About images in "theme.json":

        - for logo folder stands key "logo" in json, for titlebar - "titlebar-image", for titlebarBackground - "titlebar-background-image", for background - "background-image"
        - you can *pass* or *not pass* these keys in json, if they are not passed they will ignored/deleted
        - keys have array values like this:
            - [
                {
                    "height": height*2,
                    "path": "images/logo/logo_width*2xheight*2.png",
                    "width": width*2,
                    "x": 0,
                    "y": 0
                },
                {
                    "height": height,
                    "path": "images/logo/logo_widthxheight.png",
                    "width": width,
                    "x": 0,
                    "y": 0
                }
            ]
        - default values of height (h) and width (w) for every key:
            - "background-image":
                - w = 375
                - h = 667
            - "logo":
                - w = 196
                - h = 44
            - "titlebar-background-image":
                - w = 375
                - h = 667
            - "titlebar-image":
                - w = 320
                - h = 64
        - you *can* specify "x" and "y" if you want
        - theoretically you can provide different "w" and "h"

        Accepting:
        - file: BinaryIO

        Recieving:
        - object
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/media/upload/target/community-theme-pack", data=file.read(), headers=headers.Headers(data=file.read()).s_headers, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.json()

    def promote(self, userId: str, rank: str):
        """
        Promote user to curator, leader or agent.

        Accepting:
        - userId: str
        - rank: str
            - can be only "agent"/"transfer-agent", "leader" or "curator"

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        rank = rank.lower().replace("agent", "transfer-agent")

        if rank.lower() not in ["transfer-agent", "leader", "curator"]:
            raise exceptions.WrongType(rank)

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/user-profile/{userId}/{rank}", headers=self.additional_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.status_code

    def get_join_requests(self, start: int = 0, size: int = 25):
        """
        Get all requests to join your precious community.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `JoinRequest`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if self.comId is None: raise exceptions.CommunityNeeded()

        response = self.session.get(f"/x{self.comId}/s/community/membership-request?status=pending&start={start}&size={size}", headers=self.additional_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return objects.JoinRequest(response.json()).JoinRequest

    def accept_join_request(self, userId: str):
        """
        Accept user to join your precious community.

        "Congratulations!

        Your REQUEST TO JOIN has been approved."

        https://www.youtube.com/watch?v=LabIat9t-uY

        Accepting:
        - userId: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({})

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/membership-request/{userId}/accept", headers=self.additional_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.status_code

    def reject_join_request(self, userId: str):
        """
        Reject user to join your precious community.

        "Congratulations!

        Your REQUEST TO JOIN has been denied.

        Don't even bother trying again."

        https://www.youtube.com/watch?v=3vH6GBbeAgA

        Accepting:
        - userId: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({})

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/membership-request/{userId}/reject", headers=self.additional_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.status_code

    def get_community_stats(self):
        """
        Get community statistics.

        Recieving:
        - object `CommunityStats`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if self.comId is None: raise exceptions.CommunityNeeded()

        response = self.session.get(f"/x{self.comId}/s/community/stats", headers=self.additional_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return objects.CommunityStats(response.json()["communityStats"]).CommunityStats

    def get_community_user_stats(self, type: str, start: int = 0, size: int = 25):
        """
        Get community user statistics.

        Accepting:
        - type: str
            - can be only "leader" or "curator"
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `UserProfileList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if self.comId is None: raise exceptions.CommunityNeeded()

        if type.lower() == "leader": target = "leader"
        elif type.lower() == "curator": target = "curator"
        else: raise exceptions.WrongType(type)

        response = self.session.get(f"/x{self.comId}/s/community/stats/moderation?type={target}&start={start}&size={size}", headers=self.additional_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return objects.UserProfileList(response.json()["userProfileList"]).UserProfileList

    def change_welcome_message(self, message: str, isEnabled: bool = True):
        """
        Change welcome message of community.

        Accepting:
        - message: str
        - isEnabled: bool = True

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "path": "general.welcomeMessage",
            "value": {
                "enabled": isEnabled,
                "text": message
            },
            "timestamp": inttime()
        })

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/configuration", headers=self.additional_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.status_code

    def change_amino_id(self, aminoId: str):
        """
        Change AminoID of community.

        Accepting:
        - aminoId: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "endpoint": aminoId,
            "timestamp": inttime()
        })

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/settings", headers=self.additional_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.status_code

    def change_guidelines(self, message: str):
        """
        Change rules of community.

        Accepting:
        - message: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "content": message,
            "timestamp": inttime()
        })

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/guideline", headers=self.additional_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.status_code

    def edit_community(self, name: str = None, description: str = None, aminoId: str = None, primaryLanguage: str = None, themePackUrl: str = None):
        """
        Edit community.

        Accepting:
        - name: str = None
        - description: str = None
        - aminoId: str = None
        - primaryLanguage: str = None
        - themePackUrl: str = None

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        
        data = {"timestamp": inttime()}

        if name is not None: data["name"] = name
        if description is not None: data["content"] = description
        if aminoId is not None: data["endpoint"] = aminoId
        if primaryLanguage is not None: data["primaryLanguage"] = primaryLanguage
        if themePackUrl is not None: data["themePackUrl"] = themePackUrl

        data = dumps(data)

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/settings", data=data, headers=self.additional_headers(data=data), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.status_code

    def change_module(self, module: str, isEnabled: bool):
        """
        Enable or disable module.

        Accepting:
        - module: str
            - can be only "chat", "livechat", "screeningroom", "publicchats", "posts",
              "ranking", "leaderboards", "featured", "featuredposts", "featuredusers",
              "featuredchats", "sharedfolder", "influencer", "catalog",
              "externalcontent" or "topiccategories"
        - isEnabled: bool

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if module.lower() == "chat": mod = "module.chat.enabled"
        elif module.lower() == "livechat": mod = "module.chat.avChat.videoEnabled"
        elif module.lower() == "screeningroom": mod = "module.chat.avChat.screeningRoomEnabled"
        elif module.lower() == "publicchats": mod = "module.chat.publicChat.enabled"
        elif module.lower() == "posts": mod = "module.post.enabled"
        elif module.lower() == "ranking": mod = "module.ranking.enabled"
        elif module.lower() == "leaderboards": mod = "module.ranking.leaderboardEnabled"
        elif module.lower() == "featured": mod = "module.featured.enabled"
        elif module.lower() == "featuredposts": mod = "module.featured.postEnabled"
        elif module.lower() == "featuredusers": mod = "module.featured.memberEnabled"
        elif module.lower() == "featuredchats": mod = "module.featured.publicChatRoomEnabled"
        elif module.lower() == "sharedfolder": mod = "module.sharedFolder.enabled"
        elif module.lower() == "influencer": mod = "module.influencer.enabled"
        elif module.lower() == "catalog": mod = "module.catalog.enabled"
        elif module.lower() == "externalcontent": mod = "module.externalContent.enabled"
        elif module.lower() == "topiccategories": mod = "module.topicCategories.enabled"
        else: raise exceptions.SpecifyType()

        data = dumps({
            "path": mod,
            "value": isEnabled,
            "timestamp": inttime()
        })

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/configuration", headers=self.additional_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.status_code

    def add_influencer(self, userId: str, monthlyFee: int):
        """
        Create fanclub.

        Accepting:
        - userId: str
        - monthlyFee: int
            - can be maximum 500 coins per month

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "monthlyFee": monthlyFee,
            "timestamp": inttime()
        })

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/influencer/{userId}", headers=self.additional_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.status_code

    def remove_influencer(self, userId: str):
        """
        Delete fanclub.

        Accepting:
        - userId: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.delete(f"/x{self.comId}/s/influencer/{userId}", headers=self.additional_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.status_code

    def get_notice_list(self, start: int = 0, size: int = 25):
        """
        Get notices list.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `NoticeList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.get(f"/x{self.comId}/s/notice?type=management&status=1&start={start}&size={size}", headers=self.additional_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return objects.NoticeList(response.json()["noticeList"]).NoticeList

    def delete_pending_role(self, noticeId: str):
        """
        Delete pending role.

        Accepting:
        - noticeId: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.delete(f"/x{self.comId}/s/notice/{noticeId}", headers=self.additional_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.status_code
