app.factory('Burial', function($resource, $routeParams){
	return $resource('/api/burial/:burialID', {burialID:'@id'},{
		get: {
			method: 'GET',
			params: {
				format: 'json',
			},
			isArray: false
		},
		query: {
			method: 'GET',
			params: {
				format: 'json',
			},
			isArray: true
		},
		update: {
			method: 'PUT',
            params: {
                format: 'json',
            }
		}
		
	});
});
