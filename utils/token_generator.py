import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
import my_pb2
import output_pb2
import logging
import warnings
from urllib3.exceptions import InsecureRequestWarning
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
import random
import uuid

# Disable SSL warning
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

class TokenGenerator:
    def __init__(self, cache=None):
        self.cache = cache
        self.AES_KEY = b'Yg&tc%DEuh6%Zc^8'
        self.AES_IV = b'6oyZDr22E3ychjM%'
        
        # Setup session with connection pooling and retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.05,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=50, pool_maxsize=50)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
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
            res = self.session.post(url, headers=headers, data=data, timeout=5)
            if res.status_code != 200:
                return None
            token_json = res.json()
            if "access_token" in token_json and "open_id" in token_json:
                return token_json
            else:
                return None
        except requests.exceptions.Timeout:
            logging.error("Request timed out while getting token")
            return None
        except requests.exceptions.ConnectionError:
            logging.error("Connection error while getting token")
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
            # Don't use cache for unique tokens - generate fresh each time
            # This ensures each token is unique and not the same every time

            # Get access token
            token_data = self.get_token(password, uid)
            if not token_data:
                return {
                    "status": "failed",
                    "error": "Invalid UID or password"
                }

            # Create game data with unique elements for each token
            game_data = my_pb2.GameData()
            # Add microseconds for absolute uniqueness
            unique_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            game_data.timestamp = unique_timestamp
            game_data.game_name = "free fire"
            game_data.game_version = 1
            game_data.version_code = "1.108.3"
            game_data.os_info = "Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)"
            game_data.device_type = "Handheld"
            # Randomize network provider for variety
            providers = ["Verizon Wireless", "AT&T", "T-Mobile", "Sprint"]
            game_data.network_provider = random.choice(providers)
            connections = ["WIFI", "4G", "5G"]
            game_data.connection_type = random.choice(connections)
            # Vary screen dimensions slightly
            game_data.screen_width = random.randint(1270, 1290)
            game_data.screen_height = random.randint(950, 970)
            game_data.dpi = str(random.randint(235, 245))
            game_data.cpu_info = "ARMv7 VFPv3 NEON VMH | 2400 | 4"
            game_data.total_ram = random.randint(5900, 6000)
            game_data.gpu_name = "Adreno (TM) 640"
            game_data.gpu_version = "OpenGL ES 3.0"
            # Generate unique user_id for each token
            game_data.user_id = f"Google|{str(uuid.uuid4())}"
            # Randomize IP address for uniqueness
            game_data.ip_address = f"172.190.{random.randint(100, 199)}.{random.randint(10, 254)}"
            game_data.language = "en"
            game_data.open_id = token_data['open_id']
            game_data.access_token = token_data['access_token']
            game_data.platform_type = 4
            game_data.device_form_factor = "Handheld"
            # Randomize device models for variety
            device_models = [
                "Asus ASUS_I005DA", "Samsung SM-G991B", "OnePlus Nord CE 5G",
                "Xiaomi Mi 11", "Huawei P30 Pro", "Google Pixel 5", 
                "Sony Xperia 1 III", "Motorola Edge 20"
            ]
            game_data.device_model = random.choice(device_models)
            # Add random values to ensure unique tokens each time
            game_data.field_60 = random.randint(32900, 32999)
            game_data.field_61 = random.randint(29800, 29899)
            game_data.field_62 = random.randint(2470, 2490)
            game_data.field_63 = random.randint(910, 920)
            game_data.field_64 = random.randint(31200, 31250)
            game_data.field_65 = random.randint(32900, 32999)
            game_data.field_66 = random.randint(31200, 31250)
            game_data.field_67 = random.randint(32900, 32999)
            game_data.field_70 = random.randint(3, 5)
            game_data.field_73 = random.randint(1, 3)
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
            game_data.field_92 = random.randint(9200, 9210)
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

            response = self.session.post(url, data=bytes.fromhex(edata), headers=headers, verify=False, timeout=3)

            if response.status_code == 200:
                example_msg = output_pb2.Garena_420()
                try:
                    example_msg.ParseFromString(response.content)
                    response_dict = self.parse_response(str(example_msg))
                    
                    result = {
                        "status": "success",
                        "token": response_dict.get("token", "N/A")
                    }
                    
                    # Don't cache to ensure unique tokens every time
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
        except requests.exceptions.Timeout:
            logging.error("Request timed out during JWT generation")
            return {
                "status": "failed",
                "error": "Request timed out - please try again"
            }
        except requests.exceptions.ConnectionError:
            logging.error("Connection error during JWT generation")
            return {
                "status": "failed",
                "error": "Connection error - please check your internet connection"
            }
        except Exception as e:
            logging.error(f"Token generation error: {str(e)}")
            return {
                "status": "failed",
                "error": f"Internal error: {str(e)}"
            }
