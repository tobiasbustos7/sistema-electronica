from app import create_app
app = create_app()
c = app.test_client()
c.post('/auth/login', data={'username':'admin','password':'admin123'})
pages = [
    '/', '/productos/', '/proveedores/', '/compras/',
    '/ventas/clientes', '/inventario/', '/caja/',
    '/usuarios/', '/historial/', '/configuracion/', '/reportes/'
]
ok = 0
fl = 0
for p in pages:
    r = c.get(p)
    if r.status_code == 200:
        ok += 1
        status = 'OK'
    else:
        fl += 1
        status = 'FAIL'
    print(f'{status}: {p} ({r.status_code})')
print(f'\nTotal: {ok} OK, {fl} FAIL')
