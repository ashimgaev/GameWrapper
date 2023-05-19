
var masterHostInputElement;

var mastertStatusElement;

var configTable;
var masterService;
var configModel;
var masterStatusModel;
var healthStatusDivElement;
var healthStatuslabelElement;
var loggerElement;

var HealthStatus;


function StartMain() {
    masterHostInputElement = document.getElementById("MasterServiceHostInputId");
    initMasterAddressFromCookies()
    masterHostInputElement.value = MASTER_SERVICE_ADDRESS
    storeMasterAddressInCookies()
    masterService = new MasterService(MASTER_SERVICE_HOST)

    mastertStatusElement = document.getElementById("MasterStatusId");
    healthStatusDivElement = document.getElementById("HealthStatusDivId");
    healthStatuslabelElement = document.getElementById("HealthStatusLabelId");
    loggerElement = document.getElementById("LoggerInputId");

    configTable = new ConfigTable()

    updateConfigView()

    startPingTimer()
}

function startPingTimer() {
    setTimeout(
        () => {
            try {
                logsModel = masterService.getLogs();
                if (HealthStatus == false) {
                    healthStatusDivElement.className = "StatusDivGood";
                    healthStatuslabelElement.innerHTML = "Good!"
                    HealthStatus = true
                    startReloadPageTimer(500)
                }
                // Update logger
                var str = "";
                for (var i = 0; i < logsModel.logs.length; i++) {
                    str = str + logsModel.logs[i] + "\n";
                }
                loggerElement.value = str;
            } catch (err) {
                healthStatusDivElement.className = "StatusDivBad";
                healthStatuslabelElement.innerHTML = "Bad!"
                HealthStatus = false
            }
            startPingTimer()
        },
        1 * 1000
    );
}

function startReloadPageTimer(ms) {
    setTimeout(
        () => {
            updateConfigView()
        },
        ms
    );
}

function storeMasterAddressInCookies() {
    let host = "master_host=" + masterHostInputElement.value + ";" + "expires=Thu, 18 Dec 2050 12:00:00 UTC"
    document.cookie = host
}

function onHostApplyClick() {
    storeMasterAddressInCookies()
    // Reload screen
}


function onMasterStatusClick() {
    masterService.setMasterStatus(mastertStatusElement.checked)
}

function ConfigTable() {
    this.table = document.getElementById("ConfigTableId");

    this.buildConfigGroup = function (cfgSection) {
        var groupElement = document.createElement("fieldset");

        let sectionName = cfgSection.name;
        let pwdInputElement;
        let allowedInputElement;
        
        {
            let el = document.createElement("legend");
            el.innerHTML = cfgSection.name
            groupElement.appendChild(el)
        }

        {
            let el = document.createElement("label");
            el.innerHTML = 'password: '
            groupElement.appendChild(el)
        }
        {
            let el = document.createElement("input");
            el.type = "text"
            el.value = cfgSection.pwd
            pwdInputElement = el
            groupElement.appendChild(el)
        }

        groupElement.appendChild(document.createElement("br"))

        {
            let el = document.createElement("label");
            el.innerHTML = 'allowed: '
            groupElement.appendChild(el)
        }
        {
            let el = document.createElement("input");
            el.type = "checkbox"
            el.checked = cfgSection.allowed
            allowedInputElement = el
            el.onclick = function () {
                masterService.updateConfigs([{ 'name': sectionName, 'pwd': pwdInputElement.value, 'allowed': allowedInputElement.checked }])
            }
            groupElement.appendChild(el)
        }

        groupElement.appendChild(document.createElement("br"))

        {
            let el = document.createElement("button");
            el.innerHTML = 'update: '
            el.onclick = function () {
                masterService.updateConfigs([{ 'name': sectionName, 'pwd': pwdInputElement.value, 'allowed': allowedInputElement.checked } ])
            }
            groupElement.appendChild(el)
        }

        return groupElement;
    }

    this.buildTable = function (cfgModel, masterStatus) {
        this.clear();
        for (var i = 0; i < cfgModel.sections.length; i++) {
            let groupElement = this.buildConfigGroup(cfgModel.sections[i]);
            this.table.appendChild(groupElement)
        }
        mastertStatusElement.checked = masterStatus.is_active
    }

    this.clear = function () {
        this.table.innerHTML = "";
    }
}

function updateConfigView() {
    masterStatusModel = masterService.getMasterStatus()
    configModel = masterService.getAllConfigs()
    configTable.buildTable(configModel, masterStatusModel)
}

function onSyncConfigClick() {
    masterService.syncConfig()
    startReloadPageTimer(2000)
}