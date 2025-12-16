import urllib.parse

password = "oyMDc5NTU4MDg5fQ.NA7UeD2TNGgYfZ4VXkRr7je6tcLJIWgReO7Q5oiVXho"
encoded = urllib.parse.quote(password, safe="")
print(f"Original: {password}")
print(f"Encoded:  {encoded}")
print(f"Are they different? {password != encoded}")

# Build connection strings
user = "postgres.znaauaswqmurwfglantv"
host = "aws-1-eu-central-1.pooler.supabase.com"
port = "5432"
db = "postgres"

url_original = f"postgresql://{user}:{password}@{host}:{port}/{db}"
url_encoded = f"postgresql://{user}:{encoded}@{host}:{port}/{db}"

print(f"\nOriginal URL: {url_original[:80]}...")
print(f"Encoded URL:  {url_encoded[:80]}...")
