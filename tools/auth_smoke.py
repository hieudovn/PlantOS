import httpx
BASE='http://127.0.0.1:8011'
r = httpx.post(f'{BASE}/api/auth/login', json={'username':'admin','password':'Test@1234'})
print('LOGIN:', r.status_code)
c = dict(r.cookies)
csrf = c.get('plantos_csrf','')
print('CSRF:', 'YES' if csrf else 'NO')
r2 = httpx.get(f'{BASE}/api/config', cookies=c)
print('CONFIG:', r2.status_code, 'REDACTED' if 'REDACTED' in r2.text else 'NOT')
r3 = httpx.get(f'{BASE}/api/config')
print('NO AUTH:', r3.status_code)
r4 = httpx.post(f'{BASE}/api/auth/logout', cookies=c, headers={'X-CSRF-Token': csrf})
print('LOGOUT:', r4.status_code)
r5 = httpx.get(f'{BASE}/api/config', cookies=c)
print('AFTER:', r5.status_code, '(expected 401)')
ok = r.status_code==200 and r2.status_code==200 and r3.status_code==401 and r4.status_code==200 and r5.status_code==401
print('AUTH SMOKE:', 'PASS' if ok else 'FAIL')
