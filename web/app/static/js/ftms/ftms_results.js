var JQftmsResultTable; 

$(function(){
    
    JQftmsResultTable = initFtmsResultTable();
    
    $( "#ftms_merge_variable_gui" ).dialog({
        resizable: false,
        autoOpen: false,
        height: "auto",
        width: 450,
        modal: false,
        buttons: {
          "Combine and Download": function() {
            variable = $("#ftms_merge_variable").val();
            combineSelectedFtmsResults(variable);
            $( this ).dialog( "close" );
          },
          Cancel: function() {
            $( this ).dialog( "close" );
          }
        }
      });

});

function open_ftms_merge_variable_gui(){
    $( "#ftms_merge_variable_gui" ).dialog( "open" );
}
function combineSelectedFtmsResults(variable){
    
    
    let all_data_selected = JQftmsResultTable.rows('.is-selected').ids();
    let combined_data_id = []
    
    for (i = 0; i < all_data_selected.length; i++) {
        
        combined_data_id.push(all_data_selected[i])
    }

    //alert(all_data_selected);
    //url = '/ftms/combine_result/'
    
    //let data = JSON.stringify({"data_ids": combined_data_id});
    location.href =  '/ftms/combine_result/'+  combined_data_id + '/' + variable;

}

function downloadSelectedFtmsResults(){
    
    function download_all(linkArray) {
    for (var i = 0; i < linkArray.length; i++) { 
        
        setTimeout(function download_all(path) { location.href = path; }, 200 + i * 200, linkArray[i]);
        }        
    };
    
    let all_data_selected = JQftmsResultTable.rows('.is-selected').ids()
    
    let download_urls = []
    
    for (i = 0; i < all_data_selected.length; i++) {
        
        download_urls.push("/ftms/download/" + all_data_selected[i])
    }
    download_all(download_urls)
}

function removeSelectedFtmsResults(){
    
    function remove_result(rowId){
        
        //alert(rowId);
        JQftmsResultTable.row("#"+rowId).remove().draw();
        location.href =  "/ftms/remove_result/" +  rowId;
            
    };
    
    function remove_all(linkArray) {
    for (var i = 0; i < linkArray.length; i++) { 
        
        setTimeout(function (args) { remove_result(args) }, 200 + i * 200, linkArray[i]);
        }        
    };
    
    if (window.confirm("You are about to delete this result from the database, are you sure?")) {
        
        let all_data_selected = JQftmsResultTable.rows('.is-selected').ids()
        
        let download_urls = []
        
        for (i = 0; i < all_data_selected.length; i++) {
            
            download_urls.push(all_data_selected[i])
        }
        //alert(download_urls);
        remove_all(download_urls)

    }
}

function removeFtmsResult(href, id) {
    
    if (window.confirm("You are about to delete this result from the database, are you sure?")) {
        
        //var recent_item = $(`.ftmsrecentresult#${this.id}`);
        
        //$(recent_item).remove();
        var table_item = $(`.ftmsresulttable#${id}`);
        
        table_item.remove();

        location.href = href;

        //location.reload();

    }
};

function initFtmsResultTable(){
    
    ftmsResultTable = $('#ftmsResultsTable').DataTable({searching: true, paging: true, info: true,
        "lengthMenu": [[4, 10, 25, 50, -1], [4, 10, 25, 50, "All"]],
        rowId: 'id',
        "order": [[ 2, 'desc' ]]
    
    });

    $('#ftmsResultsTable tbody').on( 'click', 'tr', function () {
        $(this).toggleClass('is-selected');
        
        let all_selected = ftmsResultTable.rows('.is-selected').ids()
        
        if (all_selected.length > 0){
            $('#ftmsResultsTableNav').removeClass('is-hidden');
        }
        else{
            $('#ftmsResultsTableNav').addClass('is-hidden');
        }
        
    } );
    
    return ftmsResultTable
}