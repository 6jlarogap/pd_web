app.factory('GravePhoto', function($resource){
	return $resource('/api/grave-photo:photoID', {photoID:'@id'},{
		get: {
			method: 'GET',
			params: {
				format: 'json'
			},
			isArray: false
		},
		query: {
			method: 'GET',
			params: {
				format: 'json'
			},
			isArray: true
		},
		update: {
			method: 'PUT'
		}
	});
});