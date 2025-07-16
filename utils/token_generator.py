import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
import my_pb2
import output_pb2
import logging
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warning
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

class TokenGenerator:
    def __init__(self, cache=None):
        self.cache = cache
        self.AES_KEY = b'Yg&tc%DEuh6%Zc^8'
        self.AES_IV = b'6oyZDr22E3ychjM%'
        
    def get_token(self, password, uid):
        """Get access token from Garena API"""
        try:
            url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
            headers = {
                "Host": "100067.connect.garena.com",
                "User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "close"
            }
            data = {
                "uid": uid,
                "password": password,
                "response_type": "token",
                "client_type": "2",
                "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
                "client_id": "100067"
            }
            res = requests.post(url, headers=headers, data=data, timeout=10)
            if res.status_code != 200:
                return None
            token_json = res.json()
            if "access_token" in token_json and "open_id" in token_json:
                return token_json
            else:
                return None
        except Exception as e:
            logging.error(f"Error getting token: {str(e)}")
            return None

    def encrypt_message(self, key, iv, plaintext):
        """Encrypt message using AES CBC"""
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_message = pad(plaintext, AES.block_size)
        return cipher.encrypt(padded_message)

    def parse_response(self, content):
        """Parse protobuf response to dictionary"""
        response_dict = {}
        lines = content.split("\n")
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                response_dict[key.strip()] = value.strip().strip('"')
        return response_dict

    def generate_token(self, uid, password):
        """Generate JWT token for given UID and password"""
        try:
            # Check cache first
            cache_key = f"token_{uid}_{password}"
            if self.cache:
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    return cached_result

            # Get access token
            token_data = self.get_token(password, uid)
            if not token_data:
                return {
                    "status": "failed",
                    "error": "Invalid UID or password"
                }

            # Create game data
            game_data = my_pb2.GameData()
            game_data.timestamp = "2024-12-05 18:15:32"
            game_data.game_name = "free fire"
            game_data.game_version = 1
            game_data.version_code = "1.108.3"
            game_data.os_info = "Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)"
            game_data.device_type = "Handheld"
            game_data.network_provider = "Verizon Wireless"
            game_data.connection_type = "WIFI"
            game_data.screen_width = 1280
            game_data.screen_height = 960
            game_data.dpi = "240"
            game_data.cpu_info = "ARMv7 VFPv3 NEON VMH | 2400 | 4"
            game_data.total_ram = 5951
            game_data.gpu_name = "Adreno (TM) 640"
            game_data.gpu_version = "OpenGL ES 3.0"
            game_data.user_id = "Google|74b585a9-0268-4ad3-8f36-ef41d2e53610"
            game_data.ip_address = "172.190.111.97"
            game_data.language = "en"
            game_data.open_id = token_data['open_id']
            game_data.access_token = token_data['access_token']
            game_data.platform_type = 4
            game_data.device_form_factor = "Handheld"
            game_data.device_model = "Asus ASUS_I005DA"
            game_data.field_60 = 32968
            game_data.field_61 = 29815
            game_data.field_62 = 2479
            game_data.field_63 = 914
            game_data.field_64 = 31213
            game_data.field_65 = 32968
            game_data.field_66 = 31213
            game_data.field_67 = 32968
            game_data.field_70 = 4
            game_data.field_73 = 2
            game_data.library_path = "/data/app/com.dts.freefireth-QPvBnTUhYWE-7DMZSOGdmA==/lib/arm"
            game_data.field_76 = 1
            game_data.apk_info = "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-QPvBnTUhYWE-7DMZSOGdmA==/base.apk"
            game_data.field_78 = 6
            game_data.field_79 = 1
            game_data.os_architecture = "32"
            game_data.build_number = "2019117877"
            game_data.field_85 = 1
            game_data.graphics_backend = "OpenGLES2"
            game_data.max_texture_units = 16383
            game_data.rendering_api = 4
            game_data.encoded_field_89 = "\u0017T\u0011\u0017\u0002\b\u000eUMQ\bEZ\u0003@ZK;Z\u0002\u000eV\ri[QVi\u0003\ro\t\u0007e"
            game_data.field_92 = 9204
            game_data.marketplace = "3rd_party"
            game_data.encryption_key = "KqsHT2B4It60T/65PGR5PXwFxQkVjGNi+IMCK3CFBCBfrNpSUA1dZnjaT3HcYchlIFFL1ZJOg0cnulKCPGD3C3h1eFQ="
            game_data.total_storage = 111107
            game_data.field_97 = 1
            game_data.field_98 = 1
            game_data.field_99 = "4"
            game_data.field_100 = "4"

            # Serialize and encrypt
            serialized_data = game_data.SerializeToString()
            encrypted_data = self.encrypt_message(self.AES_KEY, self.AES_IV, serialized_data)
            edata = binascii.hexlify(encrypted_data).decode()

            # Send request to generate JWT
            url = "https://loginbp.common.ggbluefox.com/MajorLogin"
            headers = {
                'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
                'Connection': "Keep-Alive",
                'Accept-Encoding': "gzip",
                'Content-Type': "application/octet-stream",
                'Expect': "100-continue",
                'X-Unity-Version': "2018.4.11f1",
                'X-GA': "v1 1",
                'ReleaseVersion': "OB49"
            }

            response = requests.post(url, data=bytes.fromhex(edata), headers=headers, verify=False)

            if response.status_code == 200:
                example_msg = output_pb2.Garena_420()
                try:
                    example_msg.ParseFromString(response.content)
                    response_dict = self.parse_response(str(example_msg))
                    
                    result = {
                        "status": "success",
                        "token": response_dict.get("token", "N/A")
                    }
                    
                    # Cache the result
                    if self.cache:
                        self.cache.set(cache_key, result, timeout=25200)
                    
                    return result
                except Exception as e:
                    logging.error(f"Failed to deserialize response: {str(e)}")
                    return {
                        "status": "failed",
                        "error": f"Failed to deserialize response: {str(e)}"
                    }
            else:
                logging.error(f"HTTP error: {response.status_code}")
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.reason}"
                }
        except Exception as e:
            logging.error(f"Token generation error: {str(e)}")
            return {
                "status": "failed",
                "error": f"Internal error: {str(e)}"
            }
