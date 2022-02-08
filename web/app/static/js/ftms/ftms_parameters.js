$(function(){
    
    DeleteFtmsPreset();
    AddFtmsPreset();
    FtmsSetSettingsTabCookies();
    
    $( "#ftmsPreset").submit(function( event ) {
        
        event.preventDefault();
    });
    
    
});

function FtmsSetSettingsTabCookies() {
    
    let ftms_settings_tab = Cookies.get("tabs_selected_ftms");
    let ftms_settings_tab_content = Cookies.get("tabs_selected_ftms_content");
    // setter, set the active tab stocked
    if (!!ftms_settings_tab && !!ftms_settings_tab_content) {
        RemoveActiveFtmsSettings();
        hideAllFtmsSettings();
        
        $(ftms_settings_tab).addClass("is-active");
        $(ftms_settings_tab_content).removeClass("is-hidden");
        
    }
    else {
        switchToFtmsPreset();
    };
}

function AddFtmsPreset() {
    
    $( "#add_ftms_preset").click(function(e) {
        
        e.preventDefault();
        
        let new_preset_name = $( "#new_preset_name" ).val();  
        
        if (new_preset_name == ""){
            alert("Please give the new preset a name");
            return
        }
        
        let all_form_data = {
                'name': new_preset_name,
                'basic': objectifyForm($('#ftmsbasicsettings').serializeArray()),
                'input': objectifyForm($('#ftmsinputdatasettings').serializeArray()),
                'advanced': objectifyForm($('#ftmsadvancedsettings').serializeArray()),
                'ms': objectifyForm($('#ftmssettings').serializeArray()),
                'mspeak': objectifyForm($('#ftmspeaksettings').serializeArray()),
                'transient': objectifyForm($('#ftmstransietsettings').serializeArray())
        }

        $.ajax({
            
            type : 'POST',
            url : '/ftms/parameters/add-preset',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify(all_form_data),
            
        }).done(function(data) {
            

            $('#ftms_presets').append($('<option>').val(data.id).text(new_preset_name))
            $('select[name="ftms_presets"]').find('option[value="' + data.id + '"]').attr("selected",true);
            
            $('#ftmspresetsubmmit').append($('<option>').val(data.id).text(new_preset_name))
            $('select[id="ftmspresetsubmmit"]').find('option[value="' + data.id + '"]').attr("selected",true);
            

        }).fail(function(data) {
            //switchToFtmsProcess();
            alert(data.responseText);
            
        });

        e.preventDefault();
    
    });
}

function DeleteFtmsPreset() {
    
    $( "#delete_ftms_preset").click(function(e) {
        
        e.preventDefault();
        
        let current_preset_id = $( "#ftms_presets" ).val();
        
        if ( $( "#ftms_presets" ).text() == 'default'){
            alert("Cannot delete the default preset");
            return
        }

        $.ajax({
            
            type : 'PUT',
            url : '/ftms/parameters/remove-preset/'+ current_preset_id,
            dataType: 'json',
            contentType: 'application/json',
            
            
        }).done(function(data) {
            
            $("#ftms_presets option[value="+current_preset_id+"]").remove();
            $("#ftmspresetsubmmit option[value="+current_preset_id+"]").remove();
            
            let new_preset_id = $( "#ftms_presets" ).val();
            updateAllFtmsFormData(new_preset_id);

        }).fail(function(data) {
            //switchToFtmsProcess();
            alert(data.responseText);
            
        });

        e.preventDefault();
    
    });
}

function updateFtmsFormData(formType){

        let formData = new FormData($("#"+formType)[0]);
        
        let present_id = $( "#ftms_presets" ).val(); 
        event.preventDefault()
        $.ajax({
            
            type : 'POST',
            url : '/ftms/update-parameters/' + formType + '/' + present_id,
            data : formData,
            processData : false,
            contentType : false,
            
        }).done(function(data) {
            
            //TODO: reload data table and process list to avoid reload
            // call to update on load
            
            alert(data.done);
            console.log(formType);
            return false;

        }).fail(function(data) {
            //switchToFtmsProcess();
            //alert(data.responseText);
            alert(data.done);
            
        });


}

