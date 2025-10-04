from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(find_dotenv())
cs = os.getenv("EVENTHUB_CONNECTION_STRING") or ""
print("RAW:", repr(cs))
parts = {}
for kv in cs.split(";"):
    if "=" in kv:
        k, v = kv.split("=", 1); parts[k.strip()] = v.strip()
print("Endpoint:", parts.get("Endpoint"))
print("EntityPath:", parts.get("EntityPath"))
print("OK?", parts.get("Endpoint","").startswith("sb://")
            and parts.get("Endpoint","").endswith("/")
            and bool(parts.get("EntityPath")))

