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
        getAdmin: {
            method: 'GET',
            params: {
                action: 'getadmin',
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