function updateAllFtmsFormData(id) {
    
    $.getJSON( "/ftms/parameters/all/" + id , function() {
        console.log( "success" );
        }).done(function(json_result) {
            
            $("#ftmsbasicsettings").html(json_result.basic);
            $("#ftmsadvancedsettings").html(json_result.advanced);
            $("#ftmssettings").html(json_result.ms);
            $("#ftmspeaksettings").html(json_result.mspeak);
            $("#ftmstransietsettings").html(json_result.transient);
            alert(json_result.done);

        }).fail(function(data) {
            alert(data.responseText);

        }).always(function() {
            
            $('.add_atoms').click({div_template: '#usedAtoms-_',
            subfield: '.usedAtoms-subfield',
            div_target: '#usedAtoms-subfield-container',
            class_target: 'usedAtoms-subfield',
            class_template: 'usedAtoms-is-hidden',
            }, addForm)

            $('.add_kendrick').click({div_template: '#kendrickAtoms-_',
                            subfield: '.kendrick-subfield',
                            div_target: '#kendrick-subfield-container',
                            class_target: 'kendrick-subfield',
                            class_template: 'kendrick-is-hidden',
                        }, addForm)

            $('.remove_kendrick').click({subfield: '.kendrick-subfield'}, removeForm);

            $('.remove_atoms').click({subfield: '.usedAtoms-subfield'}, removeForm);
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

function switchToFtmsPreset() {
    RemoveActiveFtmsSettings();
    hideAllFtmsSettings();
    $("#ftmspreset-tab").addClass("is-active");
    $("#ftmspreset-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_ftms", "#ftmspreset-tab");
    Cookies.set("tabs_selected_ftms_content", "#ftmspreset-tab-content");
    
}

function switchToFtmsBasic() {
    RemoveActiveFtmsSettings();
    hideAllFtmsSettings();
    $("#ftmsbasic-tab").addClass("is-active");
    $("#ftmsbasic-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_ftms", "#ftmsbasic-tab");
    Cookies.set("tabs_selected_ftms_content", "#ftmsbasic-tab-content");
    
}

function switchToFtmsInputData() {
    RemoveActiveFtmsSettings();
    hideAllFtmsSettings();
    $("#ftmsinputdata-tab").addClass("is-active");
    $("#ftmsinputdata-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_ftms", "#ftmsinputdata-tab");
    Cookies.set("tabs_selected_ftms_content", "#ftmsinputdata-tab-content");
    
}

function switchToFtmsMolSearch() {
    RemoveActiveFtmsSettings();
    hideAllFtmsSettings();
    $("#ftmsmolsearch-tab").addClass("is-active");
    $("#ftmsmolsearch-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_ftms", "#ftmsmolsearch-tab");
    Cookies.set("tabs_selected_ftms_content", "#ftmsmolsearch-tab-content");
}

function switchToFtmsmSettings() {
    RemoveActiveFtmsSettings();
    hideAllFtmsSettings();
    $("#ftmsmssettings-tab").addClass("is-active");
    $("#ftmsmssettings-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_ftms", "#ftmsmssettings-tab");
    Cookies.set("tabs_selected_ftms_content", "#ftmsmssettings-tab-content");
}

function switchToFtmsMsPeak() {
    RemoveActiveFtmsSettings();
    hideAllFtmsSettings();
    $("#ftmsmspeak-tab").addClass("is-active");
    $("#ftmsmspeak-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_ftms", "#ftmsmspeak-tab");
    Cookies.set("tabs_selected_ftms_content", "#ftmsmspeak-tab-content");
}
function switchToTransient() {
    RemoveActiveFtmsSettings();
    hideAllFtmsSettings();
    $("#transient-tab").addClass("is-active");
    $("#transient-tab-content").removeClass("is-hidden");
    Cookies.set("tabs_selected_ftms", "#transient-tab");
    Cookies.set("tabs_selected_ftms_content", "#transient-tab-content");
}

function RemoveActiveFtmsSettings() {
    $(".ftms-param_nav li a").each(function() {
    $(this).removeClass("is-active");
    });
}

function hideAllFtmsSettings(){
    $("#ftmspreset-tab-content").addClass("is-hidden");
    $("#ftmsbasic-tab-content").addClass("is-hidden");
    $("#ftmsinputdata-tab-content").addClass("is-hidden");
    $("#ftmsmolsearch-tab-content").addClass("is-hidden");
    $("#ftmsmssettings-tab-content").addClass("is-hidden");
    $("#ftmsmspeak-tab-content").addClass("is-hidden");
    $("#transient-tab-content").addClass("is-hidden");

}