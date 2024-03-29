
function doGet(uri) {
    var req = new XMLHttpRequest();
    req.open("GET", uri, false);
    try {
        req.send();
        return JSON.parse(req.responseText);
    } catch (err) {
        throw new Error();
    }
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
        this.configSyncUrl = this.address + "config/sync";
        this.statusUrl = this.address + "status";
        this.logsUrl = this.address + "logs";
        this.statisticUrl = this.address + "statistic";
        this.masterRoleUrl = this.address + "master-role";
        this.sendMessageUrl = this.address + "send-message";
        this.slaveShutDownUrl = this.address + "slave-shutdown";
    }

    getLogs() {
        try {
            return doGet(this.logsUrl);
        } catch (err) {
            throw new Error();
        }
    }

    sendMessage(msg) {
        return doGet(this.sendMessageUrl + "?msg=" + msg);
    }

    sendSlaveShutdown(name) {
        return doGet(this.slaveShutDownUrl + "?name=" + name);
    }

    getStatistic() {
        return doGet(this.statisticUrl);
    }

    getMasterRole() {
        return doGet(this.masterRoleUrl);
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

    syncConfig() {
        return doGet(this.configSyncUrl);
    }

    updateConfigs(jSections) {
        return doPost(this.configUrl, { "sections": jSections });
    }
}