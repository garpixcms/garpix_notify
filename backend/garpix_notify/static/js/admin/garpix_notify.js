function smsParser(value) {
    // Парсер СМС

    switch (value) {
        case 0:
            document.querySelector('.field-sms_api_id').classList.remove('admin-none');
            document.querySelector('.field-sms_from').classList.remove('admin-none');
            document.querySelector('.field-sms_login').classList.add('admin-none');
            document.querySelector('.field-sms_password').classList.add('admin-none');
            break;
        case 1:
            document.querySelector('.field-sms_api_id').classList.add('admin-none');
            document.querySelector('.field-sms_from').classList.remove('admin-none');
            document.querySelector('.field-sms_login').classList.remove('admin-none');
            document.querySelector('.field-sms_password').classList.remove('admin-none');
            break;
        case 3:
            document.querySelector('.field-sms_api_id').classList.add('admin-none');
            document.querySelector('.field-sms_from').classList.remove('admin-none');
            document.querySelector('.field-sms_login').classList.remove('admin-none');
            document.querySelector('.field-sms_password').classList.remove('admin-none');
            break;
        case 6:
            document.querySelector('.field-sms_api_id').classList.remove('admin-none');
            document.querySelector('.field-sms_from').classList.remove('admin-none');
            document.querySelector('.field-sms_login').classList.add('admin-none');
            document.querySelector('.field-sms_password').classList.add('admin-none');
            break;
        default:
            document.querySelector('.field-sms_login').classList.remove('admin-none');
            document.querySelector('.field-sms_password').classList.remove('admin-none');
            document.querySelector('.field-sms_api_id').classList.add('admin-none');
            document.querySelector('.field-sms_from').classList.add('admin-none');
    }
}

function callParser(value) {
    // Парсер для Звонков
    switch (value) {
        case 0:
            document.querySelector('.field-call_api_id').classList.remove('admin-none');
            document.querySelector('.field-call_login').classList.add('admin-none');
            document.querySelector('.field-call_password').classList.add('admin-none');
            break;
        default:
            document.querySelector('.field-call_login').classList.remove('admin-none');
            document.querySelector('.field-call_password').classList.remove('admin-none');
            document.querySelector('.field-call_api_id').classList.add('admin-none');
    }
}

function htmlFormParser(value) {
    // Парсер для способа формирования html
    switch (value) {
        case 'ckeditor':
            document.querySelector('.field-html').classList.remove('admin-none');
            document.querySelector('.field-zipfile').classList.add('admin-none');
            break;
        default:
            document.querySelector('.field-html').classList.add('admin-none');
            document.querySelector('.field-zipfile').classList.remove('admin-none');
    }
}

window.onload = function(){
    let sms_url = document.querySelector('#id_sms_url_type');
    let call_url = document.querySelector('#id_call_url_type');
    let html_from_type = document.querySelector('#id_html_from_type');

    if (sms_url)
        smsParser(parseInt(sms_url.value));
        sms_url?.addEventListener('change', (event_sms) => {
            smsParser(parseInt(event_sms.currentTarget.value));
        })
    if (call_url)
        callParser(parseInt(call_url.value));
        call_url?.addEventListener('change', (event_sms) => {
            callParser(parseInt(event_sms.currentTarget.value));
        })
    if (html_from_type)
        htmlFormParser(html_from_type.value);
        html_from_type?.addEventListener('change', (event) => {
            htmlFormParser(event.currentTarget.value);
        })
}
