app.factory('AreaPhoto', function($resource, $routeParams){
	return $resource('/api/area-photo:photoID', {photoID:'@id'},{
		get: {
			method: 'GET',
			params: {
				format: 'json',
			},
			isArray: false
		},
		update: {
			method: 'PUT'
		}
	});
});


