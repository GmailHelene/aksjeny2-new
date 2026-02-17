from app import create_app

def test_technical_tsla():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Attempt to access technical analysis; if access control redirects to login, note it.
        resp = client.get('/analysis/technical?symbol=TSLA', follow_redirects=True)
        text = resp.get_data(as_text=True)
        print('Status', resp.status_code)
        is_login_page = 'name="email"' in text and 'Logg inn' in text
        print('Redirected to login:', is_login_page)
        if not is_login_page:
            print('Contains TSLA:', 'TSLA' in text)
            duplicate_form_present = 'technicalSearchForm' in text
            print('Duplicate legacy form present:', duplicate_form_present)
            idx = text.find('ticker-input')
            if idx != -1:
                print('...snippet...', text[max(0, idx-80): idx+120])
        else:
            print('Access control prevented analysis rendering (login required).')

if __name__ == '__main__':
    test_technical_tsla()
