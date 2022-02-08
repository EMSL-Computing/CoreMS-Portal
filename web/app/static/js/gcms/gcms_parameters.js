$(function(){
    
    DeleteGcmsPreset();
    AddGcmsPreset();
    GcmsSetSettingsTabCookies();
    
    $( "#gcmsPreset").submit(function( event ) {
        
        event.preventDefault();
    });
        
});

function GcmsSetSettingsTabCookies(params) {
    
    let gcms_settings_tab = Cookies.get("tabs_selected_gcms_settings");
    let gcms_settings_tab_content = Cookies.get("tabs_selected_gcms_settings_content");
    // setter, set the active tab stocked
    if (!!gcms_settings_tab && !!gcms_settings_tab_content) {
        RemoveActiveGcmsSettings();
        hideAllGcmsSettings();
        $(gcms_settings_tab).addClass("is-active");
        $(gcms_settings_tab_content).removeClass("is-hidden");
        
    }
    else {
        switchToFtmsPreset();
    };
}

function AddGcmsPreset() {
    
    $( "#add_gcms_preset").click(function(e) {
        
        e.preventDefault();
        
        let new_preset_name = $( "#new_gcms_preset_name" ).val();  
        
        if (new_preset_name == ""){
            alert("Please give the new preset a name");
            return
        }
        
        let all_form_data = {
                'name': new_preset_name,
                'molsearch': objectifyForm($('#gcmsmolecularsearchsettings').serializeArray()),
                'peakdetection': objectifyForm($('#gcmspeakdetectionsettings').serializeArray())
               
        }

        $.ajax({
            
            type : 'POST',
            url : '/gcms/parameters/add-preset',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(all_form_data),
            
        }).done(function(data) {
            

            $('#gcms_presets').append($('<option>').val(data.id).text(new_preset_name))
            $('select[name="gcms_presets"]').find('option[value="' + data.id + '"]').attr("selected",true);
            
            $('#gcmspresetsubmmit').append($('<option>').val(data.id).text(new_preset_name))
            $('select[id="gcmspresetsubmmit"]').find('option[value="' + data.id + '"]').attr("selected",true);
            

        }).fail(function(data) {
            //switchToGcmsProcess();
            alert(data.responseText);
            
        });

        e.preventDefault();
    
    });
}

function DeleteGcmsPreset() {
    
    $( "#delete_gcms_preset").click(function(e) {
        
        e.preventDefault();
        
        let current_preset_id = $( "#gcms_presets" ).val();
        
        if ( $( "#gcms_presets" ).text() == 'default'){
            alert("Cannot delete the default preset");
            return
        }

        $.ajax({
            
            type : 'PUT',
            url : '/gcms/parameters/remove-preset/'+ current_preset_id,
            dataType: 'json',
            contentType: 'application/json',
            
            
        }).done(function(data) {
            
            $("#gcms_presets option[value="+current_preset_id+"]").remove();
            $("#gcmspresetsubmmit option[value="+current_preset_id+"]").remove();
            
            let new_preset_id = $( "#gcms_presets" ).val();
            updateAllGcmsFormData(new_preset_id);

        }).fail(function(data) {
            //switchToGcmsProcess();
            alert(data.responseText);
            
        });

        e.preventDefault();
    
    });
}

function UpdateGcmsFormData(formType){

        let formData = new FormData($("#"+formType)[0]);
        
        let present_id = $( "#gcms_presets" ).val(); 

        $.ajax({
            
            type : 'POST',
            url : '/gcms/update-parameters/' + formType + '/' + present_id,
            data : formData,
            processData : false,
            contentType : false,
            
            
        }).done(function(data) {
            
            //TODO: reload data table and process list to avoid reload
            // call to update on load
            
            alert(data.done);
            console.log(formType);
            if (formType == "submitBasic"){
                switchToGcmsProcess();
            };

        }).fail(function(data) {
            //switchToGcmsProcess();
            alert(data.responseText);
            
        });


}

function UpdateAllGcmsFormData(id) {
    
    $.getJSON( "/gcms/parameters/all/" + id , function() {
        console.log( "success" );
        }).done(function(json_result) {
            
            $("#gcmsmolecularsearchsettings").html(json_result.molsearch);
            $("#gcmspeakdetectionsettings").html(json_result.peakdetection);
            alert(json_result.done);

        }).fail(function() {
            alert(data.responseText);

        }).always(function() {
            
            console.log( "complete" );
        });
        // more here    
}

// FTMS Settings Tabs 
function objectifyForm(formArray) {//serialize array data function
    var data = {};

    $(formArray ).each(function(index, obj){

        if(data[obj.name] === undefined)
             data[obj.name] = [];

         data[obj.name].push(obj.value);

    });

    return data
    
    // var returnArray = {};
    // for (var i = 0; i < formArray.length; i++){
    //  returnArray[formArray[i]['name']] = formArray[i]['value'];
    //}
    // return returnArray;
}


function switchToGcmsPreset() {
    RemoveActiveGcmsSettings();
    hideAllGcmsSettings();
    $("#gcmspreset-tab").addClass("is-active");
    $("#gcmspreset-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_gcms_settings", "#gcmspreset-tab");
    Cookies.set("tabs_selected_gcms_settings_content", "#gcmspreset-tab-content");
    
}

function switchToGcmsMolSearch() {
    RemoveActiveGcmsSettings();
    hideAllGcmsSettings();
    $("#gcmsmolsearch-tab").addClass("is-active");
    $("#gcmsmolsearch-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_gcms_settings", "#gcmsmolsearch-tab");
    Cookies.set("tabs_selected_gcms_settings_content", "#gcmsmolsearch-tab-content");
    
}

function switchToGcmsPeakDetection() {
    RemoveActiveGcmsSettings();
    hideAllGcmsSettings();
    $("#gcmspeakdetection-tab").addClass("is-active");
    $("#gcmspeakdetection-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_gcms_settings", "#gcmspeakdetection-tab");
    Cookies.set("tabs_selected_gcms_settings_content", "#gcmspeakdetection-tab-content");
    
}


function RemoveActiveGcmsSettings() {
    $(".gcms-param_nav li a").each(function() {
    $(this).removeClass("is-active");
    });
}

function hideAllGcmsSettings(){
    $("#gcmspreset-tab-content").addClass("is-hidden");
    $("#gcmsmolsearch-tab-content").addClass("is-hidden");
    $("#gcmspeakdetection-tab-content").addClass("is-hidden");

}