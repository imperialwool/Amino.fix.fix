from __future__ import annotations
# ^ this thing should fix problem for python3.9 and lower(?)

from typing import BinaryIO
from json import loads, dumps
from time import time as timestamp

from . import client
from .lib import exceptions, headers, objects

class ACM(client.Client):
    def __init__(self, profile: objects.UserProfile, comId: str = None, proxies: dict = None):
        client.Client.__init__(self)

        self.profile = profile
        self.comId = comId
        self.proxies = proxies

    # TODO : Finish the imaging sizing, might not work for every picture...
    def create_community(self, name: str, tagline: str, icon: BinaryIO, themeColor: str, joinType: int = 0, primaryLanguage: str = "en"):
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
            "timestamp": int(timestamp() * 1000)
        })

        response = self.session.post(f"/g/s/community", headers=self.parse_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return response.status_code

    def delete_community(self, email: str, password: str, verificationCode: str):
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
        response = self.session.post(f"/g/s-x{self.comId}/community/delete-request", headers=self.parse_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return response.status_code

    def list_communities(self, start: int = 0, size: int = 25):
        response = self.session.get(f"/g/s/community/managed?start={start}&size={size}", headers=self.parse_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return objects.CommunityList(loads(response.text)["communityList"]).CommunityList

    def get_categories(self, start: int = 0, size: int = 25):
        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.get(f"/x{self.comId}/s/blog-category?start={start}&size={size}", headers=self.parse_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return loads(response.text)

    def change_sidepanel_color(self, color: str):
        data = dumps({
            "path": "appearance.leftSidePanel.style.iconColor",
            "value": color,
            "timestamp": int(timestamp() * 1000)
        })

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/configuration", headers=self.parse_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return response.status_code
        else: return loads(response.text)

    def get_themepack_info(self, file: BinaryIO):
        """
        This method can be used for getting info about current themepack of community.
        """
        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.get(f"/g/s-x{self.comId}/community/info?withTopicList=1&withInfluencerList=1&influencerListOrderStrategy=fansCount", data=file.read(), headers=headers.Headers(data=file.read()).s_headers, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
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
        """
        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/media/upload/target/community-theme-pack", data=file.read(), headers=headers.Headers(data=file.read()).s_headers, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return loads(response.text)

    def promote(self, userId: str, rank: str):
        rank = rank.lower().replace("agent", "transfer-agent")

        if rank.lower() not in ["transfer-agent", "leader", "curator"]:
            raise exceptions.WrongType(rank)

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/user-profile/{userId}/{rank}", headers=self.parse_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return response.status_code

    def get_join_requests(self, start: int = 0, size: int = 25):
        if self.comId is None: raise exceptions.CommunityNeeded()

        response = self.session.get(f"/x{self.comId}/s/community/membership-request?status=pending&start={start}&size={size}", headers=self.parse_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return objects.JoinRequest(loads(response.text)).JoinRequest

    def accept_join_request(self, userId: str):
        data = dumps({})

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/membership-request/{userId}/accept", headers=self.parse_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return response.status_code

    def reject_join_request(self, userId: str):
        data = dumps({})

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/membership-request/{userId}/reject", headers=self.parse_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return response.status_code

    def get_community_stats(self):
        if self.comId is None: raise exceptions.CommunityNeeded()

        response = self.session.get(f"/x{self.comId}/s/community/stats", headers=self.parse_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return objects.CommunityStats(loads(response.text)["communityStats"]).CommunityStats

    def get_community_user_stats(self, type: str, start: int = 0, size: int = 25):
        if self.comId is None: raise exceptions.CommunityNeeded()

        if type.lower() == "leader": target = "leader"
        elif type.lower() == "curator": target = "curator"
        else: raise exceptions.WrongType(type)

        response = self.session.get(f"/x{self.comId}/s/community/stats/moderation?type={target}&start={start}&size={size}", headers=self.parse_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return objects.UserProfileList(loads(response.text)["userProfileList"]).UserProfileList

    def change_welcome_message(self, message: str, isEnabled: bool = True):
        data = dumps({
            "path": "general.welcomeMessage",
            "value": {
                "enabled": isEnabled,
                "text": message
            },
            "timestamp": int(timestamp() * 1000)
        })

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/configuration", headers=self.parse_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return response.status_code

    def change_amino_id(self, aminoId: str):
        data = dumps({
            "endpoint": aminoId,
            "timestamp": int(timestamp() * 1000)
        })

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/settings", headers=self.parse_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return response.status_code

    def change_guidelines(self, message: str):
        data = dumps({
            "content": message,
            "timestamp": int(timestamp() * 1000)
        })

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/guideline", headers=self.parse_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return response.status_code

    def edit_community(self, name: str = None, description: str = None, aminoId: str = None, primaryLanguage: str = None, themePackUrl: str = None):
        data = {"timestamp": int(timestamp() * 1000)}

        if name is not None: data["name"] = name
        if description is not None: data["content"] = description
        if aminoId is not None: data["endpoint"] = aminoId
        if primaryLanguage is not None: data["primaryLanguage"] = primaryLanguage
        if themePackUrl is not None: data["themePackUrl"] = themePackUrl

        data = dumps(data)

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/settings", data=data, headers=self.parse_headers(data=data), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return response.status_code

    def change_module(self, module: str, isEnabled: bool):
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
            "timestamp": int(timestamp() * 1000)
        })

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/community/configuration", headers=self.parse_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return response.status_code

    def add_influencer(self, userId: str, monthlyFee: int):
        data = dumps({
            "monthlyFee": monthlyFee,
            "timestamp": int(timestamp() * 1000)
        })

        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.post(f"/x{self.comId}/s/influencer/{userId}", headers=self.parse_headers(data=data), data=data, proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return response.status_code

    def remove_influencer(self, userId: str):
        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.delete(f"/x{self.comId}/s/influencer/{userId}", headers=self.parse_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return response.status_code

    def get_notice_list(self, start: int = 0, size: int = 25):
        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.get(f"/x{self.comId}/s/notice?type=management&status=1&start={start}&size={size}", headers=self.parse_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return objects.NoticeList(loads(response.text)["noticeList"]).NoticeList

    def delete_pending_role(self, noticeId: str):
        if self.comId is None: raise exceptions.CommunityNeeded()
        response = self.session.delete(f"/x{self.comId}/s/notice/{noticeId}", headers=self.parse_headers(), proxies=self.proxies)
        if response.status_code != 200: return exceptions.CheckException(response.text)
        else: return response.status_code
