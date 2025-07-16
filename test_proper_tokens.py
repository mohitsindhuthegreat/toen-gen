#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'attached_assets'))

from jwtgen_1752648765653 import get_token, encrypt_message, parse_response
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
import json
import requests
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warning
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# Add the attached_assets directory to Python path
sys.path.insert(0, 'attached_assets')

# Import the attached protobuf files
import my_pb2_1752648765655 as my_pb2
import output_pb2_1752648765656 as output_pb2

# Constants
AES_KEY = b'Yg&tc%DEuh6%Zc^8'
AES_IV = b'6oyZDr22E3ychjM%'

def generate_proper_token(uid, password):
    """Generate token using proper method"""
    try:
        # Step 1: Get access token
        token_data = get_token(password, uid)
        if not token_data:
            return {
                "status": "failed",
                "error": "Wrong UID or Password"
            }

        # Step 2: Create GameData protobuf
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

        # Step 3: Serialize and encrypt
        serialized_data = game_data.SerializeToString()
        encrypted_data = encrypt_message(AES_KEY, AES_IV, serialized_data)
        edata = binascii.hexlify(encrypted_data).decode()

        # Step 4: Send request
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
            # Step 5: Parse response
            example_msg = output_pb2.Garena_420()
            try:
                example_msg.ParseFromString(response.content)
                response_dict = parse_response(str(example_msg))
                return {
                    "status": "success",
                    "token": response_dict.get("token", "N/A"),
                    "uid": uid
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": f"Failed to parse response: {str(e)}"
                }
        else:
            return {
                "status": "failed",
                "error": f"HTTP {response.status_code}: {response.reason}"
            }

    except Exception as e:
        return {
            "status": "failed",
            "error": f"Internal error: {str(e)}"
        }

def main():
    # Load credentials
    with open('attached_assets/credentials_1752646896705.json', 'r') as f:
        credentials = json.load(f)

    working_tokens = []
    print('Generating tokens with proper method...')

    for i, cred in enumerate(credentials[:10]):  # Test first 10
        try:
            uid = str(cred.get('uid', ''))
            password = str(cred.get('password', ''))
            
            if uid and password:
                print(f'Processing UID: {uid}')
                result = generate_proper_token(uid, password)
                
                if result and result.get('status') == 'success':
                    token = result.get('token')
                    print(f'✓ Token generated successfully for UID: {uid}')
                    working_tokens.append({'token': token})
                else:
                    print(f'✗ Failed for UID: {uid} - {result.get("error", "Unknown error")}')
        except Exception as e:
            print(f'Error with UID {uid}: {e}')

    # Save working tokens to ind.json
    if working_tokens:
        with open('tokens/ind.json', 'w') as f:
            json.dump(working_tokens, f, indent=2)
        print(f'\nSaved {len(working_tokens)} working tokens to ind.json')
        return True
    else:
        print('No working tokens generated!')
        return False

if __name__ == "__main__":
    main()