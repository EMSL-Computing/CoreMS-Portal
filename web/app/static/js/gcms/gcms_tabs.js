
$(function(){
    
    gcmsSetTabCookies();

    
});

function gcmsSetTabCookies(){
    //var gcms_tab = Cookies.get("tabs_selected_gcms");
    //var gcms_tab_content = Cookies.get("tabs_selected_gcms_content");
    // setter, set the active tab stocked
    
    //if (!!gcms_tab && !!gcms_tab_content) {
        //RemoveActiveGcmsSettings();
        //hideAllGcmsSettings();
    //    $(gcms_tab).addClass("is-active");
    //    $(gcms_tab_content).removeClass("is-hidden");
    //  };

    let gcms_tab = Cookies.get("tabs_selected_gcms");
    let gcms_tab_content = Cookies.get("tabs_selected_gcms_content");
    // setter, set the active tab stocked
    if (!!gcms_tab && !!gcms_tab_content) {
        RemoveGcmsActive();
        HideGcmsAll();
        $(gcms_tab).addClass("is-active");
        $(gcms_tab_content).removeClass("is-hidden");
       
    }
    else {
        switchToGcmsInput();
    };

}


function switchToGcmsInput() {
    RemoveGcmsActive();
    HideGcmsAll();
    $("#gcmsinput-tab").addClass("is-active");
    $("#gcmsinput-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_gcms", "#gcmsinput-tab");
    Cookies.set("tabs_selected_gcms_content", "#gcmsinput-tab-content");
}

function switchToGcmsData() {
    RemoveGcmsActive();
    HideGcmsAll();
    $("#gcmsdata-tab").addClass("is-active");
    $("#gcmsdata-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_gcms", "#gcmsdata-tab");
    Cookies.set("tabs_selected_gcms_content", "#gcmsdata-tab-content");
}

function switchToGcmsSettings() {
    RemoveGcmsActive();
    HideGcmsAll();
    $("#gcmsparams-tab").addClass("is-active");
    $("#gcmsparams-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_gcms", "#gcmsparams-tab");
    Cookies.set("tabs_selected_gcms_content", "#gcmsparams-tab-content");
}

function switchToGcmsProcess() {
    RemoveGcmsActive();
    HideGcmsAll();
    $("#gcmsprocess-tab").addClass("is-active");
    $("#gcmsprocess-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_gcms", "#gcmsprocess-tab");
    Cookies.set("tabs_selected_gcms_content", "#gcmsprocess-tab-content");
}

function switchToGcmsResult() {
    RemoveGcmsActive();
    HideGcmsAll();
    $("#gcmsresult-tab").addClass("is-active");
    $("#gcmsresult-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_gcms", "#gcmsresult-tab");
    Cookies.set("tabs_selected_gcms_content", "#gcmsresult-tab-content");
}

function RemoveGcmsActive() {
    $(".gcms-tabs li").each(function() {
    $(this).removeClass("is-active");
    
    });
}

function HideGcmsAll(){
    $("#gcmsinput-tab-content").addClass("is-hidden");
    $("#gcmsdata-tab-content").addClass("is-hidden");
    $("#gcmsparams-tab-content").addClass("is-hidden");
    $("#gcmsprocess-tab-content").addClass("is-hidden");
    $("#gcmsresult-tab-content").addClass("is-hidden");

}