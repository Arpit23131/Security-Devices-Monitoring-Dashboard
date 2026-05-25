import requests, base64, json, time, datetime, pathlib, urllib3
from pysnmp.hlapi import getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA = pathlib.Path("data_log.jsonl")
DATA.touch(exist_ok=True)

BARRACUDA_SNMP_IP = "Enter_IP_Address"
COMMUNITY = "public"

# Add OIDs to monitor
BARRACUDA_OIDS = {
    "uptime_oid": "Enter-ID",
    "memory_oid": "Enter-ID"
    # Add more OIDs as needed
}

# def fetch_snmp_oid(oid):
#     try:
#         iterator = getCmd(
#             SnmpEngine(),
#             CommunityData(COMMUNITY, mpModel=1),  # mpModel=1 is SNMPv2c
#             UdpTransportTarget((BARRACUDA_SNMP_IP, 161), timeout=2.0, retries=1),
#             ContextData(),
#             ObjectType(ObjectIdentity(oid))
#         )

#         errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

#         if errorIndication:
#             print(f"[SNMP ERROR] {errorIndication}")
#             return None
#         elif errorStatus:
#             print(f"[SNMP ERROR] {errorStatus.prettyPrint()} at {errorIndex}")
#             return None
#         else:
#             for varBind in varBinds:
#                 return str(varBind[1])  # Extract the actual value

#     except Exception as e:
#         print(f"[ERROR] SNMP Fetch Failed for OID {oid}:", e)
#         return None


def get_token():
    login_url = "https://IP-Address/restapi/v3.2/login"
    try:
        r = requests.post(
            login_url,
            json={"username": "Enter-Username", "password": "Enter-Password"},
            verify=False,
            timeout=10
        )
        r.raise_for_status()
        return r.json()["token"]
    except Exception as e:
        print("[ERROR] Failed to get token:", e)
        return None

def get_auth_header(token):
    return {"Authorization": "Basic " + base64.b64encode(f"{token}:".encode()).decode()}

# Get initial token
token = get_token()
auth = get_auth_header(token)

while True:
    try:
        # ========= SYSTEM TELEMETRY LOGIC =========
        res = requests.get(
            "https://IP-Address/restapi/v3.2/system",
            headers=auth,
            verify=False,
            timeout=10
        )

        try:
            res_json = res.json()
        except Exception:
            print("[ERROR] Non-JSON response (system):", res.text)
            time.sleep(60)
            continue

        if res.status_code == 401 or "data" not in res_json:
            print("[INFO] Token expired for system endpoint. Reauthenticating...")
            token = get_token()
            if not token:
                time.sleep(60)
                continue
            auth = get_auth_header(token)
            continue

        if ("data" in res_json and
            "System" in res_json["data"] and
            "telemetry-name" in res_json["data"]["System"]):

            r = res_json["data"]["System"]["telemetry-name"]

            record = {
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                "req": int(r.get("total_requests", {}).get("Value", 0)),
                "upt": int(r.get("upt", {}).get("Value", 0)),
                "memGB": round(int(r.get("mem", {}).get("Value", 0)) / (1024 * 1024), 2),
                "crashes": int(r.get("num_crashes", {}).get("Value", 0))
            }

            record["type"] = "system"
            with DATA.open("a") as f:
                f.write(json.dumps(record) + "\n")

            print("[OK] System Logged:", record)

        else:
            print("[WARN] Unexpected system structure:", json.dumps(res_json, indent=2))

        # ========= SERVICE STATUS LOGIC =========
        res2 = requests.get(
            "https://IP-Address/restapi/v3.2/services",
            headers=auth,
            verify=False,
            timeout=10
        )

        try:
            res_json2 = res2.json()
        except Exception:
            print("[ERROR] Non-JSON response (service):", res2.text)
            time.sleep(60)
            continue

        if res2.status_code == 401 or "data" not in res_json2:
            print("[INFO] Token expired for service endpoint. Reauthenticating...")
            token = get_token()
            if not token:
                time.sleep(60)
                continue
            auth = get_auth_header(token)
            continue

        services_data = res_json2.get("data", {})
        for service_name, service_content in services_data.items():
            servers = service_content.get("Server", {}).get("data", {})
            for server_id, info in servers.items():
                ip = info.get("ip-address", "N/A")
                status = info.get("status", "Unknown")

                service_record = {
                    "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                    "service": service_name,
                    "server": server_id,
                    "ip": ip,
                    "status": status
                }

                service_record["type"] = "service"
                with DATA.open("a") as f:
                    f.write(json.dumps(service_record) + "\n")

                print("[OK] Service Logged:", service_record)

        # ========= BARRACUDA SNMP OID FETCH =========
        # snmp_record = {
        #     "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        #     "type": "snmp"
        # }

        # for label, oid in BARRACUDA_OIDS.items():
        #     value = fetch_snmp_oid(oid)
        #     if value is not None:
        #         snmp_record[label] = value

        # with DATA.open("a") as f:
        #     f.write(json.dumps(snmp_record) + "\n")

        # print("[OK] SNMP Data Logged:", snmp_record)

        time.sleep(600)  # 5 minutes

    except Exception as e:
        print("[ERROR]", e)
        time.sleep(60)


#py -3.11 -m pip install pysnmp
#py -3.11 log_API_OID.py