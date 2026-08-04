from __future__ import annotations
import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
SCOPES=["https://www.googleapis.com/auth/youtube.upload"]
class YouTubeUploader:
    def upload(self,video:Path,thumbnail:Path,metadata:dict,settings:dict)->str:
        secrets=Path(os.getenv("YOUTUBE_CLIENT_SECRETS","config/client_secret.json")); token=Path("config/youtube_token.json")
        creds=Credentials.from_authorized_user_file(token,SCOPES) if token.exists() else None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
            else: creds=InstalledAppFlow.from_client_secrets_file(str(secrets),SCOPES).run_local_server(port=0)
            token.write_text(creds.to_json(),encoding="utf-8")
        yt=build("youtube","v3",credentials=creds)
        body={"snippet":{"title":metadata["title"][:100],"description":metadata["description"],"tags":metadata.get("tags",[])[:30],"categoryId":settings.get("category_id","25")},"status":{"privacyStatus":settings.get("privacy_status","private"),"selfDeclaredMadeForKids":False}}
        response=yt.videos().insert(part="snippet,status",body=body,media_body=MediaFileUpload(str(video),chunksize=-1,resumable=True)).execute()
        video_id=response["id"]; yt.thumbnails().set(videoId=video_id,media_body=MediaFileUpload(str(thumbnail))).execute(); return video_id
