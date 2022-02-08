var JQgcmsDataTable;

$(function(){
    
    gcms_datalist_size();
    JQgcmsDataTable = initGcmsDataTable();
    //removeGcmsData();
    //openGCMSDataResultsModal();
});

function openGCMSDataResultsModal(href) {
        
        //e.preventDefault();
        startModalSpin();
        $.get( href, function(){
            
        }).done(function(result) {
            
            //e.preventDefault();
            $(".plot").html(result);
            
            stopModalSpin()
            
            let modal = document.querySelector('#gcmsplot');  // assuming you have only 1
            let html = document.querySelector('html');
            modal.classList.add('is-active');
            html.classList.add('is-clipped');
    
            modal.querySelector('.modal-background').addEventListener('click', function(e) {
              //e.preventDefault();
              modal.classList.remove('is-active');
              html.classList.remove('is-clipped');
            })
            modal.querySelector('.modal-close').addEventListener('click', function(e) {
                //e.preventDefault();
                modal.classList.remove('is-active');
                html.classList.remove('is-clipped');
                
              })  
              
        }).fail(function(result) {
            
            //e.preventDefault();
            stopModalSpin();

            alert('Ops something went wrong, please try again!');
    
            });
}

function initGcmsDataTable(){
    
    gcmsDataTable = $('#gcmsDataTable').DataTable({searching: true, paging: true, info: true,
        "lengthMenu": [[5, 10, 25, 50, -1], [5, 10, 25, 50, "All"]],
        rowId: 'id',
        "order": [[ 3, 'desc' ]]
    
    });

    $('#gcmsDataTable tbody').on( 'click', 'tr', function () {
        $(this).toggleClass('is-selected');
        
        let all_selected = gcmsDataTable.rows('.is-selected').ids()
        
        if (all_selected.length > 0){
            $('#gcmsDataTableNav').removeClass('is-hidden');
        }
        else{
            $('#gcmsDataTableNav').addClass('is-hidden');
        }
        
    } );

    return gcmsDataTable
}
function removeSelectedGcmsData(){
    
    function remove_data(href){
        $.post(href)
            .done(function() {
                
                updateGcmsDataList();
                
            }).fail(function() {
                
                alert('Ops something went wrong, please try again!');

            });
            
    };
    
    function remove_all(linkArray) {
    for (var i = 0; i < linkArray.length; i++) { 
        
        setTimeout(function (path) { remove_data(path) }, 200 + i * 200, linkArray[i]);
        }        
    };
    
    if (window.confirm("You are about to delete this result from the database, are you sure?")) {
        let all_data_selected = JQgcmsDataTable.rows('.is-selected').ids()
        
        let download_urls = []
        
        for (i = 0; i < all_data_selected.length; i++) {
            
            download_urls.push("/gcms/remove_data/" + all_data_selected[i])
        }
        remove_all(download_urls)

    }
}

function downloadSelectedGcmsData(){
    
    function download_all(linkArray) {
    for (var i = 0; i < linkArray.length; i++) { 
        
        setTimeout(function download_all(path) { location.href = path; }, 200 + i * 200, linkArray[i]);
        }        
    };
    
    let all_data_selected = JQgcmsDataTable.rows('.is-selected').ids()
    
    let download_urls = []
    
    for (i = 0; i < all_data_selected.length; i++) {
        
        download_urls.push("/gcms/download_data/" + all_data_selected[i])
    }
    download_all(download_urls)
}

function removeGcmsData(href) {
        
        if (window.confirm("You are about to delete this file from the database, are you sure?")) {
            
            $.post(href)
            .done(function() {
                
                updateGcmsDataList();
                
            }).fail(function() {
                
                alert('Ops something went wrong, please try again!');

            });
        }
}

function gcms_datalist_size(){
    
    let length_gcms_data = $("#gcms_data_list option").length
    
    if (length_gcms_data < 15) {
        $("#gcms_data_list").attr("size",length_gcms_data);
    } else{
        $("#gcms_data_list").attr("size","15");  
    } 

}

