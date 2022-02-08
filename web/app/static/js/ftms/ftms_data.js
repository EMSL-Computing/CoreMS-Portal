var JQftmsDataTable;

$(function(){
    
    ftmsDatalistSize();
    JQftmsDataTable = initFtmsDataTable();
    
    //removeFtmsData();
    //openDataResultsModal();

});

function openDataResultsModal(href) {
        
        startModalSpin();
        
        let preset_id = $('#ftmspresetsubmmit').val();
        let new_href = href + "/"+ preset_id;
        $.get( new_href, function(){
            
        }).done(function(result) {
            
            $(".plot").html(result);
            
            stopModalSpin()
            
            let modal = document.querySelector('#ftmsplot');  // assuming you have only 1
            let html = document.querySelector('html');
            modal.classList.add('is-active');
            html.classList.add('is-clipped');
    
            modal.querySelector('.modal-background').addEventListener('click', function(e) {
              modal.classList.remove('is-active');
              html.classList.remove('is-clipped');
            })
            modal.querySelector('.modal-close').addEventListener('click', function(e) {
                modal.classList.remove('is-active');
                html.classList.remove('is-clipped');
                
              })  
              
        }).fail(function(result) {
            
            stopModalSpin();

            alert('Ops something went wrong, please try again!');
    
            });
}

