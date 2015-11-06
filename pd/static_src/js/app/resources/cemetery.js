app.factory('Cemetery', function($resource){
    return $resource('/api/cemetery/:cemeteryID/:action', {cemeteryID:'@id'},{
        get: {
            method: 'GET',
            params: {
                format: 'json'
            }
        },
        getForm: {
            method: 'GET',
            params: {
                action: 'getform',
            },
            isArray: false
        },
        canAddCemetery: {
            method: 'GET',
            params: {
                action: 'canaddcemetery',
            },
            isArray: false
        },
        isEditable: {
            method: 'GET',
            params: {
                action: 'iseditable',
            },
            isArray: false
        },
        save: {
            method:'POST',
            params:{
                format:'json'
            }
        },
        update:{
            method:'PUT',
            params:{
                format:'json'
            }
        }
    })
});

