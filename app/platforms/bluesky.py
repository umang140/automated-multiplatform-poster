from datetime import datetime, timezone

import httpx

from app.platforms.base import BasePlatform


class BlueskyPlatform(BasePlatform):
    name = "Bluesky"

    def missing_credentials(self):
        return self._need(
            ("BLUESKY_HANDLE", self.settings.bluesky_handle),
            ("BLUESKY_APP_PASSWORD", self.settings.bluesky_app_password),
        )

    async def publish(self, client: httpx.AsyncClient, message: str):
        pds = (self.settings.bluesky_pds_url or "https://bsky.social").rstrip("/")

        login = await client.post(
            f"{pds}/xrpc/com.atproto.server.createSession",
            json={
                "identifier": self.settings.bluesky_handle,
                "password": self.settings.bluesky_app_password,
            },
        )
        login.raise_for_status()
        session = login.json()

        created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        post = await client.post(
            f"{pds}/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {session['accessJwt']}"},
            json={
                "repo": session["did"],
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": message,
                    "createdAt": created,
                },
            },
        )
        post.raise_for_status()

        uri = post.json().get("uri", "")
        rkey = uri.rsplit("/", 1)[-1] if uri else None
        handle = session.get("handle") or self.settings.bluesky_handle
        url = f"https://bsky.app/profile/{handle}/post/{rkey}" if rkey else None
        return url, True
