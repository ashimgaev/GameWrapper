
function initMasterAddressFromCookies() {
    let docCookie = document.cookie
    let list = docCookie.split(";")
    for (i = 0; i < list.length; i++) {
        name_val_pair = list[i].split("=")
        let name = name_val_pair[0].trim()
        if (name == "master_host") {
            return name_val_pair[1].trim()
        }
    }
    return "127.0.0.1:8005"
}

var MASTER_SERVICE_ADDRESS = initMasterAddressFromCookies();
var MASTER_SERVICE_HOST = "http://" + MASTER_SERVICE_ADDRESS + "/master/";