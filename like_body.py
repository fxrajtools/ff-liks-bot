# like_body.py
import requests
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from google.protobuf.json_format import ParseDict, MessageToDict

from ff_proto import MajorLogin_pb2

try:
    from ff_proto.send_like_pb2 import like as LikeProfileReq
    SEND_LIKE_AVAILABLE = True
except ImportError:
    SEND_LIKE_AVAILABLE = False
    LikeProfileReq = None
    print("⚠️ send_like_pb2.py nahi mili — likes nahi jayenge")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MAIN_KEY = b'Yg&tc%DEuh6%Zc^8'
MAIN_IV = b'6oyZDr22E3ychjM%'
RELEASEVERSION = "OB54"


def aes_encrypt(plaintext: bytes) -> bytes:
    cipher = AES.new(MAIN_KEY, AES.MODE_CBC, MAIN_IV)
    return cipher.encrypt(pad(plaintext, AES.block_size))


def aes_decrypt(ciphertext: bytes) -> bytes:
    cipher = AES.new(MAIN_KEY, AES.MODE_CBC, MAIN_IV)
    return unpad(cipher.decrypt(ciphertext), AES.block_size)


def get_garena_token(uid, password):
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
    payload = {
        'uid': uid,
        'password': password,
        'response_type': "token",
        'client_type': "2",
        'client_secret': "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        'client_id': "100067"
    }
    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(A063 ;Android 13;en;IN;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }
    try:
        r = requests.post(url, data=payload, headers=headers, verify=False, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Token error: {e}")
        return None


def major_login(access_token, open_id):
    try:
        payload_dict = {
            "openid": open_id,
            "logintoken": access_token,
            "platform": "4",
        }
        proto = MajorLogin_pb2.request()
        ParseDict(payload_dict, proto, ignore_unknown_fields=True)
        encrypted = aes_encrypt(proto.SerializeToString())

        url = "https://loginbp.ggpolarbear.com/MajorLogin"
        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 13; A063 Build/TKQ1.221220.001)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Expect': "100-continue",
            'Authorization': "Bearer",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': RELEASEVERSION,
            'Content-Type': "application/octet-stream"
        }
        r = requests.post(url, data=encrypted, headers=headers, verify=False, timeout=10)

        resp = MajorLogin_pb2.response()
        try:
            decrypted = aes_decrypt(r.content)
            resp.ParseFromString(decrypted)
        except Exception:
            resp.ParseFromString(r.content)

        return MessageToDict(resp, preserving_proto_field_name=True)
    except Exception as e:
        print(f"MajorLogin error: {e}")
        return None


def create_like_payload(uid: int, region: str) -> bytes:
    if not SEND_LIKE_AVAILABLE:
        raise Exception("send_like_pb2.py nahi mili")

    request = LikeProfileReq()
    request.uid = uid
    request.region = region

    return aes_encrypt(request.SerializeToString())


def send_like(guest_uid, guest_pass, target_uid, region):
    if not SEND_LIKE_AVAILABLE:
        print("❌ send_like_pb2.py missing")
        return False

    try:
        token_data = get_garena_token(guest_uid, guest_pass)
        if not token_data or "access_token" not in token_data:
            return False

        access_token = token_data["access_token"]
        open_id = token_data["open_id"]

        login_data = major_login(access_token, open_id)
        if not login_data or "token" not in login_data:
            return False

        game_token = login_data["token"]
        server_url = login_data["serverUrl"]

        encrypted_payload = create_like_payload(int(target_uid), region)

        url = f"{server_url}/LikeProfile"
        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 13; A063 Build/TKQ1.221220.001)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Authorization': f"Bearer {game_token}",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': RELEASEVERSION,
            'Content-Type': "application/octet-stream"
        }
        r = requests.post(url, data=encrypted_payload, headers=headers, verify=False, timeout=10)

        return r.status_code == 200

    except Exception as e:
        print(f"send_like error: {e}")
        return False