function updateGcmsDataList() {
    
    let process_files = $('#gcms_data_list')
    let ref_files = $('#gcms_selected_reference_file')
    let gcms_data_table = $('#gcmsDataTable')
    let tbody = gcms_data_table.children('tbody');

    let sizeList = 0;
    process_files.attr('disabled', 'disabled');
    process_files.empty();
    
    ref_files.attr('disabled', 'disabled');
    ref_files.empty();

    gcms_data_table.attr('disabled', 'disabled');
    //tbody.empty();
    JQgcmsDataTable.clear().draw();

    $.getJSON( '/gcms/gcms_all_data', function( json_result ) {
        
    }).done(function(json_result) {
        
        ref_files.append(
            $('<option>', {
                value: 0,
                text: 'None'
            })
        )
        var navbar = `<tr id="gcmsDataTableNav" class="is-hidden" role="row"><td rowspan="1" colspan="1">
        <a title="Delete Selected" class="removeSelectedGcmsData" onclick="removeSelectedGcmsData()">
        
        <span class="icon is-medium">
            <i class="fa fa-minus-circle" aria-hidden="true"></i>
        </span>
        </a>
        <a title="Download Selected" class="downloadSelectedGcmsData" onclick="downloadSelectedGcmsData( )">
        
        <span class="icon is-medium">
            <i class="fa fa-download" aria-hidden="true"></i>
        </span>
        </a>
        </td><td rowspan="1" colspan="1"></td><td rowspan="1" colspan="1"></td><td rowspan="1" colspan="1"></td><td rowspan="1" colspan="1"></td><td rowspan="1" colspan="1"></td></tr>`
        
        JQgcmsDataTable.row.add( $(navbar)).draw();

        json_result.data.forEach(function(item) {
            
            //tbody.append(GcMSDataTableRow(item));
            JQgcmsDataTable.row.add( $(GcMSDataTableRow(item))).draw();
            //alert(item.is_calibration);
            if(item.is_calibration) {
                
               ref_files.append(
                    $('<option>', {
                        value: item.id,
                        text: item.name + item.modifier
                    })
                );
            } 
            else {
                 sizeList = sizeList + 1
                process_files.append(
                    $('<option>', {
                        value: item.id,
                        text: item.name + item.modifier
                    })
                );

                
            };
            
        });

        if(sizeList <= 15) {
            process_files.attr("size",sizeList);
        }
        else{
            process_files.attr("size",15);
        }

        ref_files.removeAttr('disabled');
        process_files.removeAttr('disabled');
        gcms_data_table.removeAttr('disabled');
    
        //TODO: reload data table and process list to avoid reload
        //location.reload();
        
    }).fail(function() {
        stopModalSpin();
        alert('Ops something went wrong, please try again!');
        
    });
        
    
}  

function GcMSDataTableRow(item){
    var table_row = `<tr style="word-wrap:break-word;" id=${item.id}>
                <td >${item.name}${item.modifier}</td>
                <td >(${item.suffix} ) / ${item.filetype}</td>
                <td >${item.pst_time_stamp}</td>
                <td><a title="Download Data" class="download_gcms_data" href="/gcms/download_data/${item.id}">
                    <span class="icon">
                    <i class="fa fa-download" aria-hidden="true"></i>
                    </span>
                    </a>
                </td>
                <td><a title="Delete Data" class="remove_gcms_data" onClick="removeGcmsData('/gcms/remove_data/${item.id}', '${item.id}')" >
                        <span class="icon">
                        <i class="fa fa-minus-circle" aria-hidden="true"></i>
                        </span>
                    </a>
                </td>
                
                <td><a title="Open Data" class="open_gcms_data" id="${item.id}" onClick="openGCMSDataResultsModal('/gcms/load_data_modal/${item.id}')">
                <span class="icon is-small">
                    <i class="fas fa-external-link-alt"></i>
                </span>
                </button>
            </td>
            
            </tr>`;
            return table_row;
}