app.factory('Area', function($resource, $routeParams){
	return $resource('/api/area/:areaID', {areaID:'@id'},{
        get: {
            method:'GET',
            params:{
                format:'json'
            },
            isArray:false
        },
        list: {
            method:'GET',
            params:{
                format:'json'
            },
            isArray:true,
            cache:false
        },
        create: {
    		method:'GET',
    		params:{
    			format:'json'
    		}, 
    		isArray:true
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
    });
});
