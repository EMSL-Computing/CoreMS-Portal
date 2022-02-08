
$(function(){
    
    ftmsSetTabCookies();
    
});

function ftmsSetTabCookies(){
    

    let tab = Cookies.get("tabs_selected");
    let tab_content = Cookies.get("tabs_selected_content");
    // setter, set the active tab stocked
    if (!!tab && !!tab_content) {
        RemoveActive();
        HideAll();
        $(tab).addClass("is-active");
        $(tab_content).removeClass("is-hidden");
        
    }
    else {
        switchToFtmsInput();
    };

}

function RemoveActive() {
    $(".ftms-tabs li").each(function() {
    $(this).removeClass("is-active");
    
    });
}

function switchToFtmsResult() {
    RemoveActive();
    HideAll();
    $("#ftmsresult-tab").addClass("is-active");
    $("#ftmsresult-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected", "#ftmsresult-tab");
    Cookies.set("tabs_selected_content", "#ftmsresult-tab-content");
}

function switchToFtmsData() {
    RemoveActive();
    HideAll();
    $("#ftmsdata-tab").addClass("is-active");
    $("#ftmsdata-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected", "#ftmsdata-tab");
    Cookies.set("tabs_selected_content", "#ftmsdata-tab-content");
}

function switchToFtmsInput() {
    RemoveActive();
    HideAll();
    $("#ftmsinput-tab").addClass("is-active");
    $("#ftmsinput-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected", "#ftmsinput-tab");
    Cookies.set("tabs_selected_content", "#ftmsinput-tab-content");
}

function switchToFtmsProcess() {
    RemoveActive();
    HideAll();
    $("#ftmsprocess-tab").addClass("is-active");
    $("#ftmsprocess-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected", "#ftmsprocess-tab");
    Cookies.set("tabs_selected_content", "#ftmsprocess-tab-content");
}

function switchToFtmsSettings() {
    RemoveActive();
    HideAll();
    $("#ftmsparams-tab").addClass("is-active");
    $("#ftmsparams-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected", "#ftmsparams-tab");
    Cookies.set("tabs_selected_content", "#ftmsparams-tab-content");
}

function HideAll(){
    $("#ftmsinput-tab-content").addClass("is-hidden");
    $("#ftmsparams-tab-content").addClass("is-hidden");
    $("#ftmsprocess-tab-content").addClass("is-hidden");
    $("#ftmsdata-tab-content").addClass("is-hidden");
    $("#ftmsresult-tab-content").addClass("is-hidden");

}
