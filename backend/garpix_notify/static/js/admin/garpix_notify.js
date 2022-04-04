window.onload = function(){
    let sms_url = document.querySelector('#id_sms_url_type');

    if (parseInt(sms_url.value) == 0) {
        document.querySelector('.field-sms_login').classList.add('admin-none');
        document.querySelector('.field-sms_password').classList.add('admin-none');
    }
    else {
        document.querySelector('.field-sms_api_id').classList.add('admin-none');
    }

    sms_url.addEventListener('change', (event) => {
        if (parseInt(event.currentTarget.value) === 0){
            document.querySelector('.field-sms_api_id').classList.remove('admin-none');
            document.querySelector('.field-sms_login').classList.add('admin-none');
            document.querySelector('.field-sms_password').classList.add('admin-none');
        }
        else {
            document.querySelector('.field-sms_login').classList.remove('admin-none');
            document.querySelector('.field-sms_password').classList.remove('admin-none');
            document.querySelector('.field-sms_api_id').classList.add('admin-none');
        }
    });
}