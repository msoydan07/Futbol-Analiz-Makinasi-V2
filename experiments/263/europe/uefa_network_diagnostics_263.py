"""One-shot bounded UEFA transport diagnostics for Actions runners only.
Does not authenticate, scrape fixtures, run predictions or bypass access control.
"""
import json,socket,ssl,time,urllib.request
from urllib.parse import urlsplit

TESTS=[
 ("github_control","https://raw.githubusercontent.com/openfootball/champions-league/abfaeddc2ee3d14f99ecc163c9ddb46cb4d67cef/2025-26/cl.txt"),
 ("uefa_article","https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-champions-league-all-the-league-phase-fixtures/"),
 ("uefa_root","https://www.uefa.com/"),
 ("uefa_docs","https://documents.uefa.com/"),
 ("uefa_editorial","https://editorial.uefa.com/"),
]
def run():
    entries=[]
    for name,url in TESTS:
        host=urlsplit(url).hostname;record={"name":name,"host":host}
        t=time.monotonic()
        try:
            ips=sorted({a[4][0] for a in socket.getaddrinfo(host,443,socket.AF_INET,socket.SOCK_STREAM)})
            record["dns_ipv4"]=ips[:3]
            record["dns_status"]="resolved"
        except Exception as ex:
            record["dns_status"]=type(ex).__name__
            record["dns_ipv4"]=[]
        record["dns_elapsed_sec"]=round(time.monotonic()-t,2)
        # TLS stream fetch: capped bytes, bounded seconds; never assume a 200 proves content correctness
        t=time.monotonic()
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0",
                      "Accept":"text/html, text/plain, */*"})
            with urllib.request.urlopen(req,timeout=5) as res:
                record["http_status"]=res.status
                record["content_type"]=res.headers.get("Content-Type")
                record["bytes_prefix"]=len(res.read(64))
                record["redirect_host"]=urlsplit(res.geturl()).hostname
                record["request_status"]="reachable"
        except Exception as ex:
            record["request_status"]=type(ex).__name__
            record["error_excerpt"]=str(ex)[:220]
        record["request_elapsed_sec"]=round(time.monotonic()-t,2)
        entries.append(record)
    print("UEFA_TRANSPORT_DIAGNOSTICS="+json.dumps({"scope":"NETWORK_ONLY_NO_FIXTURE_VERIFICATION","entries":entries},sort_keys=True))
if __name__=="__main__":run()
