from app import create_app

app = create_app('testing')
client = app.test_client()

print('GET /insider-trading ...', end=' ')
resp = client.get('/insider-trading')
print(resp.status_code)

print('GET /insider-trading/api/latest ...', end=' ')
resp2 = client.get('/insider-trading/api/latest?limit=5')
print(resp2.status_code)
try:
    print(resp2.get_json())
except Exception as e:
    print('JSON parse error:', e)
