app.factory('AreaPurpose', function($resource){
	return $resource('/api/area-purpose/:iID', {iID:'@id'},{
            get: {
            		method:'GET', 
            		params:{  format:'json' }, 
            		isArray:true
            	}
   	});
});