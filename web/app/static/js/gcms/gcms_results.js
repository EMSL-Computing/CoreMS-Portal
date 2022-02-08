var JQgcmsResultTable; 

$(function(){
    
    JQgcmsResultTable = initGcmsResultTable();
    
});
function downloadSelectedGcmsResults(){
    
    function download_all(linkArray) {
    for (var i = 0; i < linkArray.length; i++) { 
        
        setTimeout(function download_all(path) { location.href = path; }, 200 + i * 200, linkArray[i]);
        }        
    };
    
    let all_data_selected = JQgcmsResultTable.rows('.is-selected').ids()
    
    let download_urls = []
    
    for (i = 0; i < all_data_selected.length; i++) {
        
        download_urls.push("/gcms/download/" + all_data_selected[i])
    }
    download_all(download_urls)
}

function removeSelectedGcmsResults(){
    
    function remove_result(rowId){
        
        JQgcmsResultTable.row("#"+rowId).remove().draw();
        location.href =  "/gcms/remove_result/" +  rowId;
            
    };
    
    function remove_all(linkArray) {
    for (var i = 0; i < linkArray.length; i++) { 
        
        setTimeout(function (args) { remove_result(args) }, 200 + i * 200, linkArray[i]);
        }        
    };
    
    if (window.confirm("You are about to delete this result from the database, are you sure?")) {
        
        let all_data_selected = JQgcmsResultTable.rows('.is-selected').ids()
        
        let download_urls = []
        
        for (i = 0; i < all_data_selected.length; i++) {
            
            download_urls.push(all_data_selected[i])
        }
        
        remove_all(download_urls)

    }
}

function removeGcmsResult(href, id) {
    
    if (window.confirm("You are about to delete this result from the database, are you sure?")) {
        
        //var recent_item = $(`.ftmsrecentresult#${this.id}`);
        
        //$(recent_item).remove();
        var table_item = $(`.gcmsresulttable#${id}`);
        
        table_item.remove();

        location.href = href;

        //location.reload();

    }
};

function initGcmsResultTable(){
    
    gcmsResultTable = $('#gcmsResultsTable').DataTable({searching: true, paging: true, info: true,
        "lengthMenu": [[4, 10, 25, 50, -1], [4, 10, 25, 50, "All"]],
        rowId: 'id',
        "order": [[ 2, 'desc' ]]
    
    });

    $('#gcmsResultsTable tbody').on( 'click', 'tr', function () {
        $(this).toggleClass('is-selected');
        
        let all_selected = gcmsResultTable.rows('.is-selected').ids()
        
        if (all_selected.length > 0){
            $('#gcmsResultsTableNav').removeClass('is-hidden');
        }
        else{
            $('#gcmsResultsTableNav').addClass('is-hidden');
        }
        
    } );
    
    return gcmsResultTable
}