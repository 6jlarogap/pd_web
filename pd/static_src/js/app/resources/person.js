app.factory('AlivePerson', function($resource,$routeParams){
	return $resource('/api/alive-person/:personID', {personID: '@id'}, {
		get: {
			method: 'GET',
			params: {
				format: 'json',
			},
			isArray: false
		},
		update: {
			method: 'PUT',
		}
	});
})


.factory('DeadPerson', function($resource,$routeParams){
	return $resource('/api/dead-person/:personID', {personID: '@id'}, {
		get: {
			method: 'GET',
			params: {
				format: 'json',
			},
			isArray: false
		},
		update: {
			method: 'PUT',
		}
	});
});
