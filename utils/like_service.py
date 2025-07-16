import json
import aiohttp
import asyncio
import requests
import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf.message import DecodeError
from google.protobuf.json_format import MessageToJson
import like_pb2
import like_count_pb2
import uid_generator_pb2


class LikeService:
    def __init__(self):
        self.AES_KEY = b"Yg&tc%DEuh6%Zc^8"
        self.AES_IV = b"6oyZDr22E3ychjM%"

    def encrypt_message(self, plaintext):
        """Encrypt message using AES CBC"""
        try:
            cipher = AES.new(self.AES_KEY, AES.MODE_CBC, self.AES_IV)
            padded_message = pad(plaintext, AES.block_size)
            encrypted_message = cipher.encrypt(padded_message)
            return binascii.hexlify(encrypted_message).decode("utf-8")
        except Exception:
            return None

    def create_like_protobuf(self, user_id, region):
        """Create like protobuf message"""
        try:
            message = like_pb2.like()
            message.uid = int(user_id)
            message.region = region
            return message.SerializeToString()
        except Exception:
            return None

    def create_uid_protobuf(self, uid):
        """Create UID protobuf message"""
        try:
            message = uid_generator_pb2.uid_generator()
            message.saturn_ = int(uid)
            message.garena = 1
            return message.SerializeToString()
        except Exception:
            return None

    def decode_protobuf(self, binary):
        """Decode protobuf response"""
        try:
            items = like_count_pb2.Info()
            items.ParseFromString(binary)
            return items
        except DecodeError:
            return None
        except Exception:
            return None

    def load_tokens(self, server_name):
        """Load tokens for specified server"""
        try:
            if server_name == "IND":
                path = "tokens/ind.json"
            elif server_name in {"BR", "US", "SAC", "NA"}:
                path = "tokens/br.json"
            else:
                path = "tokens/bd.json"
            
            with open(path, "r") as f:
                tokens = json.load(f)
                return tokens if tokens else None
        except Exception:
            return None

    def enc(self, uid):
        """Encrypt UID for requests"""
        protobuf_data = self.create_uid_protobuf(uid)
        if protobuf_data is None:
            return None
        return self.encrypt_message(protobuf_data)

    async def send_like_request(self, encrypted_uid, token, url):
        """Send single like request"""
        try:
            edata = bytes.fromhex(encrypted_uid)
            headers = {
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Expect": "100-continue",
                "X-Unity-Version": "2018.4.11f1",
                "X-GA": "v1 1",
                "ReleaseVersion": "OB48",
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=edata, headers=headers) as response:
                    return await response.text()
        except Exception:
            return None

    async def send_multiple_like_requests(self, uid, server_name, url):
        """Send multiple like requests asynchronously"""
        region = server_name
        protobuf_message = self.create_like_protobuf(uid, region)
        if protobuf_message is None:
            return None
        
        encrypted_uid = self.encrypt_message(protobuf_message)
        if encrypted_uid is None:
            return None

        tokens = self.load_tokens(server_name)
        if tokens is None:
            return None

        tasks = []
        for i in range(100):  # Send 100 like requests
            token = tokens[i % len(tokens)]["token"]
            tasks.append(self.send_like_request(encrypted_uid, token, url))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    def make_player_info_request(self, encrypt, server_name, token):
        """Get player information"""
        if server_name == "IND":
            url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            url = "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
        else:
            url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"

        edata = bytes.fromhex(encrypt)
        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Expect": "100-continue",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB49",
        }
        
        try:
            response = requests.post(url, data=edata, headers=headers, verify=False, timeout=10)
            if response.status_code == 200:
                return self.decode_protobuf(response.content)
            else:
                # Log the error for debugging
                print(f"Player info request failed with status {response.status_code}")
                return None
        except Exception as e:
            print(f"Player info request error: {str(e)}")
            return None

    async def process_like_request(self, uid, server_name):
        """Process complete like operation"""
        try:
            tokens = self.load_tokens(server_name)
            if tokens is None:
                raise Exception("Failed to load tokens.")
            
            token = tokens[0]["token"]
            encrypted_uid = self.enc(uid)

            # Get initial player info
            before = self.make_player_info_request(encrypted_uid, server_name, token)
            if before is None:
                raise Exception("Failed to retrieve initial player info.")

            data_before = json.loads(MessageToJson(before))
            before_like = int(data_before.get("AccountInfo", {}).get("Likes", 0))

            # Determine like URL based on server
            if server_name == "IND":
                url = "https://client.ind.freefiremobile.com/LikeProfile"
            elif server_name in {"BR", "US", "SAC", "NA"}:
                url = "https://client.us.freefiremobile.com/LikeProfile"
            else:
                url = "https://clientbp.ggblueshark.com/LikeProfile"

            # Send multiple like requests
            await self.send_multiple_like_requests(uid, server_name, url)

            # Get updated player info
            after = self.make_player_info_request(encrypted_uid, server_name, token)
            if after is None:
                raise Exception("Failed to retrieve player info after like requests.")

            data_after = json.loads(MessageToJson(after))
            after_like = int(data_after.get("AccountInfo", {}).get("Likes", 0))
            player_uid = int(data_after.get("AccountInfo", {}).get("UID", 0))
            player_name = str(data_after.get("AccountInfo", {}).get("PlayerNickname", ""))
            like_given = after_like - before_like
            status = 1 if like_given != 0 else 2

            return {
                "status": status,
                "message": "Like operation successful" if status == 1 else "No likes added",
                "player": {
                    "uid": player_uid,
                    "nickname": player_name,
                },
                "likes": {
                    "before": before_like,
                    "after": after_like,
                    "added_by_api": like_given,
                },
            }

        except Exception as e:
            raise Exception(f"Error processing like request: {str(e)}")