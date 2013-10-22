app.factory('Place', function($resource,$routeParams){
	return $resource('/api/place/:placeID', {placeID: '@id'}, {
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
			method: 'PUT',
            params: {
            }
		},
		save: {
			method: 'POST',
            params: {
				format: 'json'
            }
		},
		list_cemetery: {
			method: 'GET',
			params: {
				format: 'json'
			},
			isArray: true
		},

	});
});
