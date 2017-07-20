$(document).ready(function(){
    $('.dataTables-example').DataTable({
        pageLength: 25,
//        Changed for disable sorting on month column
        order: [],
        //
        responsive: true,
        dom: '<"html5buttons"B>lTfgitp',
        buttons: [
            { extend: 'copy'},
            {extend: 'csv'},
            {extend: 'excel'},
            {extend: 'pdf'},

            {extend: 'print',
             customize: function (win){
                    $(win.document.body).addClass('white-bg');
                    $(win.document.body).css('font-size', '10px');

                    $(win.document.body).find('table')
                            .addClass('compact')
                            .css('font-size', 'inherit')
                          /*  .prepend(
                           '<img src="http://www.malabarmilma.com/images/milma_logo.jpg" style="position:absolute; top:0; left:0;" />'
                       )*/
                            ;

            }
            }
        ]

    });

});