function removeSelectedFtmsData(){
    
    function remove_data(href){
        $.post(href)
            .done(function() {
                
                updateFtmsDataList();
                
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
        let all_ftms_data_selected = JQftmsDataTable.rows('.is-selected').ids()
        
        let download_urls = []
        
        for (i = 0; i < all_ftms_data_selected.length; i++) {
            
            download_urls.push("/ftms/remove_data/" + all_ftms_data_selected[i])
        }
        remove_all(download_urls)
        

    }
}
function open_raw_data(){

}

function downloadSelectedFtmsData(){
    
    function download_all(linkArray) {
    for (var i = 0; i < linkArray.length; i++) { 
        
        setTimeout(function download_all(path) { location.href = path; }, 200 + i * 200, linkArray[i]);
        }        
    };
    
    let all_ftms_data_selected = JQftmsDataTable.rows('.is-selected').ids()
    
    let download_urls = []
    
    for (i = 0; i < all_ftms_data_selected.length; i++) {
        
        download_urls.push("/ftms/download_data/" + all_ftms_data_selected[i])
    }
    download_all(download_urls)
}

function initFtmsDataTable(){
    
    var ftmsDataTable = $('#ftmsDataTable').DataTable({searching: true, paging: true, info: true,
        "lengthMenu": [[5, 10, 25, 50, -1], [5, 10, 25, 50, "All"]],
        rowId: 'id',
        "order": [[ 3, 'desc' ]]
    });

    $('#ftmsDataTable tbody').on( 'click', 'tr', function () {
        $(this).toggleClass('is-selected');
        
        let all_ftms_data_selected = ftmsDataTable.rows('.is-selected').ids()
        
        if (all_ftms_data_selected.length > 0){
            $('#ftmsDataTableNav').removeClass('is-hidden');
        }
        else{
            $('#ftmsDataTableNav').addClass('is-hidden');
        }
        
    } );
 
    return ftmsDataTable
}


function removeFtmsResult(href, id) {
    
    if (window.confirm("You are about to delete this result from the database, are you sure?")) {
        
        //var recent_item = $(`.ftmsrecentresult#${this.id}`);
        
        //$(recent_item).remove();
        var table_item = $(`.ftmsresulttable#${id}`);
        
        //recent_item.remove()

        table_item.remove();

        location.href = href;

        //location.reload();

    }
};

function removeFtmsData(href) {
    
    //$('.remove_ftms_data').click(function(e) {
        
        if (window.confirm("You are about to delete this file from the database, are you sure?")) {
            //e.preventDefault();
            $.post(href)
            .done(function() {
                
                updateFtmsDataList();
                
            }).fail(function() {
                
                alert('Ops something went wrong, please try again!');

            });
            
        }
    //}); 
}

function ftmsDatalistSize(){
    
    let length_ftms_data = $("#ftms_data_list option").length
    
    if (length_ftms_data < 15) {
        $("#ftms_data_list").attr("size",length_ftms_data);
    } else{
        $("#ftms_data_list").attr("size","15");  
    } 

}

function updateFtmsDataList() {
    
    let process_files = $('#ftms_data_list')
    let ref_files = $('#reference_file')
    let ftms_data_table = $('#ftmsDataTable')
    let tbody = ftms_data_table.children('tbody');

    let sizeList = 0;
    process_files.attr('disabled', 'disabled');
    process_files.empty();
    
    ref_files.attr('disabled', 'disabled');
    ref_files.empty();

    ftms_data_table.attr('disabled', 'disabled');
    //tbody.empty();
    JQftmsDataTable.clear().draw();

    $.getJSON( '/ftms/ftms_all_data', function( json_result ) {
        
    }).done(function(json_result) {
        
        ref_files.append(
            $('<option>', {
                value: 0,
                text: 'None/Do Not Recalibrate'
            })
        )

        var navbar = `<tr id="ftmsDataTableNav" class="is-hidden" role="row"><td rowspan="1" colspan="1">
        <a title="Delete Selected" class="removeSelectedFtmsData" onclick="removeSelectedFtmsData()">
        
        <span class="icon is-medium">
            <i class="fa fa-minus-circle" aria-hidden="true"></i>
        </span>
        </a>
        <a title="Download Selected" class="downloadSelectedFtmsData" onclick="downloadSelectedFtmsData( )">
        
        <span class="icon is-medium">
            <i class="fa fa-download" aria-hidden="true"></i>
        </span>
        </a>
        </td><td rowspan="1" colspan="1"></td><td rowspan="1" colspan="1"></td><td rowspan="1" colspan="1"></td><td rowspan="1" colspan="1"></td><td rowspan="1" colspan="1"></td></tr>`

        //JQftmsDataTable.row.add( $(navbar)).draw();

        //tbody.append(navbar)

        json_result.data.forEach(function(item) {
            
            JQftmsDataTable.row.add( $(FtmsDataTableRow(item))).draw();
            //tbody.append(FtmsDataTableRow(item));

            if(item.filetype != 'reference') {
                
                sizeList = sizeList + 1
                process_files.append(
                    $('<option>', {
                        value: item.id,
                        text: item.name + item.modifier
                    })
                );
            } 
            else {
                ref_files.append(
                    $('<option>', {
                        value: item.id,
                        text: item.name + item.modifier
                    })
                )
            };
            
        })

        if(sizeList <= 15) {
            process_files.attr("size",sizeList);
        }
        else{
            process_files.attr("size",15);
        }

        ref_files.removeAttr('disabled');
        process_files.removeAttr('disabled');
        ftms_data_table.removeAttr('disabled');
    
        
    
            
        //TODO: reload data table and process list to avoid reload
        //location.reload();
        
    }).fail(function() {
        stopModalSpin();
        alert('Ops something went wrong, please try again!');
        
    });
        
    
}  

function FtmsDataTableRow(item){
    var table_row = `<tr style="word-wrap:break-word;" id=${item.id}>
                <td >${item.name}${item.modifier} </td>
                <td >(${item.suffix} ) / ${item.filetype}</td>
                <td >${item.pst_time_stamp}</td>
                <td >${item.id}</td>
                <td><a title="Download Data" class="download_ftms_data" href="/ftms/download_data/${item.id}">
                    <span class="icon">
                    <i class="fa fa-download" aria-hidden="true"></i>
                    </span>
                    </a>
                </td>
                <td><a title="Delete Data" class="remove_ftms_data" onClick="removeFtmsData('/ftms/remove_data/${item.id}', '${item.id}')" >
                        <span class="icon">
                        <i class="fa fa-minus-circle" aria-hidden="true"></i>
                        </span>
                    </a>
                </td>
                <td><a title="Open Data" class="open_ftms_data" id="${item.id}" onClick="openDataResultsModal('/ftms/load_data_modal/${item.id}')" >
                <span class="icon is-small">
                    <i class="fas fa-external-link-alt"></i>
                </span>
                </button>
            </td>
            
            </tr>`;
            return table_row;
} 