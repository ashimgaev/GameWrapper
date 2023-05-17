
function doGet(uri) {
    var req = new XMLHttpRequest();
    req.open("GET", uri, false);
    req.send();
    return JSON.parse(req.responseText);
}

function doPost(uri, jData) {
    var req = new XMLHttpRequest();
    req.open("POST", uri, false);
    req.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    var data = JSON.stringify(jData);
    req.send(data);
    return JSON.parse(req.responseText);
}


class MasterService {
    constructor(address) {
        this.address = address
        this.configUrl = this.address + "config";
        this.statusUrl = this.address + "status";
    }

    setMasterStatus(is_active) {
        return doPost(this.statusUrl, { "is_active": is_active });
    }

    getMasterStatus() {
        return doGet(this.statusUrl);
    }

    getAllConfigs() {
        return doGet(this.configUrl);
    }

    updateConfigs(jSections) {
        return doPost(this.configUrl, { "sections": jSections });
    }
}