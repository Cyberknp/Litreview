from opensearchpy import OpenSearch 

client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    use_ssl=False,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
)

INDEX_NAME = "research-papers"  # Replace with your index name

def check_connections():
    return client.info()

if __name__=="__main__":
    print(check_connections())
    