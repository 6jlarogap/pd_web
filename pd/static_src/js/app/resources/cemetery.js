app.factory('Cemetery', function($resource){
	return $resource('/api/cemetery/:cemeteryID', {cemeteryID:'@id'},{
	    get: {
	        method: 'GET',
	        params: {
	            format: 'json'
	        }
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

