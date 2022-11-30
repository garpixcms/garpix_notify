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

function firstLoad(sms, call) {
    smsParser(parseInt(sms.value));
    callParser(parseInt(call.value));
}

window.onload = function(){
    let sms_url = document.querySelector('#id_sms_url_type');
    let call_url = document.querySelector('#id_call_url_type');
    firstLoad(sms_url, call_url)

    sms_url.addEventListener('change', (event_sms) => {
        smsParser(parseInt(event_sms.currentTarget.value));
    })
    call_url.addEventListener('change', (event_call) => {
        callParser(parseInt(event_call.currentTarget.value));
    })
}
